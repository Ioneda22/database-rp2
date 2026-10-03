# T3 — Notebook 05: estabilidade e escolha do modelo

**Responsável:** Guilherme · **Prazo:** domingo 04/10 (a tabela precisa estar pronta para a aula de 07/10) · **Tempo estimado:** 2h com revisão

## Por que

Uma partição só serve para descrever perfis se não mudar muito quando os dados
mudam um pouco. O artigo (seção 3.3) promete três testes: subjanelas de dois
anos, com e sem os municípios pequenos e, para o K-means, sementes diferentes.
Este notebook roda os testes, monta a tabela de comparação do artigo e aplica
a regra de decisão que o grupo combinou **antes** de ver os resultados.

## Antes de começar

- T1 e T2 precisam estar prontas (`src/preprocessamento.py`,
  `src/clusterizacao.py`, `metricas_clusterizacao.csv`, `dbscan_grade.csv`).
- Leia `CLAUDE.md` e o notebook 04.

## A regra de decisão (copiar para o Markdown do notebook)

> **Versão de 02/10.** Os passos 1 a 5 são os do plano; o passo 4b e a
> tolerância de 0,05 foram acrescentados em 02/10. O grupo confirma esta
> versão **antes** de rodar o notebook. Se não concordar com o 4b, apague-o
> daqui antes de pedir a tarefa ao Claude Code.

1. **Candidatos**: K-means e Ward com k de 2 a 10. O DBSCAN só entra se alguma
   configuração da grade tiver pelo menos 2 grupos e menos de 20% de ruído.
2. **Filtro de tamanho**: sai a partição com algum grupo menor que 5% dos
   municípios (32 municípios).
3. **Qualidade**: entre as que sobraram, para cada algoritmo ficam os k que
   estão entre os 3 melhores em silhueta **e** entre os 3 melhores em
   Calinski–Harabasz. Se nenhum k satisfizer as duas, ficam os 3 melhores em
   silhueta. O Davies–Bouldin é reportado e serve de desempate.
4. **Estabilidade**: os candidatos são ordenados pelo `ari_estabilidade`
   (média dos três ARI abaixo). Diferenças menores que **0,05** contam como
   empate.
   - **4b. Dois níveis.** A melhor partição com k = 2 é registrada como a
     **divisão mais robusta** e entra na resposta da pergunta (ii). Uma
     divisão em dois grupos, porém, não forma "perfis" no sentido da pergunta
     (iii). Por isso, a partição usada para caracterizar os perfis é a mais
     estável **com k ≥ 3**, pelos mesmos critérios.
5. **Interpretabilidade**: entre empatados, o grupo escolhe a partição cujos
   perfis todos conseguem descrever em uma frase, e registra a justificativa.

O código aplica os passos 1 a 4b e **sugere**: imprime a melhor partição com
k = 2 e a lista de candidatos com k ≥ 3, já marcando os empates. O passo 5 é
nosso.

## O que implementar

### 1. Funções novas em `src/clusterizacao.py`

- `ari_sementes(W, k, n=20) -> tuple[float, float]`: K-means de referência com
  `n_init=N_INIT`; depois 20 K-means com `n_init=1` e `random_state` de 0 a 19;
  devolve média e mínimo do ARI contra a referência. Comentário explicando por
  que isso só se aplica ao K-means (o Ward não sorteia nada, sempre dá o mesmo
  resultado).
- `ari_subjanela(base_mod, painel, cobertura, features, bloco_de, anos, algoritmo, k, rotulos_ref) -> float`:
  `taxas_da_janela` → `montar_matriz` → `agrupar` → ARI contra os rótulos da
  janela completa.
- `ari_sem_pequenos(base_mod, features, bloco_de, algoritmo, k, rotulos_ref) -> float`:
  tira os municípios com `flag_pop_pequena`, refaz `montar_matriz` **só com os
  que sobraram** (como se os pequenos nunca tivessem existido), agrupa e
  calcula o ARI contra a referência restrita aos mesmos municípios.
- Em todos: comentário explicando que o ARI não depende do número que cada
  grupo recebe (o "grupo 0" de uma partição pode ser o "grupo 2" da outra), só
  de quem está junto com quem.

Para não recalcular à toa, montar a matriz de cada subjanela **uma vez** e
reaproveitar para todos os candidatos.

### 2. Constantes em `src/config.py`

