# T1 — Levar o pré-processamento para `src/`

**Responsável:** Higor · **Prazo:** sábado 03/10, de manhã (as outras tarefas dependem desta) · **Tempo estimado:** 30 min

## Por que

Os testes de estabilidade (T3) e de sensibilidade (T5) precisam refazer o
pré-processamento várias vezes: com taxas de outra janela de anos, sem os
municípios pequenos ou sem uma variável. Hoje esse cálculo só existe dentro do
notebook 03. Se cada notebook copiar o código, uma diferença pequena entre as
cópias invalida a comparação. Por isso ele vai virar função, usada por todos.

## Antes de começar

Leia `CLAUDE.md`, `notebooks/03_preprocessamento.ipynb` (células 3, 5 e 7) e
as funções `definir_janela` e `agregar_janela` de `src/merge_bases.py`.

## O que implementar

Criar `src/preprocessamento.py` com:

1. `ORDEM_BLOCOS = ["criminalidade", "socioeconomico", "gestao"]`.

2. `carregar_features(dic: pd.DataFrame) -> tuple[list[str], pd.Series]`
   Devolve a lista das 22 features ordenada por bloco e por nome (igual ao
   notebook 03) e a série `bloco_de` (coluna → bloco).

3. `taxas_da_janela(base: pd.DataFrame, painel: pd.DataFrame, cobertura: pd.DataFrame, anos: list[int]) -> pd.DataFrame`
   Devolve uma **cópia** de `base` com as colunas `taxa_<grupo>` de
   criminalidade recalculadas só com os anos pedidos.
   - Reaproveitar `agregar_janela(painel, anos)` de `merge_bases.py`.
   - Exposição = soma de `n_meses / 12` dos anos pedidos, lida da `cobertura`
     (a mesma conta de `definir_janela`, mas recebendo `anos` como parâmetro,
     porque `definir_janela` lê `ANOS_JANELA` do config).
   - Mesma fórmula do `merge_bases.py`:
     `ocorrências / (população × exposição) × TAXA_POR_HABITANTES`, com
     município sem ocorrência valendo 0.
   - Não mexer em nenhuma outra coluna (`prop_via_publica`, IEGM, IBGE ficam
     como estão).

4. `montar_matriz(df: pd.DataFrame, features: list[str], bloco_de: pd.Series) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series]`
   Faz exatamente o que as células 5 e 7 do notebook 03 fazem e devolve
   `(Z, W, peso)`:
   - `Z`: só `log1p` (nas taxas criminais e nas duas colunas em R$ que
     estiverem em `features`) e `StandardScaler`;
   - `W`: `Z` multiplicada pelo peso `1/√n` do bloco;
   - `peso`: o peso de cada coluna.
   - O peso tem que ser calculado **a partir da lista `features` recebida**: se
     a T5 tirar uma coluna da gestão, o bloco passa a ter 6 colunas e o peso
     muda para `1/√6`.
   - `df` já chega filtrado (o chamador decide quem entra). O índice de saída é
     `0..n-1` (`reset_index`), para bater com os rótulos do scikit-learn.

## O que **não** fazer

- **Não reescrever o notebook 03.** Ele é didático, explica cada passo, e já
  foi entregue. Só acrescentar uma célula no final (abaixo).
- Não mudar `merge_bases.py`.

## Acrescentar ao fim do notebook 03

Uma seção `## 7. Conferência com src/preprocessamento.py` com uma célula de
Markdown curta (o código desta fase passou a existir também como função, para
ser reaplicado nos testes de estabilidade, e esta célula confirma que as duas
versões dão o mesmo resultado) e uma célula de código com:

- `assert` de que `montar_matriz(modelagem, features, bloco_de)[1]` é igual a
  `W` (use `np.allclose`);
- `assert` de que `taxas_da_janela(..., [2023, 2024, 2025])` reproduz as 9
  taxas criminais da `base_final.csv` nos 644 municípios.

Rodar o notebook 03 inteiro de novo e conferir que **nenhuma figura nem a
`matriz_modelagem.csv` mudou** (`git diff --stat` só deve mostrar o próprio
notebook e o arquivo novo).

## Critérios de aceite

- [ ] `src/preprocessamento.py` existe, com as 3 funções documentadas.
- [ ] Os dois `assert` passam.
- [ ] `matriz_modelagem.csv` e as figuras do notebook 03 não mudaram.
- [ ] Entrada no changelog do `ANDAMENTO.md`.

## Prompt para colar no Claude Code

> Leia o `CLAUDE.md` e o arquivo `tarefas/T1_preprocessamento_em_src.md`.
> Antes de escrever código, me mostre em poucas linhas o que vai criar e o que
> vai mudar. Depois implemente, rode o notebook 03 e me mostre o resultado dos
> dois `assert` e o `git diff --stat`.
