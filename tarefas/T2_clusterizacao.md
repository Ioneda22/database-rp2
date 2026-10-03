# T2 — Notebook 04: rodar os três algoritmos

**Responsável:** Higor · **Prazo:** sábado 03/10 (depois da T1) · **Tempo estimado:** 1h30 com revisão

## Por que

É o núcleo da pergunta (ii) do artigo: aplicar K-means, hierárquico de Ward e
DBSCAN sobre a mesma matriz e medir a qualidade de cada partição. Este
notebook **só mede**. A escolha do modelo fica para o notebook 05 (T3), que
aplica a regra de decisão combinada pelo grupo.

## Antes de começar

- A T1 precisa estar pronta (`src/preprocessamento.py`).
- Leia `CLAUDE.md`, o notebook 03 inteiro (padrão de texto e de código) e
  `src/figuras.py`.

## O que implementar

### 1. Constantes novas em `src/config.py`

Numa seção nova `# --- Clusterização ---`, com um comentário curto em cada:

```python
RANDOM_STATE = 42
N_INIT = 50                # quantas vezes o K-means recomeça com centros novos
K_MIN, K_MAX = 2, 10       # faixa de número de grupos testada
TAMANHO_MINIMO_GRUPO = 0.05   # grupo com menos de 5% dos municípios não vira perfil
VARIANCIA_PCA_DBSCAN = 0.80   # o DBSCAN roda sobre as componentes que somam 80%
```

### 2. `src/clusterizacao.py`

Funções pequenas, cada uma com docstring:

- `agrupar(W, algoritmo, k) -> np.ndarray`: devolve os rótulos.
  `"kmeans"` → `KMeans(k, n_init=N_INIT, random_state=RANDOM_STATE)`;
  `"ward"` → `AgglomerativeClustering(k, linkage="ward")`.
- `soma_quadrados_interna(W, rotulos) -> float`: soma das distâncias ao
  quadrado de cada município até a média do seu grupo. Para o K-means é a
  própria inércia; calculando à mão dá para comparar com o Ward também.
- `metricas_por_k(W) -> pd.DataFrame`: para cada algoritmo (`kmeans`, `ward`)
  e cada k de `K_MIN` a `K_MAX`, uma linha com `algoritmo`, `k`,
  `soma_quadrados`, `silhueta`, `calinski_harabasz`, `davies_bouldin`,
  `menor_grupo`, `maior_grupo` (em número de municípios). São 18 linhas.
- `componentes_pca(W, variancia) -> np.ndarray`: escores do PCA com o número
  de componentes que soma `variancia` da variância (deve dar 12 componentes;
  conferir com `assert`, porque o artigo já cita esse número).
- `distancia_k_vizinho(X, min_pts) -> np.ndarray`: distância de cada ponto ao
  seu `min_pts`-ésimo vizinho, ordenada. Usar
  `NearestNeighbors(n_neighbors=min_pts)`; o próprio ponto conta como o
  primeiro vizinho, que é a mesma convenção do `min_samples` do DBSCAN do
  scikit-learn. Explicar isso num comentário.
- `grade_dbscan(X, min_pts_lista, quantis) -> pd.DataFrame`: para cada
  `min_pts`, testa como `eps` os quantis 0,50, 0,60, 0,70, 0,80, 0,90, 0,95 e
  0,99 da curva de k-distância. Uma linha por combinação com `min_pts`, `eps`,
  `n_grupos`, `pct_ruido`, `maior_grupo_pct` e `silhueta` (calculada sem os
  pontos de ruído e só quando houver pelo menos 2 grupos; senão `NaN`).
  `min_pts_lista = [d + 1, 2 * d]`, sendo `d` o número de componentes (13 e
  24). São duas regras práticas comuns; comentar isso sem citar autor.

### 3. Funções novas em `src/figuras.py`

Numa seção nova `# Fase 4 - clusterização`, no padrão das outras:

- `plot_selecao_k(metricas) -> Figure` — **Figura 4**. Grade 2×2:
  (a) soma dos quadrados interna (cotovelo), (b) silhueta, (c)
  Calinski–Harabasz, (d) Davies–Bouldin. Em cada painel, K-means em `C0` com
  marcador `o` e Ward em `C1` com marcador `s` e linha tracejada (para ler em
  preto e branco). No título de cada painel, indicar se maior ou menor é
  melhor. Eixo x com os inteiros de k. Tamanho que caiba em meia coluna do
  artigo, cerca de `figsize=(7, 5)`.
- `plot_k_distancia(distancias, eps_testados) -> Figure` — figura de apoio.
  Curva ordenada com linhas horizontais pontilhadas cinza nos `eps` testados.
  Docstring: mostra se existe um "joelho" na curva; sem joelho, não há uma
  separação natural entre regiões densas e ruído.
- `plot_dendrograma(W) -> Figure` — figura de apoio. `scipy` com ligação
  `ward`, `truncate_mode="lastp"`, `p=30`, sem rótulos de município. Eixo y
  "custo da fusão".

### 4. `notebooks/04_clusterizacao.ipynb`

Estrutura (títulos de Markdown):

- **Abertura.** O que o notebook faz, quais saídas do artigo produz (Figura 4,
  `metricas_clusterizacao.csv`, `dbscan_grade.csv`) e um aviso: a escolha do
  modelo é feita no notebook 05, com uma regra definida antes de ver estes
  números.
- **`## 1. Matriz de entrada`.** Ler `matriz_modelagem.csv`. `assert` de que
  são 644 linhas, de que as colunas são as 22 features na ordem do dicionário
  (usar `carregar_features`) e de que não há ausentes.
- **`## 2. Os três algoritmos`.** Só Markdown: um parágrafo curto para cada
  algoritmo, em linguagem comum (K-means: grupos em volta de centros, k
  escolhido por nós, sorteio inicial; Ward: junta os dois grupos mais
  parecidos, passo a passo, formando uma árvore; DBSCAN: procura regiões com
  muitos municípios próximos e chama de ruído quem fica isolado).
- **`## 3. K-means e Ward para k de 2 a 10`.** Markdown explicando cada métrica
  em uma frase (o que mede e se maior ou menor é melhor). Rodar
  `metricas_por_k`, mostrar a tabela arredondada, salvar
  `metricas_clusterizacao.csv`, gerar e salvar a Figura 4.
- **`## 4. Dendrograma`.** Figura de apoio e um parágrafo explicando como ler.
- **`## 5. DBSCAN`.** Markdown: por que ele roda sobre as componentes do PCA
  (com 22 colunas as distâncias ficam parecidas demais entre si, e "região
  densa" deixa de fazer sentido; o próprio notebook 03 registrou esse alerta
  antes). Calcular as componentes, a k-distância, a figura de apoio e a grade.
  Salvar `dbscan_grade.csv`.
- **`## 6. Resumo`.** Uma tabela com a melhor linha de cada algoritmo **por
  métrica** (só descrição, sem escolher). Markdown com o que os números
  mostram, escrito **depois** de rodar e conferido com a tabela.

Se a silhueta sair baixa (abaixo de 0,25), o texto deve ligar isso ao que o
notebook 03 já mostrou: os municípios formam uma nuvem contínua. Não tratar
como erro.

## Critérios de aceite

- [ ] `metricas_clusterizacao.csv` com 18 linhas e as colunas pedidas.
- [ ] `dbscan_grade.csv` com 14 linhas (2 `min_pts` × 7 quantis).
- [ ] `figuras/figura4_selecao_k.png`, `figura_k_distancia.png` e
      `figura_dendrograma.png`.
- [ ] `assert` de 12 componentes passando.
- [ ] Notebook roda do início ao fim em menos de 5 minutos.
- [ ] Nenhum arquivo dos notebooks 01–03 mudou.
- [ ] Todo número citado em Markdown confere com a saída da célula.
- [ ] Entrada no changelog do `ANDAMENTO.md`.

## Prompt para colar no Claude Code

> Leia o `CLAUDE.md` e `tarefas/T2_clusterizacao.md`. Leia também o notebook
> 03 inteiro para pegar o nosso jeito de escrever. Me mostre um plano curto,
> implemente, rode o notebook 04 e me mostre a tabela de métricas, a grade do
> DBSCAN e a Figura 4. Não escolha o modelo.