```python
# Preenchidas pelo grupo depois do notebook 05 (passo 5 da regra de decisão).
ALGORITMO_ESCOLHIDO = None   # "kmeans" ou "ward"
K_ESCOLHIDO = None
SUBJANELAS = [[2023, 2024], [2024, 2025]]
TOLERANCIA_ARI = 0.05        # diferença de ARI abaixo disso conta como empate
K_MIN_PERFIS = 3             # passo 4b: perfis precisam de pelo menos 3 grupos
```

### 3. `notebooks/05_estabilidade_escolha.ipynb`

- **Abertura.** Objetivo, saídas (`tabela_comparacao_algoritmos.csv` e, depois
  da escolha, `perfis.csv`) e a regra de decisão completa, com a frase "regra
  definida antes da execução dos testes".
- **`## 1. Por que testar a estabilidade`.** Markdown curto: o que é o ARI
  (índice de Rand ajustado) em linguagem comum: 1 quando as duas partições são
  iguais, perto de 0 quando concordam tanto quanto um sorteio.
- **`## 2. Subjanelas`.** Por que 2023–2024 e 2024–2025 (exposição de 2 anos
  cada; mesmas taxas por 100 mil por ano). `assert` de que a exposição é 2,0.
- **`## 3. Sem os municípios pequenos`.** Por que (uma única ocorrência muda
  muito a taxa de uma cidade com menos de 5.000 habitantes). Dizer quantos
  municípios ficam (495).
- **`## 4. Sementes (só K-means)`.**
- **`## 5. Tabela de comparação`.** Juntar `metricas_clusterizacao.csv` com os
  ARI. Colunas: `algoritmo`, `k`, `silhueta`, `calinski_harabasz`,
  `davies_bouldin`, `menor_grupo`, `ari_2023_2024`, `ari_2024_2025`,
  `ari_sem_pequenos`, `ari_estabilidade`, `ari_sementes_media`,
  `ari_sementes_min`, `passa_tamanho`, `candidato_qualidade`. Acrescentar uma
  linha-resumo do DBSCAN (melhor configuração da grade e se foi admitida no
  passo 1). Salvar `data/processed/tabela_comparacao_algoritmos.csv`.
- **`## 6. Aplicação da regra`.** Uma célula por passo, cada uma mostrando
  quem sobrou. A última imprime a sugestão e os empatados. Markdown escrito
  depois de rodar.
- **`## 7. Partição escolhida`.** Se `ALGORITMO_ESCOLHIDO` ou `K_ESCOLHIDO`
  estiverem `None`, a célula imprime "escolha pendente: preencher no config.py
  depois da reunião" e não salva nada. Quando estiverem preenchidos:
  - agrupar com o modelo escolhido;
  - **renumerar os perfis em ordem crescente da média das 6 variáveis
    socioeconômicas padronizadas** (`Z` da T1), de modo que o perfil 1 seja o
    de menor condição socioeconômica. Comentário explicando que a numeração do
    scikit-learn é arbitrária e muda de uma execução para outra; ordenando por
    um critério fixo, "perfil 1" quer dizer sempre a mesma coisa (e o mapa
    pode usar uma escala de cor em ordem);
  - salvar `data/processed/perfis.csv` com `codigo_ibge`, `municipio`,
    `perfil`, `distancia_ao_centro` (distância em `W` até a média do perfil,
    usada na T4 para achar os municípios mais típicos) e `divisao_k2` (a
    melhor partição com k = 2 apontada pelo passo 4b, numerada pelo mesmo
    critério socioeconômico; se o grupo tiver recusado o 4b, não criar esta
    coluna);
  - mostrar o tamanho de cada perfil.

## Critérios de aceite

- [ ] `tabela_comparacao_algoritmos.csv` com 18 linhas + resumo do DBSCAN.
- [ ] Os ARI das subjanelas usam matrizes refeitas pelo `montar_matriz` (nada
      copiado à mão).
- [ ] A regra aplicada passo a passo, com a sugestão impressa (a melhor com
      k = 2 e os candidatos com k ≥ 3).
- [ ] Com as constantes em `None`, nada é salvo além da tabela.
- [ ] Notebook roda em menos de 10 minutos.
- [ ] Entrada no changelog do `ANDAMENTO.md`.

## Prompt para colar no Claude Code

> Leia o `CLAUDE.md` e `tarefas/T3_estabilidade_e_escolha.md`. A regra de
> decisão desse arquivo já foi combinada pelo grupo: implemente exatamente
> como está escrita, sem ajustar limites depois de ver os números. Me mostre um
> plano curto, implemente, rode o notebook 05 e me mostre a tabela de
> comparação e a sugestão da regra. Não preencha `ALGORITMO_ESCOLHIDO` nem
> `K_ESCOLHIDO`.
