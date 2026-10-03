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
from sklearn.metrics import (calinski_harabasz_score, davies_bouldin_score,
                             silhouette_score)
from sklearn.neighbors import NearestNeighbors

from config import K_MAX, K_MIN, N_INIT, RANDOM_STATE

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
