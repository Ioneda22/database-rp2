"""
Agrupamento dos municípios e as medidas de qualidade de cada partição.

Usado pelo notebook 04 (que mede) e pelos notebooks seguintes (que testam a
estabilidade e caracterizam os perfis). Partição = a divisão dos municípios
em grupos; rótulos = o número do grupo de cada município.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN, AgglomerativeClustering, KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import (adjusted_rand_score, calinski_harabasz_score,
                             davies_bouldin_score, silhouette_score)
from sklearn.neighbors import NearestNeighbors

from config import K_MAX, K_MIN, N_INIT, N_SEMENTES, RANDOM_STATE
from preprocessamento import montar_matriz, taxas_da_janela

ALGORITMOS_K = ["kmeans", "ward"]


def agrupar(W, algoritmo: str, k: int) -> np.ndarray:
    """Recebe a matriz, o algoritmo ("kmeans" ou "ward") e o número de grupos
    k, e devolve os rótulos de cada município."""
    X = np.asarray(W)
    if algoritmo == "kmeans":
        # n_init=N_INIT: o K-means começa sorteando os centros, e sorteios
        # diferentes podem dar grupos diferentes. Rodamos várias vezes e
        # ficamos com a melhor.
        modelo = KMeans(n_clusters=k, n_init=N_INIT, random_state=RANDOM_STATE)
    elif algoritmo == "ward":
        # O Ward não sorteia nada: com os mesmos dados, sempre dá o mesmo
        # resultado.
        modelo = AgglomerativeClustering(n_clusters=k, linkage="ward")
    else:
        raise ValueError(f"algoritmo desconhecido: {algoritmo}")
    return modelo.fit_predict(X)


def soma_quadrados_interna(W, rotulos: np.ndarray) -> float:
    """Soma das distâncias ao quadrado de cada município até a média do seu
    grupo. No K-means é a própria inércia; calculada à mão, vale também para
    o Ward, e as duas curvas ficam comparáveis."""
    X = np.asarray(W)
    total = 0.0
    for g in np.unique(rotulos):
        membros = X[rotulos == g]
        total += ((membros - membros.mean(axis=0)) ** 2).sum()
    return float(total)


def metricas_por_k(W) -> pd.DataFrame:
    """Roda K-means e Ward para cada k de K_MIN a K_MAX e devolve uma linha
    por partição com as medidas de qualidade e o tamanho do menor e do maior
    grupo (em municípios)."""
    X = np.asarray(W)
    linhas = []
    for algoritmo in ALGORITMOS_K:
        for k in range(K_MIN, K_MAX + 1):
            rotulos = agrupar(X, algoritmo, k)
            # bincount conta quantos municípios recebeu cada rótulo.
            tamanhos = np.bincount(rotulos)
            linhas.append({
                "algoritmo": algoritmo,
                "k": k,
                "soma_quadrados": soma_quadrados_interna(X, rotulos),
                "silhueta": silhouette_score(X, rotulos),
                "calinski_harabasz": calinski_harabasz_score(X, rotulos),
                "davies_bouldin": davies_bouldin_score(X, rotulos),
                "menor_grupo": int(tamanhos.min()),
                "maior_grupo": int(tamanhos.max()),
            })
    return pd.DataFrame(linhas)


def componentes_pca(W, variancia: float) -> np.ndarray:
    """Devolve a posição de cada município nas primeiras componentes do PCA,
    tantas quantas forem precisas para somar `variancia` da variação (mesma
    conta do notebook 03). É a entrada do DBSCAN."""
    X = np.asarray(W)
    pca = PCA().fit(X)
    # Mesma regra do notebook 03: a primeira componente em que a soma
    # acumulada chega a `variancia`. O + 1 é porque a contagem começa em zero.
    n = int(np.argmax(np.cumsum(pca.explained_variance_ratio_) >= variancia)) + 1
    return pca.transform(X)[:, :n]


def distancia_k_vizinho(X, min_pts: int) -> np.ndarray:
    """Distância de cada município ao seu `min_pts`-ésimo vizinho mais
    próximo, em ordem crescente. É a curva usada para escolher o raio (eps)
    do DBSCAN."""
    # O próprio ponto conta como o primeiro vizinho (distância zero). É a
    # mesma conta que o DBSCAN do scikit-learn faz com min_samples: o ponto
    # entra na contagem dos vizinhos dele mesmo.
    vizinhos = NearestNeighbors(n_neighbors=min_pts).fit(X)
    distancias, _ = vizinhos.kneighbors(X)
    # A última coluna é a distância ao vizinho mais distante dos min_pts.
    return np.sort(distancias[:, -1])


def grade_dbscan(X, min_pts_lista: list[int], quantis: list[float]
                 ) -> pd.DataFrame:
    """Testa o DBSCAN com cada `min_pts` e com raios (eps) tirados dos
    `quantis` da curva de k-distância. Devolve uma linha por combinação, com
    o número de grupos, o % de ruído, o % do maior grupo e a silhueta."""
    X = np.asarray(X)
    linhas = []
    for min_pts in min_pts_lista:
        curva = distancia_k_vizinho(X, min_pts)
        for q in quantis:
            eps = float(np.quantile(curva, q))
            rotulos = DBSCAN(eps=eps, min_samples=min_pts).fit_predict(X)
            # O DBSCAN marca o ruído (município isolado, sem grupo) com -1.
            ruido = rotulos == -1
            n_grupos = len(set(rotulos[~ruido]))
            maior = np.bincount(rotulos[~ruido]).max() if n_grupos else 0
            # A silhueta só faz sentido com pelo menos 2 grupos, e o ruído
            # fica de fora porque não é um grupo.
            silhueta = (silhouette_score(X[~ruido], rotulos[~ruido])
                        if n_grupos >= 2 else np.nan)
            linhas.append({
                "min_pts": min_pts,
                "quantil": q,
                "eps": eps,
                "n_grupos": n_grupos,
                "pct_ruido": 100 * ruido.mean(),
                "maior_grupo_pct": 100 * maior / len(X),
                "silhueta": silhueta,
            })
    return pd.DataFrame(linhas)


# ---------------------------------------------------------------------------
# Estabilidade (notebook 05)
# ---------------------------------------------------------------------------
# Todas as funções abaixo comparam duas partições pelo ARI (índice de Rand
# ajustado). O ARI não depende do número que cada grupo recebe: o "grupo 0"
# de uma partição pode ser o "grupo 2" da outra. Ele só olha quem está junto
# com quem. Vale 1 quando as duas partições são iguais e fica perto de 0
# quando elas concordam tanto quanto um sorteio.

def ari_sementes(W, k: int, n: int = N_SEMENTES) -> tuple[float, float]:
    """Compara o K-means de referência (melhor de N_INIT sorteios) com `n`
    K-means de um sorteio só, cada um com uma semente diferente, e devolve a
    média e o mínimo do ARI. Mede o quanto o resultado depende do sorteio."""
    # Só faz sentido para o K-means: o Ward não sorteia nada e sempre dá o
    # mesmo resultado com os mesmos dados.
    X = np.asarray(W)
    referencia = agrupar(X, "kmeans", k)
    aris = [adjusted_rand_score(
                referencia,
                KMeans(n_clusters=k, n_init=1, random_state=s).fit_predict(X))
            for s in range(n)]
    return float(np.mean(aris)), float(np.min(aris))


def matriz_subjanela(base_mod: pd.DataFrame, painel: pd.DataFrame,
                     cobertura: pd.DataFrame, features: list[str],
                     bloco_de: pd.Series, anos: list[int]) -> pd.DataFrame:
    """Refaz a matriz ponderada W com as taxas criminais calculadas só com
    os `anos` pedidos. Montada uma vez por subjanela e reaproveitada para
    todos os candidatos."""
    _, W_sub, _ = montar_matriz(
        taxas_da_janela(base_mod, painel, cobertura, anos), features, bloco_de)
    return W_sub


def ari_subjanela(W_sub: pd.DataFrame, algoritmo: str, k: int,
                  rotulos_ref: np.ndarray) -> float:
    """Agrupa a matriz de uma subjanela (vinda de `matriz_subjanela`) e
    devolve o ARI contra os rótulos da janela completa."""
    # Os municípios estão na mesma ordem nas duas matrizes, então dá para
    # comparar os rótulos posição a posição.
    return float(adjusted_rand_score(rotulos_ref, agrupar(W_sub, algoritmo, k)))


def ari_sem_pequenos(base_mod: pd.DataFrame, features: list[str],
                     bloco_de: pd.Series, algoritmo: str, k: int,
                     rotulos_ref: np.ndarray) -> float:
    """Tira os municípios com menos de 5.000 habitantes, refaz a matriz só
    com os que sobraram, agrupa e devolve o ARI contra a partição completa
    restrita a esses mesmos municípios."""
    ficam = ~base_mod["flag_pop_pequena"].to_numpy()
    # A padronização é refeita só com quem ficou, como se os municípios
    # pequenos nunca tivessem existido.
    _, W_grandes, _ = montar_matriz(base_mod[ficam], features, bloco_de)
    return float(adjusted_rand_score(rotulos_ref[ficam],
                                     agrupar(W_grandes, algoritmo, k)))


def marcar_qualidade(tabela: pd.DataFrame, n: int) -> pd.Series:
    """Passo 3 da regra: recebe as partições que passaram no filtro de
    tamanho e devolve verdadeiro/falso para cada uma, marcando os k que
    estão entre os `n` melhores em silhueta e em Calinski-Harabasz dentro do
    seu algoritmo (ou só em silhueta, se nenhum k cumprir as duas)."""
    marca = pd.Series(False, index=tabela.index)
    for _, t in tabela.groupby("algoritmo"):
        # nlargest(n, coluna) pega as n linhas com os maiores valores.
        top_silhueta = set(t.nlargest(n, "silhueta").index)
        top_calinski = set(t.nlargest(n, "calinski_harabasz").index)
        ficam = (top_silhueta & top_calinski) or top_silhueta
        marca[list(ficam)] = True
    return marca


def renumerar_por_socioeconomico(rotulos: np.ndarray, Z: pd.DataFrame,
                                 colunas_socio: list[str]) -> np.ndarray:
    """Renumera os grupos de 1 a k em ordem crescente da média das variáveis
    socioeconômicas padronizadas: o perfil 1 é o de menor condição
    socioeconômica."""
    # A numeração que o scikit-learn dá aos grupos é arbitrária e muda de uma
    # execução para outra. Ordenando por um critério fixo, "perfil 1" quer
    # dizer sempre a mesma coisa.
    media_socio = Z[colunas_socio].mean(axis=1).groupby(rotulos).mean()
    # rank() dá a posição de cada grupo nessa ordem (1 = menor média).
    nova_ordem = media_socio.rank(method="first").astype(int)
    return nova_ordem.loc[rotulos].to_numpy()


def distancia_ao_centro(W, rotulos: np.ndarray) -> np.ndarray:
    """Distância de cada município até a média do seu grupo, na matriz W.
    Serve para achar os municípios mais típicos de cada perfil."""
    X = np.asarray(W)
    centros = pd.DataFrame(X).groupby(rotulos).mean()
    return np.linalg.norm(X - centros.loc[rotulos].to_numpy(), axis=1)
