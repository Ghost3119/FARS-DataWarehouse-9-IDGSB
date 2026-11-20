# Unidad 3 Saber Hacer · Análisis supervisado con FARS

El Equipo 2, 9 IDGS B, compara modelos para dos decisiones de seguridad vial. La clasificación prioriza la revisión de siniestros mortales con dos o más muertes. La regresión estima las muertes mensuales por estado con datos del año anterior.

## Reproducir en CPU

Ejecuta desde la raíz del repositorio. El entorno verificado usa Python 3.14.3 y las versiones fijadas en [requirements.txt](requirements.txt).

```powershell
python -m pip install -r supervisado/requirements.txt
python -m supervisado.ejecutar
```

Los conjuntos limpios incluidos permiten entrenar con los paquetes ya instalados y sin descargar datos. El proceso guarda el [registro JSON de la evaluación](resultados/evaluacion.json), la [curva de precisión–recall y la matriz de confusión](resultados/clasificacion.png) y la [comparación de MAE](resultados/regresion.png). Puedes dirigir otra ejecución a una carpeta distinta con `--salida <directorio>`.

## Reconstruir desde los originales

```powershell
python -m supervisado.ejecutar --reconstruir
```

Este comando reutiliza las copias verificadas de `data/raw/` y descarga de [GitHub Releases](https://github.com/Ghost3119/FARS-DataWarehouse-9-IDGSB/releases) los ZIP nacionales faltantes de 2020 a 2024. [originales.json](originales.json) identifica los cinco ZIP, el archivo `accident.csv` de cada edición, el enlace de NHTSA y el SHA-256. El primer uso con los originales ausentes descarga aproximadamente 160 MiB. El código verifica los ZIP antes de abrirlos.

## Datos limpios y variables

| Archivo | Unidad y tamaño | Objetivo |
| --- | --- | --- |
| [clasificacion.csv.gz](datos/clasificacion.csv.gz) | 153 273 siniestros de 2021 a 2024 | `MULTIPLES_MUERTES` vale 1 si `FATALS >= 2` y 0 si `FATALS == 1`. |
| [regresion.csv](datos/regresion.csv) | 2 448 combinaciones de estado y mes de 2021 a 2024 | `MUERTES` suma `FATALS` para la combinación. |

- **Clasificación.** Entradas `STATE`, `MONTH`, `DAY_WEEK`, `HOUR`, `LGT_COND`, `MAN_COLL` y `VE_TOTAL`. Las seis primeras son categóricas. Se conservan los códigos FARS de valores desconocidos o sin reporte como categorías. `YEAR`, `ST_CASE` y `FATALS` permiten auditar las filas y la etiqueta.
- **Regresión.** Entradas `STATE`, `MONTH`, `MUERTES_MISMO_MES_PREV` y `MEDIA_MENSUAL_PREV`. Los dos conteos históricos provienen del mismo estado en el año previo. La historia de 2020 permite calcular las primeras entradas.
- **Cobertura.** 50 estados y el Distrito de Columbia. Las dos tablas tienen una columna `particion` con los periodos fijados de antemano. La preparación comprueba el formato de los códigos, la unicidad de las claves y la concordancia de los conteos entre ambas tablas.

## Diseño y evidencia

| Periodo | Papel | Siniestros | Estado y mes |
| --- | --- | ---: | ---: |
| 2021–2022 | Ajuste del preprocesamiento y los modelos | 79 207 | 1 224 |
| 2023 | Elección de hiperparámetros y umbrales | 37 769 | 612 |
| 2024 | Prueba de las configuraciones seleccionadas | 36 297 | 612 |

[datos.py](datos.py) verifica y transforma las fuentes. [modelos.py](modelos.py) ajusta regresión logística, Ridge y bosques aleatorios. Usa precisión promedio (AP) para seleccionar las configuraciones de clasificación y fija el umbral con un recall mínimo de 0,50 en validación. Para regresión selecciona por MAE. [ejecutar.py](ejecutar.py) integra los pasos y deja en el JSON las configuraciones, tiempos de ajuste, métricas y matrices para verificarlos.

En 2024, la logística logró AP de 0,154 y recall de 0,512 con el umbral validado. La referencia estacional obtuvo el menor MAE de regresión, 9,46 muertes por estado y mes. La lectura de estos valores depende de que FARS solo reúna siniestros mortales y de que el archivo anual previo esté disponible al momento de estimar.
