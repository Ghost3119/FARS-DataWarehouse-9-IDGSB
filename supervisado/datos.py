"""Preparación histórica de las 50 ediciones nacionales de FARS."""

import json
from pathlib import Path
from zipfile import ZipFile

import pandas as pd

from scripts.download_raw import BASE, download_asset

DIRECTORIO = Path(__file__).resolve().parent
ANIOS = tuple(range(1975, 2025))
PARTICIONES = dict.fromkeys(range(1975, 2023), "entrenamiento")
PARTICIONES.update({2023: "validacion", 2024: "prueba"})
PARTICIONES_REG = {**PARTICIONES, 1975: "historia"}
ESTADOS = (1, 2, 4, 5, 6, 8, 9, 10, 11, 12, 13, 15, 16, 17, 18, 19, 20, 21, 22, 23,
           24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42,
           44, 45, 46, 47, 48, 49, 50, 51, 53, 54, 55, 56)
CATEGORIAS_CLAS = ["STATE", "MONTH", "DAY_WEEK", "HOUR", "LUZ", "TIPO_COLISION"]
NUMERICAS_CLAS = ["VE_FORMS"]
CATEGORIAS_REG = ["STATE", "MONTH"]
NUMERICAS_REG = ["MUERTES_MISMO_MES_PREV", "MEDIA_MENSUAL_PREV"]
CLAVE_CASO = ["YEAR", "STATE", "ST_CASE"]
CLAVE_MES = ["YEAR", "STATE", "MONTH"]
CAMPOS = ["YEAR", "ST_CASE", "STATE", "MONTH", "DAY_WEEK", "HOUR", "LGT_COND",
          "MAN_COLL", "VE_FORMS", "FATALS"]
ARCHIVO_CLAS = "clasificacion.csv.gz"
ARCHIVO_REG = "regresion.csv"

# Equivalencias C20 y C25 del manual analítico FARS 1975-2024 (DOT HS 813 794).
COLISION_ANTIGUA = {0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 5, 7: 5, 9: 99}
COLISION_RECIENTE = {0: 0, 1: 1, 2: 2, 3: 4, 4: 4, 5: 4, 6: 4, 7: 5, 8: 5,
                     9: 6, 10: 3, 11: 7, 98: 99, 99: 99}

def fuentes():
    ediciones = json.loads((DIRECTORIO / "originales.json").read_text(encoding="utf-8"))
    if tuple(e["year"] for e in ediciones) != ANIOS:
        raise ValueError("El manifiesto debe cubrir exactamente las 50 ediciones nacionales")
    return ediciones


def leer_accidentes(zip_path, origen):
    anio = origen["year"]
    with ZipFile(zip_path) as archivo, archivo.open(origen["member"]) as flujo:
        # Algunas ediciones conservan una marca UTF-8 antes de la cabecera.
        if flujo.read(3) != b"\xef\xbb\xbf":
            flujo.seek(0)
        casos = pd.read_csv(
            flujo, encoding="latin1", dtype="int64",
            usecols=lambda campo: campo.strip().upper() in CAMPOS,
        )
    casos.columns = casos.columns.str.strip().str.upper()
    anios_fuente = [anio, anio % 100] + ([99] if anio in (1975, 1977) else [])
    colision = COLISION_ANTIGUA if anio < 2002 else COLISION_RECIENTE
    luz = {1: 1, 2: 2, 3: 2, 4: 3, 5: 3, 6: 3 if anio < 1980 else 2,
           7: 4, 8: 99, 9: 99}
    validos = (
        casos["YEAR"].isin(anios_fuente)
        & casos["ST_CASE"].gt(0)
        & casos["MONTH"].isin([*range(1, 13), 99])
        & casos["FATALS"].ge(0)
        & casos["VE_FORMS"].ge(0 if anio < 1982 else 1)
        & casos["DAY_WEEK"].isin([*range(1, 8), 9])
        & casos["HOUR"].isin([*range(25), 99])
        & casos["LGT_COND"].isin(luz)
        & casos["MAN_COLL"].isin(colision)
    )
    if not validos.all() or set(casos["STATE"]) != set(ESTADOS):
        raise ValueError(f"Códigos fuera del universo definido en FARS {anio}")
    if casos.duplicated(CLAVE_CASO).any():
        raise ValueError(f"Clave de siniestro duplicada en FARS {anio}")
    if (len(casos) != origen["crashes"]
            or casos["FATALS"].eq(0).sum() != origen["fatals_zero"]
            or casos["FATALS"].sum() != origen["fatalities"]):
        raise ValueError(f"Los conteos de FARS {anio} no coinciden con el manifiesto")
    casos["YEAR"] = anio
    casos["HOUR"] = casos["HOUR"].replace(24, 0)
    casos["LUZ"] = casos["LGT_COND"].map(luz)
    casos["TIPO_COLISION"] = casos["MAN_COLL"].map(colision)
    return casos.loc[
        casos["FATALS"].ge(1),
        ["YEAR", "ST_CASE", *CATEGORIAS_CLAS, *NUMERICAS_CLAS, "FATALS"],
    ]


