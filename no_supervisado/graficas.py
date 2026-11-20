"""Figuras comparables para la selección y la evaluación de los modelos."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.edgecolor": "#a1b0aa", "axes.titleweight": "bold",
    "text.color": "#202624", "axes.labelcolor": "#202624",
})
VERDE = "#075948"
AZUL = "#2d669b"
ARCILLA = "#a75123"
CLARO = "#dce7e3"


def seleccion(informe, destino):
    kmeans, pca = informe["kmeans"], informe["pca"]
    fig, (grupos, componentes) = plt.subplots(1, 2, figsize=(7.1, 2.7), layout="constrained")
    ks = [c["k"] for c in kmeans["candidatos"]]
    siluetas = [c["validacion"]["silueta"] for c in kmeans["candidatos"]]
    grupos.plot(ks, siluetas, marker="o", color=VERDE)
    grupos.set(title="Silueta en validación", xlabel="Número de grupos", xticks=ks)
    grupos.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:.2f}".replace(".", ",")))
    grupos.grid(axis="y", alpha=.2)

    ds = [c["componentes"] for c in pca["candidatos"]]
    porcentajes = [100 * c["varianza_ajuste"] for c in pca["candidatos"]]
    componentes.bar(ds, porcentajes, color=CLARO, width=.64)
    for etapa, color in [("inicial", ARCILLA), ("optimizado", AZUL)]:
        k = kmeans[etapa]["k"]
        d = pca[etapa]["componentes"]
        grupos.scatter(k, siluetas[k - ks[0]], s=65, c=color, edgecolors="white",
                       zorder=5, label=etapa.capitalize())
        componentes.bar(d, porcentajes[d - 1], color=color, width=.64)
    grupos.legend(loc="best", frameon=False, fontsize=8)
    componentes.axhline(100 * pca["meta_varianza"], linestyle="--", color=VERDE,
                        linewidth=1, label="Meta del 80 %")
    componentes.set(title="Varianza acumulada del ajuste", ylabel="Varianza (%)",
                    xlabel="Componentes retenidas", xticks=ds, ylim=(0, 105))
    componentes.legend(loc="lower right", frameon=False, fontsize=8)
    componentes.grid(axis="y", alpha=.2)
    componentes.set_axisbelow(True)
    fig.savefig(destino, dpi=260)
    plt.close(fig)


def mapa_prueba(informe, asignaciones, destino):
    fig, axes = plt.subplots(1, 2, figsize=(7.1, 3.15), sharex=True, sharey=True,
                             layout="constrained")
    varianza = informe["pca"]["varianza_por_componente"]
    paleta = [VERDE, AZUL, ARCILLA, "#61559b", "#906d20", "#307779"]
    for ax, etapa in zip(axes, ("inicial", "optimizado")):
        config = informe["kmeans"][etapa]
        for grupo in config["grupos"]:
            id_grupo = grupo["grupo"]
            color = paleta[id_grupo - 1]
            x = asignaciones.loc[asignaciones[f"grupo_{etapa}"].eq(id_grupo)]
            ax.scatter(x["cp1"], x["cp2"], s=13, color=color, alpha=.68, linewidths=0,
                       label=f"G{id_grupo} · {len(x)}")
            cx, cy = grupo["centroide_pca"]
            ax.scatter(cx, cy, marker="X", s=72, color=color, edgecolors="white",
                       linewidths=.8, zorder=5)
        ax.axhline(0, color=CLARO, linewidth=.8)
        ax.axvline(0, color=CLARO, linewidth=.8)
        ax.set(title=f"{etapa.capitalize()} · k = {config['k']}",
               xlabel=f"CP 1 ({varianza[0]:.1%})".replace(".", ","))
        ax.legend(loc="upper left", frameon=False, fontsize=8)
    axes[0].set_ylabel(f"CP 2 ({varianza[1]:.1%})".replace(".", ","))
    fig.savefig(destino, dpi=260)
    plt.close(fig)
