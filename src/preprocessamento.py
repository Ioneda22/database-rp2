"""
Pré-processamento da matriz de clusterização, em forma de função.

É o mesmo cálculo das células 3, 5 e 7 do notebook 03. Ele virou função
porque os testes de estabilidade e de sensibilidade precisam refazer a
matriz várias vezes (com outra janela de anos, sem os municípios pequenos ou
sem uma variável). Se cada notebook copiasse o código, uma diferença pequena
entre as cópias invalidaria a comparação.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from config import GRUPOS_NATUREZA, TAXA_POR_HABITANTES
from merge_bases import agregar_janela

ORDEM_BLOCOS = ["criminalidade", "socioeconomico", "gestao"]

# As duas colunas em R$ que recebem log1p junto com as taxas criminais.
COLUNAS_MONETARIAS = ["pib_percapita", "renda_domiciliar_mediana"]


def carregar_features(dic: pd.DataFrame) -> tuple[list[str], pd.Series]:
    """Recebe o dicionário da base e devolve as features (ordenadas por bloco
    e por nome, como no notebook 03) e a série coluna -> bloco."""
    bloco_de = dic.set_index("coluna")["bloco"]
    features = sorted(dic.loc[dic["papel"] == "feature", "coluna"],
                      key=lambda c: (ORDEM_BLOCOS.index(bloco_de[c]), c))
    return features, bloco_de


def exposicao_da_janela(cobertura: pd.DataFrame, anos: list[int]) -> float:
    """Recebe a cobertura da SSP e uma lista de anos e devolve a exposição:
    quantos anos completos foram observados (soma de meses / 12)."""
    # É a mesma conta do definir_janela() do merge_bases.py, mas recebendo os
    # anos como parâmetro, porque aquela função sempre lê a janela do config.
    meses = cobertura.set_index(cobertura["ano"].astype(int))["n_meses"]
    return sum(meses[a] / 12.0 for a in anos)


def taxas_da_janela(base: pd.DataFrame, painel: pd.DataFrame,
                    cobertura: pd.DataFrame, anos: list[int]) -> pd.DataFrame:
    """Devolve uma cópia de `base` com as taxas criminais (`taxa_<grupo>`)
    refeitas só com os `anos` pedidos. Usada nos testes de estabilidade com
    subjanelas; as outras colunas ficam como estão."""
    exposicao = exposicao_da_janela(cobertura, anos)

    contagens = agregar_janela(painel, anos)
    saida = base.copy()
    # O merge traz uma coluna de contagem por grupo (cvli, trafico...). Ela
    # só serve para calcular a taxa e é jogada fora logo depois.
    com_contagem = saida[["codigo_ibge"]].merge(contagens, on="codigo_ibge",
                                                how="left")
    pessoas_ano = saida["populacao"].to_numpy() * exposicao
    for grupo in GRUPOS_NATUREZA:
        # Município sem nenhuma ocorrência no grupo não aparece no painel;
        # fillna(0) faz a taxa dele valer 0, como no merge_bases.py.
        ocorrencias = com_contagem[grupo].fillna(0).to_numpy()
        saida[f"taxa_{grupo}"] = ocorrencias / pessoas_ano * TAXA_POR_HABITANTES
    return saida


def montar_matriz(df: pd.DataFrame, features: list[str], bloco_de: pd.Series
                  ) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    """Recebe os municípios já filtrados e devolve `(Z, W, peso)`: Z é a
    matriz com log1p e padronização, W é Z com o peso 1/√n de cada bloco, e
    peso é o peso de cada coluna. Linhas numeradas de 0 a n-1."""
    # Tiramos a numeração antiga das linhas para ela bater com a posição das
    # linhas nos rótulos que o scikit-learn devolve.
    X = df[features].reset_index(drop=True).astype(float)

    # log1p nas colunas de cauda longa: as taxas criminais e as colunas em R$
    # que estiverem na lista recebida.
    log_cols = [c for c in features
                if bloco_de[c] == "criminalidade" or c in COLUNAS_MONETARIAS]
    X[log_cols] = np.log1p(X[log_cols])

    # Padroniza cada coluna (média 0, desvio 1) com a média e o desvio
    # calculados só nos municípios recebidos. O StandardScaler trata cada
    # coluna separadamente, então dá o mesmo que o ColumnTransformer do
    # notebook 03.
    Z = pd.DataFrame(StandardScaler().fit_transform(X), columns=features)

    # O peso sai da lista recebida: se uma coluna for retirada de um bloco,
    # o bloco fica com uma coluna a menos e o peso muda junto.
    n_bloco = pd.Series([bloco_de[c] for c in features]).value_counts()
    peso = pd.Series({c: 1 / np.sqrt(n_bloco[bloco_de[c]]) for c in features})
    W = Z * peso
    return Z, W, peso


def orcamento(M: pd.DataFrame, bloco_de: pd.Series) -> pd.Series:
    """Recebe uma matriz (Z ou W) e devolve o % da variância total que cada
    bloco tem. É a mesma conta do notebook 03, sem arredondar, para servir de
    conferência do um terço por bloco."""
    # ddof=0 usa a fórmula populacional, que é a mesma do StandardScaler.
    var = M.var(ddof=0)
    por_bloco = var.groupby(M.columns.map(bloco_de)).sum()
    # reindex mantém a ordem dos blocos e tira os que não estão na matriz.
    por_bloco = por_bloco.reindex([b for b in ORDEM_BLOCOS if b in por_bloco])
    return por_bloco / var.sum() * 100


def escala_de_referencia(df: pd.DataFrame, features: list[str],
                         bloco_de: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Recebe os municípios de referência (os 644) e devolve a média e o
    desvio de cada feature depois do log1p, que são os números que o
    StandardScaler da montar_matriz usa. Serve para levar outro município
    (a capital) para a mesma escala sem mexer na dos 644."""
    X = _com_log(df[features].astype(float), bloco_de)
    # ddof=0: o StandardScaler divide por n, e não por n - 1.
    return X.mean(), X.std(ddof=0)