def construir_regresion(casos):
    combinaciones = pd.MultiIndex.from_product(
        [ANIOS, ESTADOS, range(1, 13)], names=CLAVE_MES
    )
    panel = (
        casos.loc[casos["MONTH"].between(1, 12)].groupby(CLAVE_MES)["FATALS"].sum()
        .reindex(combinaciones, fill_value=0)
        .rename("MUERTES")
        .reset_index()
    )
    historia = panel.rename(columns={"MUERTES": "MUERTES_MISMO_MES_PREV"})
    historia["MEDIA_MENSUAL_PREV"] = historia.groupby(["YEAR", "STATE"])[
        "MUERTES_MISMO_MES_PREV"
    ].transform("mean")
    historia["YEAR"] = historia["YEAR"] + 1
    regresion = panel.merge(historia, on=CLAVE_MES, how="left", validate="one_to_one")
    regresion["MUERTES_MISMO_MES_PREV"] = regresion["MUERTES_MISMO_MES_PREV"].astype("Int64")
    regresion["particion"] = regresion["YEAR"].map(PARTICIONES_REG)
    return regresion


def reconstruir(originales, salida):
    ediciones = fuentes()
    tablas = []
    for origen in ediciones:
        anio = origen["year"]
        archivo = download_asset(f"{BASE}fars-raw-{anio}/", origen, originales)
        tablas.append(leer_accidentes(archivo, origen))
    clasificacion = pd.concat(tablas, ignore_index=True)
    clasificacion["MULTIPLES_MUERTES"] = clasificacion["FATALS"].ge(2).astype(int)
    clasificacion["particion"] = clasificacion["YEAR"].map(PARTICIONES)
    clasificacion = clasificacion.sort_values(CLAVE_CASO, ignore_index=True)
    regresion = construir_regresion(clasificacion)
    validar_limpios(clasificacion, regresion, ediciones)
    salida.mkdir(parents=True, exist_ok=True)
    clasificacion.to_csv(
        salida / ARCHIVO_CLAS, index=False, lineterminator="\n",
        compression={"method": "gzip", "mtime": 0},
    )
    regresion.to_csv(salida / ARCHIVO_REG, index=False, lineterminator="\n")
    return clasificacion, regresion


def validar_limpios(clasificacion, regresion, ediciones):
    for datos, clave, particiones in [
        (clasificacion, CLAVE_CASO, PARTICIONES), (regresion, CLAVE_MES, PARTICIONES_REG),
    ]:
        if datos.duplicated(clave).any():
            raise ValueError("Hay claves duplicadas en los conjuntos limpios")
        if not datos["particion"].eq(datos["YEAR"].map(particiones)).all():
            raise ValueError("La partición no coincide con el año de los registros")
    historia = regresion["YEAR"].eq(ANIOS[0])
    if (clasificacion.isna().any().any()
            or regresion.drop(columns=NUMERICAS_REG).isna().any().any()
            or regresion.loc[~historia, NUMERICAS_REG].isna().any().any()
            or regresion.loc[historia, NUMERICAS_REG].notna().any().any()):
        raise ValueError("Solo los rezagos de 1975 pueden estar vacíos")
    if not clasificacion["MULTIPLES_MUERTES"].eq(clasificacion["FATALS"].ge(2)).all():
        raise ValueError("La etiqueta binaria no coincide con FATALS")

    muestras = {e["year"]: e["crashes"] - e["fatals_zero"] for e in ediciones}
    if clasificacion.groupby("YEAR").size().to_dict() != muestras:
        raise ValueError("El total de siniestros por año no coincide con el inventario")
    esperado = construir_regresion(clasificacion)
    if not regresion.sort_values(CLAVE_MES, ignore_index=True).equals(esperado):
        raise ValueError("El panel mensual y sus rezagos no coinciden con la suma de FATALS")


def cargar_limpios(directorio):
    clasificacion = pd.read_csv(directorio / ARCHIVO_CLAS)
    regresion = pd.read_csv(
        directorio / ARCHIVO_REG, dtype={"MUERTES_MISMO_MES_PREV": "Int64"},
        float_precision="round_trip",
    )
    validar_limpios(clasificacion, regresion, fuentes())
    return clasificacion, regresion
