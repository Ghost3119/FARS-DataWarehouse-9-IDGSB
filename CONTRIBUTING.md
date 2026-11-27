# FARS — Guía de colaboración · Equipo 2 · 9 IDGS B

Guía práctica de trabajo colaborativo en Git y GitHub para el repositorio del proyecto FARS. Para requisitos de entorno, descarga de datos y ejecución de scripts, consulta [README.md](README.md).

## Contenido

- [Clonar y actualizar el repositorio](#clonar-y-actualizar-el-repositorio)
- [Crear ramas](#crear-ramas)
- [Realizar commits](#realizar-commits)
- [Subir cambios mediante Pull Requests](#subir-cambios-mediante-pull-requests)
- [Archivos de datos que no deben subirse a GitHub](#archivos-de-datos-que-no-deben-subirse-a-github)

## Clonar y actualizar el repositorio

Todos los comandos de esta guía se ejecutan **desde la raíz del repositorio** (los ejemplos usan PowerShell en Windows y funcionan igual en `bash` en macOS y Linux).

Para obtener una copia local por primera vez:

```powershell
git clone https://github.com/Ghost3119/FARS-DataWarehouse-9-IDGSB.git
cd FARS-DataWarehouse-9-IDGSB
```

Ten en cuenta que `git clone` descarga únicamente el código, la documentación, los índices y los conjuntos limpios compactos; **no** descarga los **433 archivos originales (~1.62 GiB)** almacenados en [GitHub Releases](https://github.com/Ghost3119/FARS-DataWarehouse-9-IDGSB/releases). Si necesitas las fuentes originales de NHTSA en `data/raw/`, descárgalas por separado como se indica en [README.md](README.md):

```powershell
python scripts/download_raw.py
```

También puedes descargar un solo año si no necesitas la colección completa (por ejemplo, `python scripts/download_raw.py --group 2023`). Si vas a ejecutar las prácticas de Python, instala las dependencias una sola vez desde [supervisado/requirements.txt](supervisado/requirements.txt):

```powershell
python -m pip install -r supervisado/requirements.txt
```

Antes de comenzar cualquier tarea nueva, sincroniza siempre tu rama `main` local con el repositorio remoto:

```powershell
git checkout main
git pull origin main
```

## Crear ramas

No trabajes ni realices commits directos sobre `main`. Cada tarea, corrección o documentación debe desarrollarse en una rama propia creada desde la versión actualizada de `main`.

### Convención de nombres

Usa únicamente **minúsculas**, sin acentos ni espacios, separando palabras con guiones (`-`) y comenzando con un **verbo en infinitivo** que describa la acción (siguiendo el formato ya usado en el repositorio, como `documentar-requisitos-readme`):

| Tipo de cambio | Ejemplo de rama | Uso habitual |
| --- | --- | --- |
| Documentación | `documentar-guia-colaboracion` | Guías, documentación técnica y notas de revisión |
| Corrección | `corregir-validacion-datos` | Arreglos en scripts, validaciones o rutas |
| Implementación | `implementar-graficas-u5` | Nuevas prácticas, módulos o visualizaciones |
| Mantenimiento | `actualizar-dependencias-python` | Ajustes de configuración o exclusiones del proyecto |

Crea y cambia a tu rama de trabajo desde `main`:

```powershell
git checkout -b <nombre-rama>
```

Ejemplo:

```powershell
git checkout -b documentar-guia-colaboracion
```

## Realizar commits

Mantén commits pequeños y enfocados en un solo cambio lógico para facilitar la revisión y el historial del proyecto.

### Convención de mensajes

Siguiendo el historial real del repositorio (`git log`), redacta mensajes breves en **español**, iniciando con un **verbo en infinitivo con mayúscula inicial** y **sin punto final**:

| Ejemplo de mensaje | Cambio representado |
| --- | --- |
| `Documentar guía de colaboración en CONTRIBUTING.md` | Alta o actualización de documentación |
| `Actualizar exclusiones de datos locales en .gitignore` | Ajustes en reglas de archivos ignorados |
| `Corregir validación de cobertura anual en supervisado` | Corrección puntual en código o datos limpios |
| `Implementar gráficas de evaluación para la Unidad 5` | Nueva funcionalidad o entregable |

### Flujo práctico

Revisa siempre qué archivos cambiaron antes de confirmar y evita agregar carpetas completas a ciegas (`git add .`) para no incluir archivos locales no deseados:

```powershell
git status
git diff
git add <archivo>
git commit -m "Documentar guía de colaboración en CONTRIBUTING.md"
```

| Comando | Propósito |
| --- | --- |
| `git status` | Muestra la rama activa y los archivos nuevos o modificados |
| `git diff` | Permite revisar línea por línea los cambios antes de preparar el commit |
| `git add <archivo>` | Agrega al área de preparación únicamente el archivo deseado |
| `git commit -m "..."` | Registra el cambio en el historial local con el mensaje acordado |

## Subir cambios mediante Pull Requests

Cuando tus commits locales estén revisados y listos, publica tu rama en GitHub:

```powershell
git push -u origin <nombre-rama>
```

### Abrir y revisar el Pull Request en GitHub

1. Entra al repositorio en GitHub y haz clic en el botón **Compare & pull request** que aparece para tu rama recién subida.
2. Verifica que la rama destino sea `main` (`base: main` ← `compare: <nombre-rama>`).
3. Escribe un título claro y una descripción breve que incluya:
   - **Resumen:** qué problema resuelve o qué aporta el cambio.
   - **Archivos tocados:** lista exacta de archivos creados o modificados.
   - **Verificación:** comandos ejecutados o revisiones realizadas localmente para comprobar que todo funciona.
4. Solicita la revisión de **al menos un compañero del equipo** antes de hacer clic en **Merge pull request**. No fusiones tus propios cambios sin revisión previa.

### Limpieza después del Merge

Una vez aprobado y fusionado el Pull Request en `main`, actualiza tu copia local y elimina la rama ya integrada:

```powershell
git checkout main
git pull origin main
git branch -d <nombre-rama>
```

## Archivos de datos que no deben subirse a GitHub

GitHub impone un límite estricto de **100 MiB por archivo** (y advierte a partir de 50 MiB). Además, subir binarios pesados o tablas crudas al historial de Git incrementa permanentemente el tamaño del repositorio, vuelve lento cada `git clone` para todo el equipo y duplica información que ya se conserva con trazabilidad SHA-256 en GitHub Releases.

Por esta razón, el archivo [.gitignore](.gitignore) bloquea los directorios y extensiones locales de datos pesados, entornos virtuales y temporales.

### Qué NO se sube al repositorio

| Ruta o patrón | Motivo |
| --- | --- |
| `data/raw/` | Carpeta local donde `scripts/download_raw.py` restaura las descargas |
| `*.zip` | Archivos originales de NHTSA; los 433 originales (~1.62 GiB) viven en [GitHub Releases](https://github.com/Ghost3119/FARS-DataWarehouse-9-IDGSB/releases) |
| CSV crudos extraídos (`ACCIDENT.csv`, `PERSON.csv`, `VEHICLE.csv`, etc.) | Pesan decenas o cientos de MiB al descomprimirse; si necesitas inspeccionarlos, extráelos en una carpeta temporal fuera del versionado |
| `*.partial` | Descargas interrumpidas o incompletas generadas por el script de descarga |
| `.venv/`, `venv/`, `__pycache__/`, `*.pyc` | Entornos virtuales locales y archivos compilados de caché de Python |
| `.DS_Store`, `Thumbs.db` | Archivos ocultos de metadatos generados por macOS y Windows |

### Qué SÍ se versiona en el repositorio

| Categoría | Rutas versionadas |
| --- | --- |
| Manifiestos e índices | [sources/manifest.json](sources/manifest.json), [sources/INDEX.md](sources/INDEX.md), [supervisado/originales.json](supervisado/originales.json) |
| Conjuntos limpios compactos | [supervisado/datos/clasificacion.csv.gz](supervisado/datos/clasificacion.csv.gz), [supervisado/datos/regresion.csv](supervisado/datos/regresion.csv), [no_supervisado/datos/perfiles_estado_anio.csv](no_supervisado/datos/perfiles_estado_anio.csv) |
| Resultados reproducibles | `supervisado/resultados/` (`clasificacion.png`, `cobertura_anual.csv`, `evaluacion.json`, `regresion.png`) y `no_supervisado/resultados/` (`asignaciones_prueba.csv`, `evaluacion.json`, `mapa_prueba.png`, `seleccion.png`) |
| Código, configuración y documentación | Scripts en `scripts/`, `supervisado/` y `no_supervisado/`, flujo en `.github/workflows/import-raw.yml`, [supervisado/requirements.txt](supervisado/requirements.txt), [.gitignore](.gitignore), [README.md](README.md) y esta guía |
