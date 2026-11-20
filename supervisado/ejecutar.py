"""Reproduce el análisis desde la raíz con python -m supervisado.ejecutar."""

import argparse
import json
from pathlib import Path
from platform import python_version
from time import perf_counter

import matplotlib
import numpy
import pandas
import scipy
import sklearn
from threadpoolctl import threadpool_limits

from .datos import DIRECTORIO, PARTICIONES, cargar_limpios, fuentes, reconstruir
from .graficas import grafica_clasificacion, grafica_regresion
from .modelos import RECALL_MINIMO, SEMILLA, evaluar_clasificacion, evaluar_regresion


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reconstruir", action="store_true", help="Verificar o descargar los cinco ZIP originales")
    parser.add_argument("--originales", type=Path, default=DIRECTORIO.parent / "data" / "raw")
    parser.add_argument("--datos", type=Path, default=DIRECTORIO / "datos")
    parser.add_argument("--salida", type=Path, default=DIRECTORIO / "resultados")
    parser.add_argument("--hilos", type=int, default=4, help="Hilos de CPU para los bosques aleatorios")
    args = parser.parse_args()
    if args.hilos < 1:
        parser.error("--hilos debe ser mayor que cero")

    inicio = perf_counter()
    if args.reconstruir:
        clas, reg = reconstruir(args.originales, args.datos)
    else:
        clas, reg = cargar_limpios(args.datos)
    print(f"Datos validados: {len(clas):,} siniestros y {len(reg):,} observaciones estado-mes", flush=True)
    with threadpool_limits(limits=2):
        clasificacion, curvas = evaluar_clasificacion(clas, args.hilos)
        regresion = evaluar_regresion(reg, args.hilos)
    args.salida.mkdir(parents=True, exist_ok=True)
    grafica_clasificacion(clasificacion, curvas, args.salida / "clasificacion.png")
    grafica_regresion(regresion, args.salida / "regresion.png")

    resumen = clas.groupby("YEAR").agg(
        siniestros=("FATALS", "size"),
        multiples_muertes=("MULTIPLES_MUERTES", "sum"),
        muertes=("FATALS", "sum"),
    )
    resumen["particion"] = resumen.index.map(PARTICIONES)
    resumen["estado_mes"] = reg.groupby("YEAR").size()
    informe = {
        "entorno": {
            "python": python_version(),
            "numpy": numpy.__version__,
            "pandas": pandas.__version__,
            "scipy": scipy.__version__,
            "scikit_learn": sklearn.__version__,
            "matplotlib": matplotlib.__version__,
            "hilos_bosques": args.hilos,
            "semilla": SEMILLA,
            "computo": "CPU",
        },
        "segundos": round(perf_counter() - inicio, 2),
        "recall_minimo_validacion": RECALL_MINIMO,
        "originales": fuentes(),
        "muestras": resumen.to_dict(orient="index"),
        "clasificacion": clasificacion,
        "regresion": regresion,
    }
    destino = args.salida / "evaluacion.json"
    destino.write_text(json.dumps(informe, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Evaluación en {informe['segundos']:.2f} s con CPU local. Resultados: {destino}")


if __name__ == "__main__":
    main()
