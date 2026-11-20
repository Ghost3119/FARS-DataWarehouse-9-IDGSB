"""Preparación de los conjuntos nacionales de FARS 2020-2024."""

import json
from pathlib import Path
from zipfile import ZipFile

import pandas as pd

from scripts.download_raw import BASE, download_asset

DIRECTORIO = Path(__file__).resolve().parent
ANIOS = tuple(range(2020, 2025))
PARTICIONES = {2021: "entrenamiento", 2022: "entrenamiento", 2023: "validacion", 2024: "prueba"}
ESTADOS = (1, 2, 4, 5, 6, 8, 9, 10, 11, 12, 13, 15, 16, 17, 18, 19, 20, 21, 22, 23,
           24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42,
           44, 45, 46, 47, 48, 49, 50, 51, 53, 54, 55, 56)
CATEGORIAS_CLAS = ["STATE", "MONTH", "DAY_WEEK", "HOUR", "LGT_COND", "MAN_COLL"]
NUMERICAS_CLAS = ["VE_TOTAL"]
CATEGORIAS_REG = ["STATE", "MONTH"]
NUMERICAS_REG = ["MUERTES_MISMO_MES_PREV", "MEDIA_MENSUAL_PREV"]
CLAVE_CASO = ["YEAR", "STATE", "ST_CASE"]
CLAVE_MES = ["YEAR", "STATE", "MONTH"]
CAMPOS = ["YEAR", "ST_CASE", *CATEGORIAS_CLAS, *NUMERICAS_CLAS, "FATALS"]
ARCHIVO_CLAS = "clasificacion.csv.gz"
ARCHIVO_REG = "regresion.csv"


def fuentes():
    return json.loads((DIRECTORIO / "originales.json").read_text(encoding="utf-8"))


def leer_accidentes(zip_path, nombre_csv, anio):
    with ZipFile(zip_path) as archivo, archivo.open(nombre_csv) as flujo:
        # Algunas ediciones conservan una marca UTF-8 antes de la cabecera.
        if flujo.read(3) != b"\xef\xbb\xbf":
            flujo.seek(0)
        casos = pd.read_csv(flujo, encoding="latin1", usecols=CAMPOS, dtype="int64")
    validos = (
        casos["YEAR"].eq(anio)
        & casos["ST_CASE"].gt(0)
        & casos["MONTH"].between(1, 12)
        & casos["FATALS"].ge(1)
        & casos["VE_TOTAL"].ge(1)
        & casos["DAY_WEEK"].between(1, 7)
        & casos["HOUR"].isin([*range(24), 99])
        & casos["LGT_COND"].between(1, 9)
        & casos["MAN_COLL"].isin([0, 1, 2, 6, 7, 8, 9, 10, 11, 98, 99])
    )
    if not validos.all() or set(casos["STATE"]) != set(ESTADOS):
        raise ValueError(f"Códigos fuera del universo definido en FARS {anio}")
    if casos.duplicated(CLAVE_CASO).any():
        raise ValueError(f"Clave de siniestro duplicada en FARS {anio}")
    return casos.loc[:, CAMPOS]


def construir_regresion(casos):
    combinaciones = pd.MultiIndex.from_product(
        [ANIOS, ESTADOS, range(1, 13)], names=CLAVE_MES
    )
    panel = (
        casos.groupby(CLAVE_MES)["FATALS"].sum()
        .reindex(combinaciones, fill_value=0)
        .rename("MUERTES")
        .reset_index()
    )
    historia = panel.rename(columns={"MUERTES": "MUERTES_MISMO_MES_PREV"})
    historia["MEDIA_MENSUAL_PREV"] = historia.groupby(["YEAR", "STATE"])[
        "MUERTES_MISMO_MES_PREV"
    ].transform("mean")
    historia["YEAR"] = historia["YEAR"] + 1
    regresion = panel.loc[panel["YEAR"].isin(PARTICIONES)].merge(
        historia, on=CLAVE_MES, how="left", validate="one_to_one"
    )
    regresion["particion"] = regresion["YEAR"].map(PARTICIONES)
    return regresion


def reconstruir(originales, salida):
    ediciones = fuentes()
    tablas = []
    for origen in ediciones:
        anio = origen["year"]
        archivo = download_asset(f"{BASE}fars-raw-{anio}/", origen, originales)
        tablas.append(leer_accidentes(archivo, origen["member"], anio))
    casos = pd.concat(tablas, ignore_index=True)
    clasificacion = casos.loc[casos["YEAR"].isin(PARTICIONES)].copy()
    clasificacion["MULTIPLES_MUERTES"] = clasificacion["FATALS"].ge(2).astype(int)
    clasificacion["particion"] = clasificacion["YEAR"].map(PARTICIONES)
    clasificacion = clasificacion.sort_values(CLAVE_CASO, ignore_index=True)
    regresion = construir_regresion(casos)
    validar_limpios(clasificacion, regresion, ediciones)
    salida.mkdir(parents=True, exist_ok=True)
    clasificacion.to_csv(
        salida / ARCHIVO_CLAS, index=False, lineterminator="\n",
        compression={"method": "gzip", "mtime": 0},
    )
    regresion.to_csv(salida / ARCHIVO_REG, index=False, lineterminator="\n")
    return clasificacion, regresion


def validar_limpios(clasificacion, regresion, ediciones):
    for datos, clave in [(clasificacion, CLAVE_CASO), (regresion, CLAVE_MES)]:
        if datos.isna().any().any() or datos.duplicated(clave).any():
            raise ValueError("Hay nulos o claves duplicadas en los conjuntos limpios")
        if not datos["particion"].eq(datos["YEAR"].map(PARTICIONES)).all():
            raise ValueError("La partición no coincide con el año de los registros")
    if not clasificacion["MULTIPLES_MUERTES"].eq(clasificacion["FATALS"].ge(2)).all():
        raise ValueError("La etiqueta binaria no coincide con FATALS")

    muestras = {e["year"]: e["crashes"] for e in ediciones if e["year"] in PARTICIONES}
    if clasificacion.groupby("YEAR").size().to_dict() != muestras:
        raise ValueError("El total de siniestros por año no coincide con el inventario")
    indice = pd.MultiIndex.from_product(
        [PARTICIONES, ESTADOS, range(1, 13)], names=CLAVE_MES
    )
    muertes = clasificacion.groupby(CLAVE_MES)["FATALS"].sum().reindex(indice, fill_value=0)
    conteos = regresion.set_index(CLAVE_MES)["MUERTES"].sort_index()
    if not conteos.equals(muertes.rename("MUERTES")):
        raise ValueError("El panel de regresión no coincide con la suma de FATALS")


def cargar_limpios(directorio):
    clasificacion = pd.read_csv(directorio / ARCHIVO_CLAS)
    regresion = pd.read_csv(directorio / ARCHIVO_REG, float_precision="round_trip")
    validar_limpios(clasificacion, regresion, fuentes())
    return clasificacion, regresion
