# Unidad 3 Saber Hacer · Análisis supervisado con FARS

El Equipo 2, 9 IDGS B, compara modelos para dos decisiones de seguridad vial con **las 50 ediciones nacionales de FARS, de 1975 a 2024**. La clasificación prioriza la revisión de siniestros mortales con dos o más muertes. La regresión estima las muertes mensuales por estado con datos del año anterior.

## Reproducir en CPU

Ejecuta desde la raíz del repositorio. El entorno verificado usa Python 3.14.3 y las versiones fijadas en [requirements.txt](requirements.txt).

```powershell
python -m pip install -r supervisado/requirements.txt
python -m supervisado.ejecutar
```

Los conjuntos limpios incluidos permiten entrenar con los paquetes ya instalados y sin descargar datos. El proceso guarda la [cobertura de los 50 años](resultados/cobertura_anual.csv), el [registro de la evaluación](resultados/evaluacion.json), la [curva de precisión y recall y la matriz de confusión](resultados/clasificacion.png) y la [comparación de MAE](resultados/regresion.png). Puedes dirigir otra ejecución a una carpeta distinta con `--salida <directorio>`.

## Reconstruir desde los originales

```powershell
python -m supervisado.ejecutar --reconstruir
```

Este comando reutiliza las copias verificadas de `data/raw/` y descarga de [GitHub Releases](https://github.com/Ghost3119/FARS-DataWarehouse-9-IDGSB/releases) los ZIP nacionales faltantes. [originales.json](originales.json) identifica los 50 originales, la ruta de la tabla `ACCIDENT` de cada edición, el enlace de NHTSA y el SHA-256. La descarga completa ocupa aproximadamente 617 MiB. El código verifica cada ZIP antes de abrirlo.

## Datos limpios y variables

| Archivo | Unidad y tamaño | Objetivo |
| --- | --- | --- |
| [clasificacion.csv.gz](datos/clasificacion.csv.gz) | 1 872 452 siniestros de 1975 a 2024 | `MULTIPLES_MUERTES` vale 1 si `FATALS >= 2` y 0 si `FATALS == 1`. |
| [regresion.csv](datos/regresion.csv) | 30 600 combinaciones de estado y mes de 1975 a 2024 | `MUERTES` suma `FATALS` para la combinación. |

- **Clasificación.** Entradas `STATE`, `MONTH`, `DAY_WEEK`, `HOUR`, `LUZ`, `TIPO_COLISION` y `VE_FORMS`. Las seis primeras son categóricas. El código 24 de hora se convierte a 0 para representar la medianoche. Los valores sin dato conservan sus categorías. `VE_FORMS` cuenta formularios de vehículos en circulación. Los ceros de 1975–1981 reflejan la práctica de registro de la época.
- **Regresión.** Entradas `STATE`, `MONTH`, `MUERTES_MISMO_MES_PREV` y `MEDIA_MENSUAL_PREV`. El panel contiene 612 observaciones por año para los 50 estados y el Distrito de Columbia. Las filas de 1975 tienen partición `historia` y rezagos vacíos. Sus conteos permiten calcular los predictores de 1976.
- **Control de registros.** El año de la edición normaliza la clave `YEAR, STATE, ST_CASE`. Se excluyen 12 filas históricas con `FATALS = 0` porque la tarea clasifica siniestros con al menos una muerte. Los cuatro casos con mes desconocido se conservan en clasificación y sus muertes figuran en `muertes_sin_mes` en la cobertura anual. La agregación mensual requiere un mes del 1 al 12.

Las equivalencias se basan en los elementos C4A, C8, C9A, C20, C25 y C101 del [manual analítico FARS 1975–2024](https://doi.org/10.21949/dz60-ft73). `LUZ` usa 1 para luz diurna, 2 para oscuridad, 3 para amanecer u ocaso, 4 para otras condiciones y 99 para datos sin reporte o desconocidos. `TIPO_COLISION` agrupa 0 como categoría original sin choque entre vehículos según la edición, 1 como alcance, 2 como frontal, 3 como trasera con trasera, 4 como angular, 5 como roce lateral, 6 como trasera con costado, 7 como otra y 99 como sin reporte o desconocida.

## Diseño y evidencia

| Periodo | Papel | Siniestros | Estado y mes |
| --- | --- | ---: | ---: |
| 1975 | Entrenamiento de clasificación e historia de regresión | 39 152 | 612 |
| 1976–2022 | Entrenamiento de los dos modelos | 1 759 234 | 28 764 |
| 2023 | Elección de hiperparámetros y umbrales | 37 769 | 612 |
| 2024 | Prueba de las configuraciones seleccionadas | 36 297 | 612 |

[datos.py](datos.py) verifica y transforma las fuentes. [modelos.py](modelos.py) ajusta regresión logística, Ridge y bosques aleatorios. Usa precisión promedio (AP) para seleccionar las configuraciones de clasificación y fija el umbral con un recall mínimo de 0,50 en validación. Para regresión selecciona por MAE. [ejecutar.py](ejecutar.py) integra los pasos y deja en el JSON las configuraciones, tiempos de ajuste, métricas y matrices para verificarlos.

En la prueba de 2024, la regresión logística obtuvo AP de 0,155 y detectó el 51,8 % de los siniestros con múltiples muertes con el umbral validado. En regresión, el bosque aleatorio obtuvo MAE de 8,00 muertes por estado y mes, frente al 9,46 de la regla estacional. La reconstrucción y evaluación completas tardaron 321,73 segundos en CPU con los ZIP ya descargados.

FARS reúne siniestros mortales. Para generalizar a todo el tránsito se necesitarían datos de siniestros sin muertes y de exposición. La estimación mensual supone que la edición anual anterior está disponible al momento de pronosticar.
