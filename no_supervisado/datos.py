"""Construye los perfiles anuales a partir de los FARS nacionales homologados."""

from pathlib import Path

import pandas as pd

from supervisado.datos import ANIOS, ESTADOS

DIRECTORIO = Path(__file__).resolve().parent
FUENTE = DIRECTORIO.parent / "supervisado" / "datos" / "clasificacion.csv.gz"
CLAVE = ["YEAR", "STATE"]
INDICADORES = {
    "oscuridad": "Oscuridad",
    "fin_semana": "Fin de semana",
    "madrugada": "Madrugada",
    "frontal": "Choque frontal",
    "angular": "Choque angular",
    "roce_lateral": "Roce lateral",
}


def construir_perfiles(fuente):
    campos = [*CLAVE, "LUZ", "DAY_WEEK", "HOUR", "TIPO_COLISION"]
    casos = pd.read_csv(fuente, usecols=campos, dtype="int64")
    luz_valida = casos["LUZ"].isin([1, 2, 3, 4])
    dia_valido = casos["DAY_WEEK"].between(1, 7)
    hora_valida = casos["HOUR"].between(0, 23)
    colision_valida = casos["TIPO_COLISION"].between(0, 7)
    observaciones = casos[CLAVE].assign(
        oscuridad=casos["LUZ"].eq(2).astype(float).where(luz_valida),
        fin_semana=casos["DAY_WEEK"].isin([1, 7]).astype(float).where(dia_valido),
        madrugada=casos["HOUR"].between(0, 5).astype(float).where(hora_valida),
        frontal=casos["TIPO_COLISION"].eq(2).astype(float).where(colision_valida),
        angular=casos["TIPO_COLISION"].eq(4).astype(float).where(colision_valida),
        roce_lateral=casos["TIPO_COLISION"].eq(5).astype(float).where(colision_valida),
    )
    estado_anio = observaciones.groupby(CLAVE, sort=True)
    perfiles = estado_anio[list(INDICADORES)].mean()
    esperado = pd.MultiIndex.from_product([ANIOS, ESTADOS], names=CLAVE)
    if not perfiles.index.equals(esperado) or perfiles.isna().any().any():
        raise ValueError("Se requiere un perfil completo por estado y año de 1975 a 2024")
    perfiles["n_casos"] = estado_anio.size()
    denominadores = {
        "oscuridad": "n_luz", "fin_semana": "n_dia",
        "madrugada": "n_hora", "frontal": "n_colision",
    }
    perfiles = perfiles.join(estado_anio[list(denominadores)].count().rename(columns=denominadores))
    perfiles = perfiles.reset_index()
    perfiles["particion"] = "ajuste"
    perfiles.loc[perfiles["YEAR"].between(2015, 2019), "particion"] = "validacion"
    perfiles.loc[perfiles["YEAR"].ge(2020), "particion"] = "prueba"
    return perfiles
