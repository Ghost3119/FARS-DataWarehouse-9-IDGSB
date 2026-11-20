"""Ajusta y compara configuraciones iniciales y optimizadas de K-means y PCA."""

import numpy as np
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import (
    adjusted_rand_score, calinski_harabasz_score, davies_bouldin_score, silhouette_score,
)
from sklearn.preprocessing import StandardScaler

from .datos import CLAVE, INDICADORES

SEMILLA = 42
REINICIOS = 20
K_INICIAL = 3
COMPONENTES_INICIALES = 2
META_VARIANZA = 0.80


def ajustar_kmeans(x, k):
    return KMeans(n_clusters=k, n_init=REINICIOS, random_state=SEMILLA).fit(x)


def metricas_grupos(x, grupos):
    return {
        "silueta": float(silhouette_score(x, grupos)),
        "davies_bouldin": float(davies_bouldin_score(x, grupos)),
        "calinski_harabasz": float(calinski_harabasz_score(x, grupos)),
    }


def estabilidad(ajuste, validacion, k, referencia):
    columnas = list(INDICADORES)
    rng = np.random.default_rng(SEMILLA)
    estados = ajuste["STATE"].unique()
    valores = []
    for _ in range(12):
        muestra = rng.choice(estados, 41, replace=False)
        x = ajuste.loc[ajuste["STATE"].isin(muestra), columnas]
        escala = StandardScaler().fit(x)
        refit = ajustar_kmeans(escala.transform(x), k)
        grupos = refit.predict(escala.transform(validacion[columnas]))
        valores.append(adjusted_rand_score(referencia, grupos))
    return {
        "repeticiones": len(valores),
        "estados": 41,
        "mediana_ari": float(np.median(valores)),
        "min_ari": min(valores),
        "max_ari": max(valores),
    }


def evaluar_cluster(modelo, base, x_prueba, escala, pca):
    grupos = modelo.predict(x_prueba)
    centros = escala.inverse_transform(modelo.cluster_centers_)
    orden = np.argsort(centros[:, 0])
    renumerar = np.empty(modelo.n_clusters, dtype=int)
    renumerar[orden] = np.arange(1, modelo.n_clusters + 1)
    centros_pca = pca.transform(modelo.cluster_centers_)
    perfiles = [{
        "grupo": int(renumerar[i]),
        "centroide": dict(zip(INDICADORES, centros[i].tolist())),
        "perfiles_ajuste": int(np.sum(modelo.labels_ == i)),
        "perfiles_prueba": int(np.sum(grupos == i)),
        "centroide_pca": centros_pca[i, :2].tolist(),
    } for i in orden]
    detalle = {**base, "prueba": metricas_grupos(x_prueba, grupos), "grupos": perfiles}
    return detalle, renumerar[grupos]


def rmse_reconstruccion(pca, x, proyeccion, d):
    truncada = proyeccion.copy()
    truncada[:, d:] = 0
    return float(np.sqrt(np.mean((x - pca.inverse_transform(truncada)) ** 2)))


def analizar(perfiles):
    ajuste, validacion, prueba = [
        perfiles.loc[perfiles["particion"].eq(nombre)]
        for nombre in ("ajuste", "validacion", "prueba")
    ]
    campos = list(INDICADORES)
    escala = StandardScaler().fit(ajuste[campos])
    x_a, x_v, x_p = [escala.transform(p[campos]) for p in (ajuste, validacion, prueba)]

    candidatos = {}
    for k in range(2, 7):
        modelo = ajustar_kmeans(x_a, k)
        candidatos[k] = (modelo, {
            "k": k,
            "inercia_ajuste": float(modelo.inertia_),
            "validacion": metricas_grupos(x_v, modelo.predict(x_v)),
        })
    k_mejor = max(candidatos, key=lambda k: candidatos[k][1]["validacion"]["silueta"])

    pca = PCA(svd_solver="full").fit(x_a)
    pv, pp = pca.transform(x_v), pca.transform(x_p)
    acumulada = np.cumsum(pca.explained_variance_ratio_)
    d_mejor = int(np.searchsorted(acumulada, META_VARIANZA)) + 1
    opciones = [{
        "componentes": d,
        "varianza_ajuste": float(acumulada[d - 1]),
        "rmse_validacion": rmse_reconstruccion(pca, x_v, pv, d),
    } for d in range(1, len(campos) + 1)]

    informe = {
        "muestras": {nombre: len(tabla) for nombre, tabla in
                     [("ajuste", ajuste), ("validacion", validacion), ("prueba", prueba)]},
        "kmeans": {"candidatos": [fila for _, fila in candidatos.values()]},
        "pca": {
            "meta_varianza": META_VARIANZA,
            "candidatos": opciones,
            "varianza_por_componente": pca.explained_variance_ratio_.tolist(),
            "coeficientes_cp1_cp2": dict(zip(campos, pca.components_[:2].T.tolist())),
        },
    }
    asignaciones = prueba[CLAVE].assign(cp1=pp[:, 0], cp2=pp[:, 1])
    for nombre, k, d in [("inicial", K_INICIAL, COMPONENTES_INICIALES),
                         ("optimizado", k_mejor, d_mejor)]:
        modelo, fila = candidatos[k]
        info, grupos = evaluar_cluster(modelo, fila, x_p, escala, pca)
        informe["kmeans"][nombre] = info
        asignaciones[f"grupo_{nombre}"] = grupos
        informe["pca"][nombre] = {
            **opciones[d - 1], "rmse_prueba": rmse_reconstruccion(pca, x_p, pp, d),
        }
    informe["kmeans"]["estabilidad"] = estabilidad(
        ajuste, validacion, k_mejor, candidatos[k_mejor][0].predict(x_v)
    )
    return informe, asignaciones