def transformar_com_escala(df: pd.DataFrame, features: list[str],
                           bloco_de: pd.Series, media: pd.Series,
                           desvio: pd.Series) -> pd.DataFrame:
    """Aplica o log1p e padroniza `df` com a média e o desvio recebidos (da
    escala_de_referencia). Devolve os valores em desvios em relação à média
    dos municípios de referência."""
    X = _com_log(df[features].astype(float), bloco_de)
    return (X - media[features]) / desvio[features]


def _com_log(X: pd.DataFrame, bloco_de: pd.Series) -> pd.DataFrame:
    """log1p nas mesmas colunas da montar_matriz (taxas criminais e R$)."""
    X = X.copy()
    log_cols = [c for c in X.columns
                if bloco_de[c] == "criminalidade" or c in COLUNAS_MONETARIAS]
    X[log_cols] = np.log1p(X[log_cols])
    return X


def estimador_bayesiano_global(y: np.ndarray, n: np.ndarray
                               ) -> tuple[np.ndarray, np.ndarray]:
    """Recebe as ocorrências `y` e as pessoas-ano `n` de cada município e
    devolve (taxa suavizada por pessoa-ano, C). É o estimador bayesiano
    empírico global de Marshall (1991), usado por Assunção et al. (1998)."""
    y = np.asarray(y, dtype=float)
    n = np.asarray(n, dtype=float)
    r = y / n                                   # taxa bruta
    m = y.sum() / n.sum()                       # taxa do conjunto todo
    # s² estima o quanto as taxas "verdadeiras" variam entre municípios: a
    # variação observada (ponderada pela população) menos a parte que é só
    # acaso, que é maior quanto menor o município.
    s2 = (n * (r - m) ** 2).sum() / n.sum() - m / n.mean()
    # Se o acaso explicar toda a variação, a conta dá negativa; aí não há
    # diferença real entre municípios e todos ficam com a taxa do conjunto.
    s2 = max(s2, 0.0)
    # C vai de 0 a 1 e diz quanto confiamos na taxa do próprio município:
    # perto de 1 em município grande (a taxa quase não muda), perto de 0 em
    # município pequeno (a taxa é puxada para a média).
    C = s2 / (s2 + m / n)
    return m + C * (r - m), C


def suavizar_taxas(base: pd.DataFrame, painel: pd.DataFrame,
                   cobertura: pd.DataFrame, anos: list[int]) -> pd.DataFrame:
    """Devolve uma cópia de `base` com as taxas criminais (`taxa_<grupo>`)
    trocadas pelas taxas suavizadas do estimador bayesiano empírico global
    (Marshall, 1991; Assunção et al., 1998), e uma coluna `c_<grupo>` com o C
    de cada município, que diz quanto da taxa bruta foi mantido."""
    # A taxa do conjunto (m) sai dos municípios recebidos: com os 644 da
    # modelagem, é a taxa do estado sem a capital.
    exposicao = exposicao_da_janela(cobertura, anos)
    contagens = agregar_janela(painel, anos)
    saida = base.copy()
    com_contagem = saida[["codigo_ibge"]].merge(contagens, on="codigo_ibge",
                                                how="left")
    pessoas_ano = saida["populacao"].to_numpy() * exposicao
    for grupo in GRUPOS_NATUREZA:
        # Mesmo fillna(0) da taxas_da_janela: sem ocorrência, a contagem é 0.
        ocorrencias = com_contagem[grupo].fillna(0).to_numpy()
        suavizada, C = estimador_bayesiano_global(ocorrencias, pessoas_ano)
        saida[f"taxa_{grupo}"] = suavizada * TAXA_POR_HABITANTES
        saida[f"c_{grupo}"] = C
    return saida
