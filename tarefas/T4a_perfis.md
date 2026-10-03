# T4a — Notebook 06: caracterizar os perfis

**Responsável:** Higor · **Prazo:** sexta 09/10 · **Tempo estimado:** 1h30 com revisão

## Por que

É a pergunta (iii) do artigo: que perfis aparecem. Achar os grupos é metade
do trabalho; a outra metade é dizer o que eles são, de um jeito que se leia no
artigo e se explique no vídeo.

## Antes de começar

- `ALGORITMO_ESCOLHIDO` e `K_ESCOLHIDO` preenchidos no `config.py` e
  `data/processed/perfis.csv` gerado pelo notebook 05.
- Leia `CLAUDE.md` e o notebook 05.

## O que implementar

### 1. Funções novas em `src/figuras.py` (seção `# Fase 5 - perfis`)

- `plot_perfis(medias, bloco_de, ordem_blocos, rotulos_perfis) -> Figure` —
  **Figura 5**. Mapa de calor com uma linha por feature (ordem por bloco, com
  linhas cinza separando os blocos, como na Figura 2) e uma coluna por perfil
  (rótulo "Perfil 1 (n = 123)"). Valor = média padronizada da feature no
  perfil. `cmap="RdBu"`, `vmin=-1.5`, `vmax=1.5`, número com uma casa decimal
  em cada célula. Rótulos sem `taxa_` e sem `_ord`, como na Figura 2. Barra
  de cor com o rótulo "desvios em relação à média dos 644 municípios".
  Docstring: mostra em que cada perfil fica acima ou abaixo da média; serve
  para dar nome aos perfis.

### 2. `notebooks/06_perfis.ipynb`

- **Abertura.** Objetivo, saídas (Figura 5, `tabela_perfis.csv`,
  `tabela_exemplos_perfis.csv`) e o modelo usado (lido do `config.py`, não
  escrito à mão).
- **`## 1. Tamanho dos perfis`.** Número de municípios, população mediana e
  % de municípios pequenos (`flag_pop_pequena`) em cada perfil. Se o
  `perfis.csv` tiver a coluna `divisao_k2`, uma tabela cruzada
  (`pd.crosstab`) entre `perfil` e `divisao_k2`, para mostrar como os perfis
  se encaixam (ou não) nas duas grandes divisões.
- **`## 2. Figura 5 - perfis em relação à média`.** Médias de `Z` (a matriz
  padronizada **sem** o peso por bloco, vinda de `montar_matriz`) por perfil.
  Markdown explicando por que `Z` e não `W`: o peso por bloco encolhe os
  valores e deixaria as cores apagadas, sem mudar quem está acima ou abaixo da
  média. Comentário no código explicando o `vmin`/`vmax`: médias além de 1,5
  desvio ficam na cor mais forte, para que um perfil muito extremo em uma
  variável não deixe todas as outras células quase brancas. O número escrito
  na célula continua mostrando o valor real.
- **`## 3. Os perfis em unidades originais`.** O mapa de calor diz "acima ou
  abaixo da média"; esta tabela diz "quanto". Medianas por perfil, nas
  unidades da base (não transformadas), de: `populacao`, `taxa_cvli`,
  `taxa_roubo_outros`, `taxa_furto_outros`, `taxa_estupro_total`,
  `renda_domiciliar_mediana`, `pib_percapita`, `taxa_urbanizacao`,
  `prop_esgoto_adequado`, `taxa_alfabetizacao` e `iegm_ord` (este último só
  como contexto, já que não é feature). Mais uma linha "total" com a mediana
  dos 644. Salvar `data/processed/tabela_perfis.csv` com perfis nas linhas.
- **`## 4. Municípios de cada perfil`.** Para cada perfil: os 5 mais típicos
  (menor `distancia_ao_centro`) e os 3 mais populosos. Comentário explicando a
  diferença: os típicos representam o perfil; os populosos são os nomes que o
  leitor reconhece. Salvar `data/processed/tabela_exemplos_perfis.csv`.
- **`## 5. Leitura dos perfis`.** Uma célula de Markdown por perfil, **escrita
  depois de rodar**, com: os 3 ou 4 traços mais marcantes (do mapa de calor),
  números da tabela da seção 3 e os exemplos. **Não dar nome aos perfis**:
  deixar `Nome: [a definir pelo grupo]`. O nome sai da reunião de 09/10.

## Critérios de aceite

- [ ] `figuras/figura5_perfis.png` legível em preto e branco (os números nas
      células garantem isso).
- [ ] `tabela_perfis.csv` e `tabela_exemplos_perfis.csv` salvas.
- [ ] Todo número no Markdown confere com as tabelas.
- [ ] Nenhum nome de perfil inventado.
- [ ] Entrada no changelog do `ANDAMENTO.md`.

## Prompt para colar no Claude Code

> Leia o `CLAUDE.md` e `tarefas/T4a_perfis.md`. Me mostre um plano curto,
> implemente, rode o notebook 06 e me mostre a Figura 5, a tabela de perfis e
> os exemplos. Não dê nome aos perfis.
