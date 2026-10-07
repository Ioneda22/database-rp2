"""
Funções que desenham as figuras do artigo. Cada uma recebe os dados prontos
e devolve a figura; quem salva é estilo.salvar.

Deixamos os gráficos aqui para os notebooks ficarem só com a preparação dos
dados e a chamada da função.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.figure import Figure

from parse_ssp import normaliza

INICIO_JANELA = pd.Timestamp("2023-01-01")


# ---------------------------------------------------------------------------
# Fase 1 - janela temporal
# ---------------------------------------------------------------------------

def _serie_mensal(painel: pd.DataFrame, por: list[str]) -> pd.DataFrame:
    """Soma as ocorrências por mês (e por grupo, se pedido) e monta a data."""
    s = (painel[painel["mes"] > 0]
         .groupby(por + ["ano", "mes"])["ocorrencias"].sum().reset_index())
    s["data"] = pd.to_datetime(dict(year=s["ano"], month=s["mes"], day=1))
    return s.sort_values("data")


def plot_serie_mensal(painel: pd.DataFrame,
                      naturezas: dict[str, list[str]] | None = None) -> Figure:
    """
    Série mensal de ocorrências no estado, com uma linha em jan/2023.
    Serve para ver se a troca de sistema da SSP deixou um degrau na virada
    de 2022 para 2023. Sem `naturezas` mostra o total; com o dicionário
    GRUPOS_NATUREZA mostra um gráfico por grupo.
    """
    if naturezas is None:
        s = _serie_mensal(painel, [])
        fig, ax = plt.subplots(figsize=(8, 3.4))
        ax.plot(s["data"], s["ocorrencias"], color="C0")
        ax.axvline(INICIO_JANELA, color="C1", label="jan/2023: início da janela")
        # O eixo começa em zero de propósito. Se cortar o eixo, qualquer
        # oscilação parece um degrau.
        ax.set_ylim(0)
        ax.set_ylabel("ocorrências no mês")
        ax.set_title("Total mensal de ocorrências registradas em São Paulo")
        ax.legend(loc="lower left")
        fig.tight_layout()
        return fig

    mapa = {normaliza(nat): grupo
            for grupo, lista in naturezas.items() for nat in lista}
    bloco = painel.assign(grupo=painel["natureza"].map(mapa)).dropna(subset=["grupo"])
    s = _serie_mensal(bloco, ["grupo"])

    grupos = list(naturezas)
    linhas = int(np.ceil(len(grupos) / 2))
    fig, axes = plt.subplots(linhas, 2, figsize=(8.5, 1.8 * linhas), sharex=True)
    for ax, g in zip(axes.ravel(), grupos):
        sg = s[s["grupo"] == g]
        ax.plot(sg["data"], sg["ocorrencias"], color="C0", lw=1.4)
        ax.axvline(INICIO_JANELA, color="C1")
        ax.set_title(g)
        ax.set_ylim(0)
    fig.suptitle("Série mensal por natureza (a linha marca jan/2023)", y=1.0)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Fase 2 - exploratória
# ---------------------------------------------------------------------------

def plot_hist_populacao(populacao: pd.Series, limiar: int) -> Figure:
    """
    Histograma da população em escala log, com uma linha no limiar de
    município pequeno. Mostra quantos municípios têm menos de 5.000
    habitantes, onde uma ocorrência já distorce a taxa por 100 mil.
    """
    fig, ax = plt.subplots(figsize=(7, 3.2))
    bins = np.logspace(np.log10(populacao.min()), np.log10(populacao.max()), 40)
    ax.hist(populacao, bins=bins, color="C0")
    n_peq = int((populacao < limiar).sum())
    ax.axvline(limiar, color="C1",
               label=f"{limiar:,} hab.: {n_peq} municípios abaixo".replace(",", "."))
    ax.set_xscale("log")
    ax.set_xlabel("população (escala log)")
    ax.set_ylabel("municípios")
    ax.set_title("Distribuição da população dos municípios")
    ax.legend()
    fig.tight_layout()
    return fig


def plot_boxplot_taxas(df: pd.DataFrame, colunas: list[str]) -> Figure:
    """
    Boxplot das taxas criminais em escala log. Mostra que as taxas têm
    escalas bem diferentes e muitos valores extremos, por isso precisam de
    transformação antes de calcular distâncias.
    """
    longo = df[colunas].melt(var_name="taxa", value_name="valor")
    longo["taxa"] = longo["taxa"].str.replace("taxa_", "")
    fig, ax = plt.subplots(figsize=(8, 3.6))
    sns.boxplot(data=longo, x="taxa", y="valor", color="C0",
                fliersize=2, ax=ax)
    ax.set_yscale("log")   # os zeros não aparecem em escala log; ver % zeros na Tabela 2
    ax.set_xlabel("")
    ax.set_ylabel("por 100 mil hab./ano (log)")
    ax.set_title("Taxas criminais: escala e cauda longa")
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    return fig


def plot_distribuicoes_log1p(df: pd.DataFrame, colunas: list[str]) -> Figure:
    """
    Histograma de cada variável antes (esquerda) e depois (direita) do
    log1p, com a assimetria no título. Mostra por que a transformação é
    necessária e que o pico em zero (zero-inflação) continua depois dela.
    """
    fig, axes = plt.subplots(len(colunas), 2, figsize=(7, 1.4 * len(colunas)))
    for i, col in enumerate(colunas):
        bruta = df[col].dropna()
        for j, (serie, cor, nome) in enumerate([(bruta, "C0", "bruta"),
                                                (np.log1p(bruta), "C1", "log1p")]):
            ax = axes[i, j]
            ax.hist(serie, bins=40, color=cor)
            ax.set_title(f"{col.replace('taxa_', '')} - {nome} "
                         f"(assimetria {serie.skew():+.2f})", fontsize=8)
            ax.set_yticks([])
    fig.tight_layout()
    return fig


def plot_spearman(rho: pd.DataFrame, bloco_de: pd.Series,
                  ordem_blocos: list[str]) -> Figure:
    """
    Mapa de calor da correlação de Spearman (só o triângulo de baixo), com
    linhas separando os blocos. Serve para ver se há pares redundantes e se
    os blocos medem coisas diferentes. Só |rho| >= 0,5 recebe o número.
    """
    rotulos = [c.replace("taxa_", "").replace("_ord", "") for c in rho.columns]
    mascara = np.triu(np.ones_like(rho, dtype=bool))
    texto = rho.round(2).astype(str).where(rho.abs() >= 0.5, "")

    fig, ax = plt.subplots(figsize=(9, 8))
    sns.heatmap(rho, mask=mascara, annot=texto, fmt="", cmap="RdBu",
                vmin=-1, vmax=1, square=True, annot_kws={"size": 7},
                xticklabels=rotulos, yticklabels=rotulos,
                cbar_kws={"shrink": 0.6, "label": "rho de Spearman"}, ax=ax)

    # Linhas entre os blocos (as features já vêm ordenadas por bloco).
    corte = 0
    for b in ordem_blocos[:-1]:
        corte += sum(1 for c in rho.columns if bloco_de[c] == b)
        ax.axhline(corte, color="gray", lw=1)
        ax.axvline(corte, color="gray", lw=1)
    ax.set_title(f"Correlação de Spearman entre as {len(rho)} features")
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Fase 3 - pré-processamento
# ---------------------------------------------------------------------------

def plot_orcamento_blocos(sem_peso: pd.Series, com_peso: pd.Series) -> Figure:
    """
    Quanto da variância total cada bloco tem, antes e depois do peso 1/√n.
    Mostra que sem o peso o bloco com mais colunas domina, e que com o peso
    os três ficam com 1/3 cada.
    """
    tabela = pd.DataFrame({"sem peso": sem_peso, "com peso 1/√n": com_peso})
    fig, ax = plt.subplots(figsize=(7, 3.4))
    tabela.plot.bar(ax=ax, color=["C0", "C1"], rot=0)
    for barras in ax.containers:
        ax.bar_label(barras, fmt="%.1f%%", fontsize=8)
    ax.axhline(100 / len(tabela), color="gray", ls="--",
               label=f"paridade: {100 / len(tabela):.1f}%")
    ax.set_ylabel("% da variância total")
    ax.set_ylim(0, max(tabela.max()) * 1.2)
    ax.set_title("Participação de cada bloco na distância")
    ax.legend()
    fig.tight_layout()
    return fig


def plot_variancia_pca(explained_variance_ratio: np.ndarray) -> Figure:
    """
    Variância explicada por componente (barras) e acumulada (linha), com a
    marca de 80%. Mostra quantas componentes são necessárias.
    """
    ev = np.asarray(explained_variance_ratio) * 100
    acumulada = np.cumsum(ev)
    comps = np.arange(1, len(ev) + 1)
    k80 = int(np.argmax(acumulada >= 80)) + 1

    fig, ax = plt.subplots(figsize=(7, 3.6))
    ax.bar(comps, ev, color="lightgray", label="por componente")
    ax.plot(comps, acumulada, color="C0", marker="o", ms=4, label="acumulada")
    ax.axhline(80, color="C1", ls="--", label=f"80% com {k80} componentes")
    ax.set_xticks(comps)
    ax.set_xlabel("componente principal")
    ax.set_ylabel("% da variância")
    ax.set_ylim(0, 102)
    ax.set_title("Variância explicada pelo PCA")
    ax.legend(loc="center right")
    fig.tight_layout()
    return fig


def plot_pc1_pc2(escores: np.ndarray, cor: pd.Series, rotulo_cor: str,
                 variancia: np.ndarray | None = None) -> Figure:
    """
    Municípios nas duas primeiras componentes, coloridos por uma variável.
    Serve para ver se há grupos separados ou uma nuvem contínua.
    """
    fig, ax = plt.subplots(figsize=(6.4, 5))
    pontos = ax.scatter(escores[:, 0], escores[:, 1], c=cor, cmap="Blues",
                        s=16, edgecolor="gray", linewidth=0.3)
    fig.colorbar(pontos, ax=ax, shrink=0.75, label=rotulo_cor)
    pct = ["", ""] if variancia is None else [f" ({v * 100:.1f}%)" for v in variancia[:2]]
    ax.set_xlabel("PC1" + pct[0])
    ax.set_ylabel("PC2" + pct[1])
    ax.set_title(f"Os {len(escores)} municípios nas duas primeiras componentes")
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Fase 4 - clusterização
# ---------------------------------------------------------------------------

def plot_selecao_k(metricas: pd.DataFrame) -> Figure:
    """
    Mostra as quatro medidas de qualidade do K-means e do Ward para cada k.
    Serve para comparar os dois algoritmos e ver quais k se destacam.
    """
    paineis = [
        ("soma_quadrados", "(a) soma dos quadrados interna\n(cotovelo; menor é melhor)"),
        ("silhueta", "(b) silhueta\n(maior é melhor)"),
        ("calinski_harabasz", "(c) Calinski–Harabasz\n(maior é melhor)"),
        ("davies_bouldin", "(d) Davies–Bouldin\n(menor é melhor)"),
    ]
    # Marcador e tipo de linha diferentes para ler em preto e branco.
    estilos = {"kmeans": dict(color="C0", marker="o", ls="-", label="K-means"),
               "ward": dict(color="C1", marker="s", ls="--", label="Ward")}

    fig, axes = plt.subplots(2, 2, figsize=(7, 5), sharex=True)
    for ax, (coluna, titulo) in zip(axes.ravel(), paineis):
        for algoritmo, estilo in estilos.items():
            m = metricas[metricas["algoritmo"] == algoritmo]
            ax.plot(m["k"], m[coluna], ms=4, **estilo)
        ax.set_title(titulo, fontsize=9)
        ax.set_xticks(sorted(metricas["k"].unique()))
    for ax in axes[1]:
        ax.set_xlabel("número de grupos (k)")
    axes[0, 1].legend()
    fig.tight_layout()
    return fig


def plot_k_distancia(distancias: dict[int, np.ndarray],
                     eps_testados: dict[int, list[float]]) -> Figure:
    """
    Mostra a distância de cada município ao seu min_pts-ésimo vizinho, em
    ordem, com os raios (eps) testados no DBSCAN. Serve para ver se a curva
    tem um "joelho": sem joelho, não há uma separação natural entre regiões
    densas e ruído.
    """
    fig, axes = plt.subplots(1, len(distancias), figsize=(7, 3), sharey=True,
                             squeeze=False)
    for ax, (min_pts, curva) in zip(axes[0], distancias.items()):
        ax.plot(np.arange(1, len(curva) + 1), curva, color="C0")
        for eps in eps_testados[min_pts]:
            ax.axhline(eps, color="gray", ls=":", lw=0.8)
        ax.set_title(f"min_pts = {min_pts}")
        ax.set_xlabel("municípios, em ordem")
    axes[0, 0].set_ylabel("distância ao min_pts-ésimo vizinho")
    fig.suptitle("Curva de k-distância (pontilhado: eps testados)", y=1.0)
    fig.tight_layout()
    return fig


def plot_dendrograma(W) -> Figure:
    """
    Mostra a árvore do Ward: cada junção de dois grupos, na altura do custo
    da fusão. Serve para ver em que pontos cortar a árvore separa grupos bem
    distintos (saltos grandes de altura) e onde só divide uma nuvem contínua.
    """
    from scipy.cluster.hierarchy import dendrogram, linkage

    arvore = linkage(np.asarray(W), method="ward")
    fig, ax = plt.subplots(figsize=(7, 3.6))
    # truncate_mode="lastp" mostra só as 30 últimas junções; o número entre
    # parênteses embaixo é quantos municípios cada ramo tem.
    dendrogram(arvore, truncate_mode="lastp", p=30, ax=ax,
               color_threshold=0, above_threshold_color="C0",
               leaf_font_size=7)
    ax.set_ylabel("custo da fusão")
    ax.set_xlabel("ramos (entre parênteses: número de municípios)")
    ax.set_title("Dendrograma do Ward (últimas 30 junções)")
    ax.grid(axis="x", visible=False)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Fase 5 - perfis
# ---------------------------------------------------------------------------

def plot_perfis(medias: pd.DataFrame, bloco_de: pd.Series,
                ordem_blocos: list[str], rotulos_perfis: list[str]) -> Figure:
    """
    Mostra, para cada perfil (coluna), em que features (linhas) ele fica
    acima ou abaixo da média dos 644 municípios. Serve para dar nome aos
    perfis; é a Figura 5.
    """
    rotulos = [c.replace("taxa_", "").replace("_ord", "") for c in medias.index]
    fig, ax = plt.subplots(figsize=(6, 8))
    # vmin/vmax em ±1,5: médias além disso ficam na cor mais forte. Assim um
    # perfil muito extremo em uma variável não deixa as outras células quase
    # brancas. O número escrito na célula continua sendo o valor real.
    # Arredondar um valor como -0,03 dá "-0.0"; somar 0.0 tira o sinal do zero.
    texto = medias.round(1) + 0.0
    sns.heatmap(medias, cmap="RdBu", vmin=-1.5, vmax=1.5, center=0,
                annot=texto, fmt=".1f", annot_kws={"size": 8},
                xticklabels=rotulos_perfis, yticklabels=rotulos,
                cbar_kws={"shrink": 0.6,
                          "label": "desvios em relação à média dos 644 municípios"},
                ax=ax)

    # Linhas entre os blocos (as features já vêm ordenadas por bloco).
    corte = 0
    for b in ordem_blocos[:-1]:
        corte += sum(1 for c in medias.index if bloco_de[c] == b)
        ax.axhline(corte, color="gray", lw=1)
    ax.set_xlabel("")
    ax.tick_params(axis="x", rotation=0)
    ax.set_title("Média padronizada de cada feature por perfil")
    fig.tight_layout()
    return fig


def plot_boxplot_perfis(valores: pd.Series, perfil: pd.Series, rotulo: str,
                        rotulos_perfis: list[str]) -> Figure:
    """
    Mostra a distribuição de uma variável em cada perfil (uma caixa por
    perfil). Serve para ver a diferença que o epsilon² do Kruskal-Wallis
    resume em um número.
    """
    # Mesmos tons de azul do mapa, do perfil 1 (claro) ao último (escuro).
    cores = plt.get_cmap("Blues")(np.linspace(0.2, 0.95, len(rotulos_perfis)))
    fig, ax = plt.subplots(figsize=(6, 3.6))
    sns.boxplot(x=perfil.to_numpy(), y=valores.to_numpy(), hue=perfil.to_numpy(),
                palette=list(cores), legend=False, fliersize=2, ax=ax)
    ax.set_xticks(range(len(rotulos_perfis)), rotulos_perfis)
    ax.set_xlabel("")
    ax.set_ylabel(rotulo)
    ax.set_title(f"{rotulo[0].upper()}{rotulo[1:]} por perfil")
    fig.tight_layout()
    return fig


def plot_mapa_categorias(gdf, coluna: str, rotulos: dict, titulo: str) -> Figure:
    """
    Mostra os municípios no mapa, pintados pela categoria de `coluna` (do
    primeiro item de `rotulos`, mais claro, ao último, mais escuro).
    Serve para ver se os perfis têm uma geografia; com os perfis, é a Figura 6.
    """
    from matplotlib.patches import Patch

    # Cortamos as pontas da escala Blues: o começo é quase branco e se
    # confundiria com o fundo e com o cinza dos municípios sem categoria.
    cores = plt.get_cmap("Blues")(np.linspace(0.2, 0.95, len(rotulos)))
    fig, ax = plt.subplots(figsize=(7, 5.2))
    legenda = []
    for cor, (valor, rotulo) in zip(cores, rotulos.items()):
        gdf[gdf[coluna] == valor].plot(ax=ax, color=cor, edgecolor="gray",
                                       linewidth=0.15)
        legenda.append(Patch(facecolor=cor, edgecolor="gray", label=rotulo))

    # Quem ficou sem categoria (a capital, que não tem IEGM) leva hachura,
    # para não ser confundido com o perfil mais claro quando impresso em cinza.
    sem = gdf[gdf[coluna].isna()]
    if len(sem):
        sem.plot(ax=ax, color="whitesmoke", edgecolor="gray", hatch="//////",
                 linewidth=0.15)
        legenda.append(Patch(facecolor="whitesmoke", edgecolor="gray",
                             hatch="//////", label="sem perfil (sem IEGM)"))

    ax.set_axis_off()
    ax.set_title(titulo)
    # O canto de baixo à direita é mar, por isso a legenda fica ali.
    ax.legend(handles=legenda, loc="lower right", fontsize=8, frameon=True)
    fig.tight_layout()
    return fig
