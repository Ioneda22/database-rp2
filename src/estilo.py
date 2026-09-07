"""
Estilo comum das figuras do artigo.

Duas restrições mandam aqui, e as duas vêm da entrega:

1. **O artigo é impresso.** A checklist da Fase 8 exige figuras legíveis em
   escala de cinza. Por isso nenhuma figura usa cor como único canal de
   informação: comparações vão em painéis lado a lado (a posição distingue),
   e no mapa de calor os valores que importam vêm rotulados.

2. **Paleta validada, não escolhida a olho.** Os hexadecimais abaixo passaram
   nos testes de separação para daltonismo e de contraste contra o fundo
   (ΔE protan 24,7 e normal 33,6 para o par azul/laranja, mínimo exigido 8 e
   15). Se trocarem alguma cor, revalidem -- não confiem no olho.

A divergente é azul <-> cinza <-> vermelho: dois polos que leem como opostos,
com neutro no meio. Nunca arco-íris, e nunca uma cor no ponto médio -- uma
correlação de zero tem que parecer "nada", não "alguma coisa".
"""
from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
from matplotlib.colors import LinearSegmentedColormap

BASE_DIR = Path(__file__).resolve().parent.parent
FIGURAS_DIR = BASE_DIR / "figuras"

# --- Paleta -------------------------------------------------------------
AZUL = "#2a78d6"        # série 1
LARANJA = "#eb6834"     # série 2
VERMELHO = "#e34948"    # polo quente da divergente

SUPERFICIE = "#fcfcfb"
TINTA = "#0b0b0b"       # primária
TINTA_2 = "#52514e"     # secundária
MUDO = "#898781"        # eixos e rótulos
GRADE = "#e1e0d9"
NEUTRO = "#f0efec"      # ponto médio da divergente

CMAP_DIVERGENTE = LinearSegmentedColormap.from_list(
    "rp2_div", [AZUL, NEUTRO, VERMELHO], N=256,
)


def aplicar_estilo() -> None:
    """Ajusta o matplotlib. Chame uma vez no topo do notebook."""
    mpl.rcParams.update({
        "figure.facecolor": SUPERFICIE,
        "axes.facecolor": SUPERFICIE,
        "savefig.facecolor": SUPERFICIE,
        "savefig.dpi": 200,
        "savefig.bbox": "tight",
        "figure.dpi": 110,

        "font.family": "sans-serif",
        "font.sans-serif": ["Segoe UI", "DejaVu Sans", "Arial"],
        "font.size": 9,
        "axes.titlesize": 10,
        "axes.titleweight": "semibold",
        "axes.labelsize": 9,

        "text.color": TINTA,
        "axes.labelcolor": TINTA_2,
        "xtick.color": MUDO,
        "ytick.color": MUDO,
        "xtick.labelcolor": TINTA_2,
        "ytick.labelcolor": TINTA_2,

        # Eixos e grade recuam: o dado é que tem que aparecer.
        "axes.edgecolor": GRADE,
        "axes.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "grid.color": GRADE,
        "grid.linewidth": 0.6,
        "axes.grid": True,
        "axes.grid.axis": "y",

        "lines.linewidth": 2.0,
        "lines.markersize": 5,
        "legend.frameon": False,
        "legend.fontsize": 8,
    })


def salvar(fig, nome: str) -> Path:
    """Grava a figura em figuras/<nome>.png e devolve o caminho."""
    FIGURAS_DIR.mkdir(parents=True, exist_ok=True)
    caminho = FIGURAS_DIR / f"{nome}.png"
    fig.savefig(caminho)
    print(f"-> {caminho.relative_to(BASE_DIR)}")
    return caminho
