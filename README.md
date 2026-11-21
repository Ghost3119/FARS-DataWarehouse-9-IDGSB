# FARS — Datos originales · Equipo 2 · 9 IDGS B

Repositorio académico para el análisis de siniestros viales mortales a partir de las publicaciones anuales del *Fatality Analysis Reporting System* (FARS) de NHTSA.

## Contenido

- [Requisitos](#requisitos)
- [Inicio rápido](#inicio-rápido)
- [Descargar los datos](#descargar-los-datos)
- [Ejecutar los scripts de Python](#ejecutar-los-scripts-de-python)
- [Prácticas incluidas](#prácticas-incluidas)
- [Estado y alcance](#estado-y-alcance)
- [Organización y trazabilidad](#organización-y-trazabilidad)
- [Referencias](#referencias)

## Integrantes

- Camacho Ibarra Jorge Jair
- Santana Chavez Saul Fabian
- Valdez Lara Yahir Alejandro

## Caso de uso

Una dirección de seguridad vial quiere identificar combinaciones de horario, ubicación y condiciones de circulación asociadas con mayor cantidad de siniestros mortales.

## Requisitos

| Requisito | Detalle |
| --- | --- |
| Python | 3.10 o posterior para los scripts de descarga; 3.14.3 es la versión de referencia de las prácticas |
| `pip` | Incluido con Python; se usa para instalar las dependencias fijadas |
| Dependencias | Las seis versiones de [supervisado/requirements.txt](supervisado/requirements.txt): NumPy, pandas, SciPy, scikit-learn, matplotlib y threadpoolctl |
| Conexión a Internet | Necesaria solo para descargar los archivos desde GitHub Releases; las prácticas funcionan sin conexión con los datos limpios incluidos |
| Espacio en disco | Aproximadamente 617 MiB para los 50 ZIP nacionales; aproximadamente 1.6 GiB para la colección completa |
| Cómputo | CPU, sin GPU ni tarjetas especiales |
| Sistema operativo | Los ejemplos usan PowerShell en Windows; los mismos comandos funcionan en `bash` en macOS y Linux |
| Opcional | GitHub CLI (`gh`) solamente para publicar Releases; no se necesita para descargar ni para analizar |

Comprueba la versión e instala las dependencias una sola vez:

```powershell
python --version
python -m pip install -r supervisado/requirements.txt
```

## Inicio rápido

Clona el repositorio, instala las dependencias y ejecuta las dos prácticas desde la raíz:

```powershell
git clone https://github.com/Ghost3119/FARS-DataWarehouse-9-IDGSB.git
cd FARS-DataWarehouse-9-IDGSB
python -m pip install -r supervisado/requirements.txt
python -m supervisado.ejecutar
python -m no_supervisado.ejecutar
```

Resultado esperado en pantalla, entre otros mensajes:

```text
Datos validados: 1,872,452 siniestros y 30,600 observaciones estado-mes
Evaluación en <segundos> s con CPU local. Resultados: supervisado/resultados/evaluacion.json
1,872,452 siniestros, 2,550 perfiles, 255 asignaciones de prueba.
```

Los ejemplos anteriores usan los conjuntos limpios incluidos, por lo que no descargan datos.

## Descargar los datos

Los archivos grandes se conservan como **assets de Releases del mismo repositorio**, para no incorporar aproximadamente 1.6 GiB de binarios al historial de Git. Un `git clone` descarga documentación y scripts, no esos assets. Los ZIP se conservan exactamente como los publica NHTSA; no se vuelven a comprimir ni se extraen automáticamente.

### Descargar todos los archivos

Con Python 3.10 o posterior, sin instalar paquetes adicionales:

```powershell
python scripts/download_raw.py
```

### Descargar un solo año

```powershell
python scripts/download_raw.py --group 2023
```

También puedes abrir la página de [Descargas originales en Releases](https://github.com/Ghost3119/FARS-DataWarehouse-9-IDGSB/releases) y descargar el asset del grupo que necesites desde el navegador.

El script restaura las rutas originales en `data/raw/`, verifica cada SHA-256 y no reemplaza archivos locales modificados. Se detiene si una Release aún no existe o una descarga falla; puede repetirse y omite archivos ya verificados. Para extraer un ZIP y trabajar sobre sus CSV, el equipo debe hacerlo en una carpeta separada, conservando el original.

Ejemplo de la estructura que queda después de descargar el grupo `2023`:

```text
data/raw/
└── 2023/
    └── National/
        └── FARS2023NationalCSV.zip
```

La ruta exacta de cada archivo está documentada en [sources/INDEX.md](sources/INDEX.md) y en [sources/manifest.json](sources/manifest.json).

## Ejecutar los scripts de Python

Todos los comandos se ejecutan **desde la raíz del repositorio**. Las prácticas se invocan como módulos (`python -m paquete.ejecutar`) porque usan importaciones relativas entre sus propios archivos.

| Script desde la raíz | Qué hace | Ejemplo con opciones |
| --- | --- | --- |
| `python scripts/download_raw.py` | Descarga y verifica las copias originales | `python scripts/download_raw.py --group 2023 --output data/raw` |
| `python -m supervisado.ejecutar` | Entrena y evalúa clasificación y regresión | `python -m supervisado.ejecutar --reconstruir --hilos 4 --salida resultados/u3` |
| `python -m no_supervisado.ejecutar` | Construye perfiles, K-means y PCA | `python -m no_supervisado.ejecutar --datos no_supervisado/datos --salida resultados/u4` |
| `python scripts/publish_raw.py --group 2023` | Copia fuentes oficiales a Releases (solo mantenedores) | Requiere `gh` autenticado y las variables `GITHUB_REPOSITORY` y `GITHUB_SHA` |

Cada script muestra sus opciones con `--help`:

```powershell
python scripts/download_raw.py --help
python -m supervisado.ejecutar --help
python -m no_supervisado.ejecutar --help
```

Opciones más usadas:

- `--salida <directorio>`: cambia la carpeta donde se escriben los resultados.
- `--datos <directorio>`: usa otra carpeta de datos limpios o perfiles.
- `--reconstruir`: vuelve a generar los conjuntos de la Unidad 3 desde los ZIP originales descargados.
- `--group <grupo>`: limita la descarga a un año o grupo auxiliar.

## Prácticas incluidas

La [práctica de análisis supervisado de la Unidad 3](supervisado/README.md) incluye el código, los conjuntos limpios y los resultados de clasificación y regresión para las **50 ediciones nacionales FARS de 1975 a 2024**. La [cobertura anual](supervisado/resultados/cobertura_anual.csv) muestra los conteos y el uso de cada año.

```powershell
python -m supervisado.ejecutar
python -m supervisado.ejecutar --reconstruir
```

La [práctica de análisis no supervisado de la Unidad 4](no_supervisado/README.md) aplica K-means y PCA a perfiles estatales anuales, con datos transformados y una comparación reproducible antes y después de la optimización.

```powershell
python -m no_supervisado.ejecutar
```

Esta colección conserva las **fuentes crudas** tal como las publica NHTSA. La Unidad 3 armoniza por separado la tabla de siniestros de las 50 ediciones nacionales.

## Estado y alcance

**Importación completada el 16 de octubre de 2026:** 433 archivos originales, 54 grupos publicados y 1,734,358,438 bytes. Se comprobó que no falta ningún archivo del manifiesto. [Ejecución completada correctamente](https://github.com/Ghost3119/FARS-DataWarehouse-9-IDGSB/actions/runs/38983581754). Cada grupo incluye su archivo de sumas SHA-256.

El inventario contiene **433 archivos**, aproximadamente **1.62 GiB según los tamaños redondeados del catálogo**, correspondientes a **1975–2024**, archivos nacionales, Puerto Rico cuando aparece, auxiliares, notas y documentos publicados dentro del directorio FARS. Incluye todos los formatos listados, no solamente CSV. El alcance es el contenido enlazado recursivamente desde ese directorio a la fecha del inventario; no incluye documentos externos enlazados dentro de los PDF.

- [Índice por año y archivo](sources/INDEX.md)
- [Descargas originales en Releases](https://github.com/Ghost3119/FARS-DataWarehouse-9-IDGSB/releases)
- [Estado de la copia en Actions](https://github.com/Ghost3119/FARS-DataWarehouse-9-IDGSB/actions)
- [Manifiesto de procedencia](sources/manifest.json)
- [Fuente oficial NHTSA](https://www.nhtsa.gov/file-downloads?p=nhtsa/downloads/FARS/)

Cada Release se hace pública únicamente después de copiar todos los archivos de su grupo y comprobar sus tamaños remotos. Mientras la importación esté en ejecución, pueden faltar grupos. La ejecución verde de Actions y las Releases publicadas permiten verificar la finalización.

La colección de Releases sirve como fuente del diseño dimensional y de la práctica de la Unidad 3. FARS cubre los siniestros mortales de Estados Unidos, con archivos de Puerto Rico diferenciados en la fuente. Para estimar el riesgo por viaje se necesitarían datos de exposición y de siniestros sin muertes.

## Organización y trazabilidad

| Ruta | Contenido |
| --- | --- |
| `sources/manifest.json` | Rutas, URLs, grupos, tamaños y fechas informados por el catálogo |
| `sources/INDEX.md` | Índice navegable de las 433 fuentes |
| `scripts/publish_raw.py` | Copia binaria NHTSA → GitHub Releases; no procesa registros |
| `scripts/download_raw.py` | Descarga las copias y comprueba su integridad |
| `.github/workflows/import-raw.yml` | Ejecución de la copia por grupos |
| `supervisado/` | Práctica de la Unidad 3, datos limpios y resultados |
| `no_supervisado/` | Práctica de la Unidad 4, perfiles y resultados |

Cada Release contiene `SHA256SUMS.json` con URL, ruta original, nombre del asset, bytes y SHA-256 calculados al descargar.

Los nombres de assets reemplazan `/` por `__` y espacios por `_` porque Releases no admite carpetas. Esto no modifica los bytes; el manifiesto conserva el nombre y ruta originales. El descargador restaura esa estructura. Las ediciones publicadas no se sobrescriben automáticamente al repetir el workflow.

## Referencias

National Highway Traffic Safety Administration. (s. f.). *NHTSA file downloads: FARS*. https://www.nhtsa.gov/file-downloads?p=nhtsa/downloads/FARS/

National Highway Traffic Safety Administration. (s. f.). *Fatality Analysis Reporting System*. https://www.nhtsa.gov/research-data/fatality-analysis-reporting-system-fars

La procedencia y documentación de cada edición están incluidas en el índice; se conserva la atribución a NHTSA. Consulta los avisos de la fuente para los términos aplicables.
