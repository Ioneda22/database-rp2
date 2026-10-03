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


def taxas_da_janela(base: pd.DataFrame, painel: pd.DataFrame,
                    cobertura: pd.DataFrame, anos: list[int]) -> pd.DataFrame:
    """Devolve uma cópia de `base` com as taxas criminais (`taxa_<grupo>`)
    refeitas só com os `anos` pedidos. Usada nos testes de estabilidade com
    subjanelas; as outras colunas ficam como estão."""
    # Exposição = quantos anos completos foram observados. É a mesma conta do
    # definir_janela() do merge_bases.py, mas recebendo os anos como
    # parâmetro, porque aquela função sempre lê a janela do config.py.
    meses = cobertura.set_index(cobertura["ano"].astype(int))["n_meses"]
    exposicao = sum(meses[a] / 12.0 for a in anos)

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
