# Revisión de datos de la Unidad 4

Importé el [CSV de perfiles](datos/perfiles_estado_anio.csv) con `Import-Csv` y agrupé las filas por `YEAR`. Comparé los años encontrados con el intervalo 1975–2024 y comprobé que los 50 años tienen exactamente 51 filas cada uno. Conté 2 550 filas y 2 550 pares únicos de `YEAR` y `STATE`, lo que confirma que no hay perfiles duplicados.

En cada fila comprobé que `n_casos` fuera un entero positivo y que los denominadores `n_luz`, `n_dia`, `n_hora` y `n_colision` fueran enteros entre 1 y `n_casos`. Las cinco columnas tuvieron cero valores inválidos. El mínimo de todas fue 14. Los máximos, en ese orden, fueron 4 975, 4 970, 4 975, 4 974 y 4 975.
