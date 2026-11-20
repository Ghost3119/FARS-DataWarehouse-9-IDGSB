"""Figuras de la evaluación para el informe y el repositorio."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np

from .modelos import BOSQUE, ESTACIONAL, LOGISTICA, MAYORIA

VERDE = "#075948"
AZUL = "#28639a"
GRIS = "#50605b"


def decimal(valor, cifras):
    return f"{valor:.{cifras}f}".replace(".", ",")


def grafica_clasificacion(informe, curvas, salida):
    modelos = informe["modelos"]
    elegido = informe["elegido_en_2023"]
    matriz = np.array(modelos[elegido]["test"]["matriz"])
    fig, (pr, cm) = plt.subplots(
        1, 2, figsize=(7.2, 3.13), width_ratios=(1.45, 1), layout="constrained"
    )
    for nombre, color, estilo in [(LOGISTICA, AZUL, "-"), (BOSQUE, VERDE, "--")]:
        precision, recall = curvas[nombre]
        ap = decimal(modelos[nombre]["test"]["ap"], 3)
        pr.step(recall, precision, where="post", color=color, linestyle=estilo,
                linewidth=1.4, label=f"{nombre} ({ap})")
    prevalencia = modelos[MAYORIA]["test"]["ap"]
    pr.axhline(prevalencia, color=GRIS, linestyle=":", label=f"Prevalencia ({decimal(prevalencia, 3)})")
    pr.set(xlim=(0, 1), ylim=(0, 1.02), xlabel="Recall", ylabel="Precision",
           title="Curvas de clasificación")
    formato = FuncFormatter(lambda x, _: decimal(x, 1))
    pr.xaxis.set_major_formatter(formato)
    pr.yaxis.set_major_formatter(formato)
    pr.grid(alpha=0.18)
    pr.legend(fontsize=7.5, loc="upper right", frameon=False)

    # Se colorea por proporción de cada clase real y se rotula con su conteo.
    proporcion = matriz / matriz.sum(axis=1, keepdims=True)
    cm.imshow(proporcion, cmap="Greens", vmin=0, vmax=1)
    for (fila, col), n in np.ndenumerate(matriz):
        cm.text(col, fila, f"{n:,}".replace(",", " "), ha="center", va="center",
                color="white" if proporcion[fila, col] >= .65 else "#17221e",
                fontweight="bold")
    clases = ["1 muerte", "2+ muertes"]
    cm.set_xticks([0, 1], clases, fontsize=8)
    cm.set_yticks([0, 1], clases, fontsize=8)
    cm.set(title=elegido, xlabel="Clase predicha", ylabel="Clase real")
    cm.tick_params(length=0)
    fig.savefig(salida, dpi=270)
    plt.close(fig)


def grafica_regresion(informe, salida):
    fig, ax = plt.subplots(figsize=(7.2, 2.45), layout="constrained")
    modelos = informe["modelos"]
    nombres = list(modelos)
    ys = np.arange(len(nombres))
    for i, (periodo, valores, color) in enumerate([
        ("Validación 2023", [m["seleccion"]["validacion"] for m in modelos.values()], "#5786a8"),
        ("Prueba 2024", [m["test"]["mae"] for m in modelos.values()], VERDE),
    ]):
        barras = ax.barh(ys + (i - .5) * .32, valores, height=.29, color=color, label=periodo)
        ax.bar_label(barras, labels=[decimal(v, 2) for v in valores], padding=4, fontsize=8.5)
    ax.set_yticks(ys, ["Referencia estacional" if m == ESTACIONAL else m for m in nombres])
    ax.invert_yaxis()
    ax.set(xlabel="MAE · muertes por estado y mes", xlim=(0, 12))
    ax.grid(axis="x", alpha=.2)
    ax.set_axisbelow(True)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.legend(loc="upper center", bbox_to_anchor=(.5, 1.18), ncols=2, frameon=False, fontsize=8.5)
    fig.savefig(salida, dpi=270)
    plt.close(fig)
