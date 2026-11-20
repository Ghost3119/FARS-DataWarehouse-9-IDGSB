"""Entrenamiento, selección temporal y evaluación de los modelos."""

from time import perf_counter

import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (
    accuracy_score, average_precision_score, confusion_matrix, f1_score,
    mean_absolute_error, precision_recall_curve, precision_score, r2_score,
    recall_score, root_mean_squared_error,
)
from sklearn.model_selection import ParameterGrid
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .datos import CATEGORIAS_CLAS, CATEGORIAS_REG, NUMERICAS_CLAS, NUMERICAS_REG

SEMILLA = 42
RECALL_MINIMO = 0.50
LOGISTICA = "Regresión logística"
RIDGE = "Ridge"
BOSQUE = "Bosque aleatorio"
MAYORIA = "Clase mayoritaria"
ESTACIONAL = "Mismo mes del año previo"


def separar(tabla, categoricas, numericas, objetivo):
    columnas = categoricas + numericas
    conjuntos = []
    for nombre in ("entrenamiento", "validacion", "prueba"):
        mascara = tabla["particion"].eq(nombre)
        conjuntos.append((tabla.loc[mascara, columnas], tabla.loc[mascara, objetivo]))
    (x_train, y_train), (x_val, y_val), (x_test, y_test) = conjuntos
    preproceso = ColumnTransformer([
        ("categoricas", OneHotEncoder(handle_unknown="ignore"), categoricas),
        ("numericas", StandardScaler(), numericas),
    ])
    return (
        (preproceso.fit_transform(x_train), y_train),
        (preproceso.transform(x_val), y_val),
        (preproceso.transform(x_test), y_test),
    )


def ajustar(modelo, cuadricula, entrenamiento, puntuar, maximizar):
    """Evalúa en 2023 y conserva el mejor ajuste de cada familia."""
    candidatos = []
    elegido = None
    mejor = -np.inf
    for parametros in ParameterGrid(cuadricula):
        estimador = modelo(**parametros)
        inicio = perf_counter()
        estimador.fit(*entrenamiento)
        valor = float(puntuar(estimador))
        candidato = {
            "parametros": parametros,
            "validacion": valor,
            "segundos_ajuste": round(perf_counter() - inicio, 3),
        }
        candidatos.append(candidato)
        prioridad = valor if maximizar else -valor
        if prioridad > mejor:
            mejor = prioridad
            elegido = (estimador, candidato)
    estimador, candidato = elegido
    return estimador, candidato, candidatos


def umbral_validacion(y, scores):
    precision, recall, umbrales = precision_recall_curve(y, scores)
    opciones = np.flatnonzero(recall[:-1] >= RECALL_MINIMO)
    # Si la precisión empata se prefiere el menor umbral, que conserva cobertura.
    indice = opciones[np.argmax(precision[opciones])]
    return {
        "umbral": float(umbrales[indice]),
        "precision": float(precision[indice]),
        "recall": float(recall[indice]),
    }


def metricas_clasificacion(y, scores, umbral):
    pred = scores >= umbral
    return {
        "accuracy": float(accuracy_score(y, pred)),
        "precision": float(precision_score(y, pred)) if pred.any() else None,
        "recall": float(recall_score(y, pred)),
        "f1": float(f1_score(y, pred)),
        "ap": float(average_precision_score(y, scores)),
        "matriz": confusion_matrix(y, pred, labels=[0, 1]).tolist(),
    }


def evaluar_clasificacion(tabla, hilos):
    cat, num = CATEGORIAS_CLAS, NUMERICAS_CLAS
    entrenamiento, (x_val, y_val), (x_test, y_test) = separar(
        tabla, cat, num, "MULTIPLES_MUERTES"
    )
    familias = [
        (LOGISTICA, lambda **p: LogisticRegression(solver="lbfgs", max_iter=400, **p),
         {"C": [1, 0.1, 10]}),
        (BOSQUE, lambda **p: RandomForestClassifier(
            n_estimators=80, random_state=SEMILLA, n_jobs=hilos, **p
         ), {"max_depth": [8, 14], "min_samples_leaf": [40, 10]}),
    ]
    finalistas = {}
    for nombre, modelo, grid in familias:
        modelo, mejor, candidatos = ajustar(
            modelo, grid, entrenamiento,
            lambda m: average_precision_score(y_val, m.predict_proba(x_val)[:, 1]),
            maximizar=True,
        )
        corte = umbral_validacion(y_val, modelo.predict_proba(x_val)[:, 1])
        finalistas[nombre] = (modelo, mejor, corte, candidatos)

    elegido = max(finalistas, key=lambda nombre: finalistas[nombre][1]["validacion"])
    informe = {
        MAYORIA: {
            "test": metricas_clasificacion(y_test, np.zeros(len(y_test)), 0.5),
            "ap_referencia_validacion": float(y_val.mean()),
        },
    }
    curvas = {}
    for nombre, (modelo, mejor, corte, candidatos) in finalistas.items():
        scores = modelo.predict_proba(x_test)[:, 1]
        informe[nombre] = {
            "candidatos": candidatos,
            "seleccion": mejor,
            "corte_validacion": corte,
            "test": metricas_clasificacion(y_test, scores, corte["umbral"]),
            "test_umbral_0_5": metricas_clasificacion(y_test, scores, 0.5),
        }
        curvas[nombre] = precision_recall_curve(y_test, scores)[:2]
    return {"elegido_en_2023": elegido, "modelos": informe}, curvas


def metricas_regresion(y, pred):
    return {
        "mae": float(mean_absolute_error(y, pred)),
        "rmse": float(root_mean_squared_error(y, pred)),
        "r2": float(r2_score(y, pred)),
    }


def evaluar_regresion(tabla, hilos):
    cat, num = CATEGORIAS_REG, NUMERICAS_REG
    entrenamiento, (x_val, y_val), (x_test, y_test) = separar(tabla, cat, num, "MUERTES")
    familias = [
        (RIDGE, Ridge, {"alpha": [1, 0.01, 0.1, 10, 100]}),
        (BOSQUE, lambda **p: RandomForestRegressor(
            n_estimators=150, random_state=SEMILLA, n_jobs=hilos, **p
        ), {"max_depth": [12, 6, None], "min_samples_leaf": [2, 6]}),
    ]
    finalistas = {}
    for nombre, modelo, grid in familias:
        modelo, mejor, candidatos = ajustar(
            modelo, grid, entrenamiento,
            lambda m: mean_absolute_error(y_val, np.maximum(m.predict(x_val), 0)),
            maximizar=False,
        )
        finalistas[nombre] = (modelo, mejor, candidatos)

    previo_val = tabla.loc[tabla["particion"].eq("validacion"), "MUERTES_MISMO_MES_PREV"]
    previo_test = tabla.loc[tabla["particion"].eq("prueba"), "MUERTES_MISMO_MES_PREV"]
    informe = {
        ESTACIONAL: {
            "seleccion": {
                "validacion": float(mean_absolute_error(y_val, previo_val)),
            },
            "test": metricas_regresion(y_test, previo_test),
        },
    }
    for nombre, (modelo, mejor, candidatos) in finalistas.items():
        pred = np.maximum(modelo.predict(x_test), 0)
        informe[nombre] = {
            "candidatos": candidatos,
            "seleccion": mejor,
            "test": metricas_regresion(y_test, pred),
        }
    elegido = min(informe, key=lambda nombre: informe[nombre]["seleccion"]["validacion"])
    return {"elegido_en_2023": elegido, "modelos": informe}
