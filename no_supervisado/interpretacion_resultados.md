# Interpretación de resultados de la Unidad 4

Al pasar de tres a dos grupos, la silueta subió de **0,1493 a 0,2669** en validación (+0,1176) y de **0,1570 a 0,2380** en prueba (+0,0810). Dos grupos obtuvieron la mayor silueta entre los candidatos de validación. [Métricas](resultados/evaluacion.json) · [Gráfica de selección](resultados/seleccion.png)

Al retener cuatro componentes en vez de dos, el error de reconstrucción (RMSE) bajó de **0,7218 a 0,3389** en validación y de **0,6731 a 0,3495** en prueba. La gráfica de selección muestra la varianza acumulada del ajuste, que pasó de **57,81 % a 88,23 %**. Cuatro fue el primer número de componentes que superó la meta del 80 %. [Métricas](resultados/evaluacion.json) · [Gráfica de selección](resultados/seleccion.png)

En el mapa de prueba, la proyección sobre CP1 y CP2 muestra puntos verdes y azules entremezclados en la zona central de la solución de tres grupos, con puntos verdes y naranjas próximos cerca de CP1 = 0. Con dos grupos, los centroides quedan a lados opuestos de CP1 = 0, donde todavía se ven puntos de ambos colores en la misma zona. El solapamiento persiste en la proyección pese a la mejora de la silueta. [Mapa de prueba](resultados/mapa_prueba.png)
