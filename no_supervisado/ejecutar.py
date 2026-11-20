"""Reproduce la práctica con python -m no_supervisado.ejecutar."""

import argparse
import hashlib
import json
from pathlib import Path
from platform import python_version
from time import perf_counter

import sklearn
from threadpoolctl import threadpool_limits

from .datos import DIRECTORIO, FUENTE, INDICADORES, construir_perfiles
from .graficas import mapa_prueba, seleccion
from .modelos import REINICIOS, SEMILLA, analizar


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--fuente", type=Path, default=FUENTE, help="CSV FARS homologado")
    cli.add_argument("--datos", type=Path, default=DIRECTORIO / "datos")
    cli.add_argument("--salida", type=Path, default=DIRECTORIO / "resultados")
    args = cli.parse_args()

    inicio = perf_counter()
    perfiles = construir_perfiles(args.fuente)
    with threadpool_limits(limits=3):
        resultados, asignaciones = analizar(perfiles)

    with args.fuente.open("rb") as archivo:
        origen = {"archivo": args.fuente.name,
                  "sha256": hashlib.file_digest(archivo, "sha256").hexdigest()}
    informe = {
        "fuente": origen,
        "entorno": {
            "python": python_version(), "scikit_learn": sklearn.__version__,
            "semilla": SEMILLA, "reinicios_kmeans": REINICIOS,
        },
        "siniestros": int(perfiles["n_casos"].sum()),
        "variables": INDICADORES,
        **resultados,
    }

    args.datos.mkdir(parents=True, exist_ok=True)
    args.salida.mkdir(parents=True, exist_ok=True)
    perfiles.to_csv(args.datos / "perfiles_estado_anio.csv", index=False, lineterminator="\n")
    asignaciones.to_csv(args.salida / "asignaciones_prueba.csv", index=False, lineterminator="\n")
    seleccion(informe, args.salida / "seleccion.png")
    mapa_prueba(informe, asignaciones, args.salida / "mapa_prueba.png")
    (args.salida / "evaluacion.json").write_text(
        json.dumps(informe, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"{informe['siniestros']:,} siniestros, {len(perfiles):,} perfiles, "
          f"{len(asignaciones)} asignaciones de prueba. Tiempo: {perf_counter() - inicio:.2f} s.")


if __name__ == "__main__":
    main()
