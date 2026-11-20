# Unidad 4 Saber Hacer · Análisis no supervisado con FARS

La práctica del Equipo 2, 9 IDGS B, compara agrupaciones de perfiles estatales de siniestros mortales y estudia cuánta información conservan sus componentes principales. Usa las 50 ediciones nacionales de 1975 a 2024.

## Fuentes y conjunto transformado

- [ZIP nacionales originales en GitHub Releases](https://github.com/Ghost3119/FARS-DataWarehouse-9-IDGSB/releases) y [manifiesto por año con el SHA-256 y la ruta de ACCIDENT](../supervisado/originales.json).
- [Tabla homologada de la U3](../supervisado/datos/clasificacion.csv.gz), que aporta 1 872 452 siniestros de los 50 estados y el Distrito de Columbia.
- [Perfiles de estado y año](datos/perfiles_estado_anio.csv), con 2 550 filas. Incluye seis proporciones, número de siniestros, denominadores válidos y la partición temporal.

Cada proporción usa solo registros con el campo correspondiente informado. `oscuridad` cuenta LUZ = 2. `fin_semana` usa DAY_WEEK = 1 o 7. `madrugada` usa HOUR de 0 a 5. `frontal`, `angular` y `roce_lateral` corresponden a TIPO_COLISION = 2, 4 y 5. STATE y YEAR identifican el perfil. El ajuste usa las seis proporciones con el mismo peso por fila.

| Partición | Años | Perfiles | Uso |
| --- | --- | ---: | --- |
| Ajuste | 1975–2014 | 2 040 | Escalador, centroides y componentes |
| Validación | 2015–2019 | 255 | Selección de k y diagnóstico de reconstrucción |
| Prueba | 2020–2024 | 255 | Comparación de las configuraciones |

## Reproducir la práctica

Desde la raíz del repositorio, con Python 3.14.3 de referencia:

```powershell
python -m pip install -r supervisado/requirements.txt
python -m no_supervisado.ejecutar
```

[datos.py](datos.py) agrega y valida la cobertura de perfiles. [modelos.py](modelos.py) ajusta StandardScaler, K-means y PCA, con semilla 42 y 20 inicializaciones por valor de k. [ejecutar.py](ejecutar.py) integra la práctica y registra el SHA-256 de entrada, las versiones y los resultados. La ejecución usa CPU y reutiliza los datos disponibles localmente. Se pueden indicar carpetas alternativas con `--datos` y `--salida`.

## Antes y después

La configuración inicial usa tres grupos y dos componentes. Para K-means se eligió el mayor valor de silueta en 2015–2019 entre k de 2 a 6. Para PCA se retuvo el menor número de componentes que conserva al menos el 80 % de varianza del ajuste.

| Medida | Inicial | Optimizada |
| --- | ---: | ---: |
| Grupos K-means | 3 | 2 |
| Silueta en prueba | 0,157 | 0,238 |
| Davies–Bouldin en prueba | 1,710 | 1,408 |
| Calinski–Harabasz en prueba | 46,3 | 66,7 |
| Componentes de PCA | 2 | 4 |
| Varianza de ajuste retenida | 57,8 % | 88,2 % |
| RMSE de reconstrucción en prueba | 0,673 | 0,349 |

El [registro de evaluación](resultados/evaluacion.json) contiene los candidatos y métricas. Las [asignaciones de prueba](resultados/asignaciones_prueba.csv) se pueden contrastar con la [visualización de grupos](resultados/mapa_prueba.png) y la [gráfica de selección](resultados/seleccion.png). Los colores del plano corresponden a K-means ajustado en seis proporciones. Los grupos resumen composiciones de siniestros mortales. Estimar el riesgo por viaje requiere datos de exposición.
