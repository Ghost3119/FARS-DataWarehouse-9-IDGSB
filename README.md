# FARS — Datos originales · Equipo 2 · 9 IDGS B

Repositorio académico para el análisis de siniestros viales mortales.

La [práctica de análisis supervisado de la Unidad 3](supervisado/README.md) incluye el código, los conjuntos limpios y los resultados de clasificación y regresión para las **50 ediciones nacionales FARS de 1975 a 2024**. La [cobertura anual](supervisado/resultados/cobertura_anual.csv) muestra los conteos y el uso de cada año.

## Integrantes

- Camacho Ibarra Jorge Jair
- Santana Chavez Saul Fabian
- Valdez Lara Yahir Alejandro

## Caso de uso

Una dirección de seguridad vial quiere identificar combinaciones de horario, ubicación y condiciones de circulación asociadas con mayor cantidad de siniestros mortales.

## Estado y alcance

**Importación completada el 16 de octubre de 2026:** 433 archivos originales, 54 grupos publicados y 1,734,358,438 bytes. Se comprobó que no falta ningún archivo del manifiesto. [Ejecución completada correctamente](https://github.com/Ghost3119/FARS-DataWarehouse-9-IDGSB/actions/runs/38983581754). Cada grupo incluye su archivo de sumas SHA-256.

Esta colección conserva las **fuentes crudas** tal como las publica NHTSA. La Unidad 3 armoniza por separado la tabla de siniestros de las 50 ediciones nacionales.

El inventario contiene **433 archivos**, aproximadamente **1.62 GiB según los tamaños redondeados del catálogo**, correspondientes a **1975–2024**, archivos nacionales, Puerto Rico cuando aparece, auxiliares, notas y documentos publicados dentro del directorio FARS. Incluye todos los formatos listados, no solamente CSV. El alcance es el contenido enlazado recursivamente desde ese directorio a la fecha del inventario; no incluye documentos externos enlazados dentro de los PDF.

- [Índice por año y archivo](sources/INDEX.md)
- [Descargas originales en Releases](https://github.com/Ghost3119/FARS-DataWarehouse-9-IDGSB/releases)
- [Estado de la copia en Actions](https://github.com/Ghost3119/FARS-DataWarehouse-9-IDGSB/actions)
- [Manifiesto de procedencia](sources/manifest.json)
- [Fuente oficial NHTSA](https://www.nhtsa.gov/file-downloads?p=nhtsa/downloads/FARS/)

Cada Release se hace pública únicamente después de copiar todos los archivos de su grupo y comprobar sus tamaños remotos. Mientras la importación esté en ejecución, pueden faltar grupos. La ejecución verde de Actions y las Releases publicadas permiten verificar la finalización.

## Descargar los originales

Los archivos grandes se conservan como **assets de Releases del mismo repositorio**, para no incorporar aproximadamente 1.6 GiB de binarios al historial de Git. Un `git clone` descarga documentación y scripts, no esos assets. Los ZIP se conservan exactamente como los publica NHTSA; no se vuelven a comprimir ni se extraen automáticamente.

Con Python 3.10 o posterior, sin instalar paquetes adicionales:

```bash
python scripts/download_raw.py
```

Para descargar solamente un año:

```bash
python scripts/download_raw.py --group 2023
```

El script restaura las rutas originales en `data/raw/`, verifica cada SHA-256 y no reemplaza archivos locales modificados. Se detiene si una Release aún no existe o una descarga falla; puede repetirse y omite archivos ya verificados. Para extraer un ZIP y trabajar sobre sus CSV, el equipo debe hacerlo en una carpeta separada, conservando el original.

## Organización y trazabilidad

- `sources/manifest.json`: rutas, URLs, grupos, tamaños y fechas informados por el catálogo.
- `sources/INDEX.md`: índice navegable de las 433 fuentes.
- `scripts/publish_raw.py`: copia binaria NHTSA → GitHub Releases. No procesa registros.
- `scripts/download_raw.py`: descarga las copias y comprueba su integridad.
- `.github/workflows/import-raw.yml`: ejecución de la copia por grupos.
- Cada Release contiene `SHA256SUMS.json` con URL, ruta original, nombre del asset, bytes y SHA-256 calculados al descargar.

Los nombres de assets reemplazan `/` por `__` y espacios por `_` porque Releases no admite carpetas. Esto no modifica los bytes; el manifiesto conserva el nombre y ruta originales. El descargador restaura esa estructura. Las ediciones publicadas no se sobrescriben automáticamente al repetir el workflow.

## Alcance de los datos

La colección de Releases sirve como fuente del diseño dimensional y de la práctica de la Unidad 3. FARS cubre los siniestros mortales de Estados Unidos, con archivos de Puerto Rico diferenciados en la fuente. Para estimar el riesgo por viaje se necesitarían datos de exposición y de siniestros sin muertes.

## Referencias

National Highway Traffic Safety Administration. (s. f.). *NHTSA file downloads: FARS*. https://www.nhtsa.gov/file-downloads?p=nhtsa/downloads/FARS/

National Highway Traffic Safety Administration. (s. f.). *Fatality Analysis Reporting System*. https://www.nhtsa.gov/research-data/fatality-analysis-reporting-system-fars

La procedencia y documentación de cada edición están incluidas en el índice; se conserva la atribución a NHTSA. Consulta los avisos de la fuente para los términos aplicables.
