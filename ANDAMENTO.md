# Andamento — o que está pronto, o que falta e o que mudou

**Atualizado em:** 07/09/2026 · **Entrega:** 16/09/2026, 23h59 (9 dias)

Este arquivo é o estado do projeto. O [PLANEJAMENTO.md](PLANEJAMENTO.md)
continua sendo o plano e o cronograma; o [README.md](README.md) explica como
rodar. Aqui fica o que já existe, o que ainda precisa ser produzido e o
registro do que mudou.

---

## 1. Onde estamos

| Fase | O que é | Situação |
|---|---|---|
| 0 | Completar as bases | ✅ concluída |
| 1 | Validar a janela temporal | ✅ concluída — janela **confirmada** |
| 2 | Exploratória e seleção de variáveis | ✅ concluída — **sem poda** |
| 3 | Pré-processamento | ⬜ a fazer |
| 4 | Clusterização e comparação | ⬜ a fazer |
| 5 | Caracterização dos perfis | ⬜ a fazer |
| 6 | Escrita conceitual (Introdução + Correlatos) | ⬜ **não começou** |
| 7 | Escrita dos resultados | ⬜ a fazer |
| 8 | Fechamento | ⬜ a fazer |

**A Trilha A está adiantada em relação ao risco; a Trilha B é o problema.** As
Fases 0, 1 e 2 fecharam. Mas o `artigo.tex` não teve uma linha alterada: ainda
tem o título antigo, a seção `Cronograma` e a Metodologia inteira no futuro.
São 5 das 11 páginas que **não dependem de dado nenhum** e que já poderiam
estar prontas.

---

## 2. O que está pronto

### 2.1 Base de dados

`data/processed/base_final.csv` — **645 municípios × 49 colunas**.

**19 features de agrupamento:** 9 criminalidade + 2 socioeconômico + 8 gestão.
As outras 30 colunas são identificação, contexto dos crimes, metadados e as
flags de alerta.

| Fonte | Ano de referência |
|---|---|
| Criminalidade (SSP-SP) | 2023–2025, exposição 3,000 anos |
| Gestão (IEGM/TCE-SP) | exercícios 2022–2024 (apurados 2023–2025), média |
| População (denominador) | 2024 |
| PIB (SIDRA 5938) | 2023 |
| Urbanização (SIDRA 9923) | Censo 2022 |

Acompanham: `dicionario_base.csv` (bloco, tipo e papel de cada coluna) e
`relatorio_base.txt`.

### 2.2 Código

| Arquivo | O que faz |
|---|---|
| `main.py` | orquestra as 4 etapas de construção |
| `src/config.py` | caminhos, janela, tabelas do SIDRA, agrupamento de naturezas |
| `src/ibge_sidra.py` | baixa população, PIB e urbanização da API do SIDRA |
| `src/parse_ssp.py` | 4,8 M de linhas de microdado → painel mensal (streaming) |
| `src/parse_iegm.py` | 3 exercícios do IEGM → média ordinal por município |
| `src/merge_bases.py` | une tudo por `codigo_ibge` → base final + dicionário |
| `src/estilo.py` | paleta validada e `rcParams` das figuras |
| `notebooks/01_validacao_temporal.ipynb` | Fase 1 |
| `notebooks/02_exploratoria.ipynb` | Fase 2 |

### 2.3 Figuras e tabelas já geradas

| Saída | Onde | Entra em |
|---|---|---|
| Figura 1 — série mensal 2022–2025 | `figuras/figura1_serie_mensal.png` | Resultados |
| Figura 1b — série por natureza | `figuras/figura1b_serie_por_natureza.png` | apoio |
| Figura 2 — correlação de Spearman | `figuras/figura2_spearman.png` | Resultados |
| Distribuições antes/depois de `log1p` | `figuras/figura_distribuicoes_log1p.png` | apoio |
| Tabela 2 — descritivas + zero-inflação | `data/processed/tabela2_descritivas.csv` | Resultados |

### 2.4 Números verificados — prontos para o artigo

Todos medidos, nenhum estimado. Servem para a Metodologia e os Resultados.

**Volume e integridade**

- 4.792.830 linhas de microdado lidas (2022–2025); 3.594.857 na janela.
- Repetição de `(delegacia, ano_bo, num_bo, natureza)`: **0,01%** em 2023 e
  2024, 0,00% em 2025 — contar linhas é contar ocorrências, e isso foi medido,
  não suposto.
- Registro ≠ circunscrição: **0,37%** (2023), 0,34% (2024), 0,31% (2025).
- Dos 683 valores distintos de `NOME_MUNICIPIO`, **532 apontam para mais de um
  código IBGE** — a junção por nome atribuiria o crime à cidade do BO.

**Base**

- 645 municípios; **644** na modelagem (São Paulo fora: TCM-SP, sem IEGM).
- **149 municípios (23,1%)** com menos de 5.000 habitantes; mediana estadual
  de 13.399.
- Ausentes: só `taxa_recuperacao_veiculo` e `prop_veiculo_motocicleta`, em 44
  municípios (6,8%) que não tiveram veículo subtraído em 3 anos — o `NaN` é a
  resposta certa. Nenhuma outra coluna tem ausente além do IEGM da capital.
- População de SP em 2024: 45.973.194.

**Validação externa**

- **CVLI estadual: 6,0 por 100 mil/ano**, compatível com a taxa publicada de
  SP. Capital em 4,6 — abaixo da média estadual, como se espera.
- Reconstruir a contagem a partir de `taxa × população × exposição` devolve o
  painel ao número exato (8.298 CVLI, 94.191 roubos de veículo).

**Fase 1 — janela**

- Sem degrau em jan/2023. Na virada 2022→2023, **5 naturezas sobem e 5
  descem**; variação mediana de 6,2% contra 5,6% nas viradas seguintes.
- As únicas que destoam são `cvli` e `estupro_total` — as *menos* sensíveis ao
  sistema de registro, o oposto do que a hipótese de artefato previria.

**Fase 2 — features**

- Zero-inflação do CVLI: **20,3%** — abaixo dos ~23% que o planejamento
  projetava para uma janela de 3 anos.
- Nenhum par com |ρ| > 0,85. Máximo: `roubo_outros × roubo_veiculo` = **0,763**.
  **As 19 features seguem inteiras.**
- `log1p` mantido: a assimetria negativa que ele parece introduzir é
  zero-inflação, não excesso de correção. Sem os zeros, toda assimetria
  pós-`log1p` cai para a faixa −0,5 a +0,7. Em `taxa_estupro_total`, **7
  municípios** produzem assimetria −2,3.
- Os máximos das taxas são municípios minúsculos: `taxa_cvli` em Balbinos
  (3.963 hab.), `taxa_estupro_total` em Guarani d'Oeste (1.999 hab.).

---

## 3. O que falta produzir

### 3.1 Código — Fase 3: pré-processamento

**`notebooks/03_preprocessamento.ipynb`**

1. Ler `dicionario_base.csv` para bloco e papel — nunca listar colunas na mão.
2. Filtrar `flag_sem_iegm` (a capital).
3. `log1p` nas 9 taxas e no PIB per capita; depois `RobustScaler` **ajustado
   só no subconjunto clusterizado**, não na base inteira.
4. **Peso por bloco `1/√n`**: 0,333 (criminalidade, 9), 0,707 (socioeconômico,
   2), 0,354 (gestão, 8). Sem isso o IEGM leva ~40% do orçamento de distância
   carregando pouca variância.
5. PCA sobre a matriz padronizada — necessária para o DBSCAN da Fase 4.

**Entrega:** matriz `X` + **Figura 3** (variância explicada acumulada).

### 3.2 Código — Fase 4: clusterização

**`notebooks/04_clusterizacao.ipynb`**

| Algoritmo | Seleção de parâmetro |
|---|---|
| K-means | cotovelo + silhueta + Calinski–Harabasz, k = 2..10 |
| Hierárquico aglomerativo | dendrograma + as mesmas três métricas |
| DBSCAN | distância ao k-ésimo vizinho, **sobre as componentes do PCA** |

> Com 644 pontos em ~19 dimensões, o DBSCAN provavelmente rotula quase tudo
> como ruído. **"DBSCAN degenerou" é resultado comparativo legítimo**, desde
> que reportado com o gráfico de k-distância mostrando a ausência de joelho.

**Entrega:** **Tabela 3** (3 algoritmos × silhueta, Calinski–Harabasz,
Davies–Bouldin) e **Figura 4** (seleção de k).

### 3.3 Código — Fase 5: caracterização dos perfis

**`notebooks/05_perfis.ipynb`**

- Médias e medianas por variável em cada grupo.
- **Heatmap de médias padronizadas** (mais legível que radar com ~19
  variáveis).
- Kruskal–Wallis reportando **tamanho de efeito (ε²)**, não p-valor: nas
  variáveis que construíram os clusters o teste sempre rejeita. Usar
  `prop_via_publica` (`papel = validacao_externa`) como validação genuinamente
  externa.
- Nomear os perfis encontrados.

**Entrega:** **Figura 5** (heatmap) e **Tabela 4** (perfis × variáveis).

### 3.4 Código — análise de estabilidade

Prometida na §3.3 do `artigo.tex` e agora barata, porque o painel é mensal:

- Reclusterizar em 2023–2024 vs 2024–2025 e comparar as partições por
  **Adjusted Rand Index**, sem reprocessar microdado.
- Rodar com e sem os 149 municípios de `flag_pop_pequena` e comparar por ARI.

### 3.5 Código — cortável

**Mapa coroplético** (`geopandas` + malha municipal do IBGE). É a peça mais
cara do projeto. **Não iniciar se a Fase 4 escorregar** — vira trabalho
futuro.

### 3.6 Texto — `artigo.tex`

Ajustes estruturais:

- [ ] Aplicar o título revisado (com *"indicadores integrados de"*). O atual
      usa `relacionando-os a`, que descreve duas etapas — o oposto do desenho
      de etapa única.
- [ ] **Remover a seção `Cronograma`** (não consta nas seções exigidas).
- [ ] Renomear `Materiais e Métodos` → `Metodologia`.
- [ ] Atualizar resumo e *abstract*: hoje estão inteiramente no futuro.

Seções:

| Seção | Máx. | Hoje | Falta |
|---|---:|---:|---|
| Introdução | 2 p | 0,6 p | **+1,4 p** (~950 palavras) |
| Trabalhos Correlatos | 3 p | 0,9 p | **+2,1 p** (~1.400 palavras) |
| Metodologia | 2 p | 0,9 p | reescrever no passado |
| Resultados Parciais | 3 p | 0 | **seção nova** |
| Discussão e Conclusão | 1 p | 0 | **seção nova** |

**Introdução:** dimensionar o problema com números; **citar a literatura de
desorganização social** — a linha 48 do tex invoca essa literatura *sem
nenhuma citação* (Shaw & McKay, Sampson); explicitar as perguntas de pesquisa.

**Trabalhos Correlatos**, em ordem de custo-benefício: (1) promover
`silva2025` e `soliani2024`, já citados mas nunca discutidos na §2 — dois
parágrafos sem leitura nova; (2) **tabela comparativa** (`trabalho | recorte |
fonte | método | validação | integra gestão pública?`), que torna visual a
lacuna afirmada em prosa; (3) buscar 2 trabalhos novos.

**Metodologia** — incorporar o que hoje só existe no código e no README:
janela e sua validação empírica, junção por `codigo_ibge`, município de
circunscrição, taxa por 100 mil habitantes-ano com população de 2024, CVLI,
naturezas excluídas, exclusão da capital, peso por bloco e transformações.

**Discussão** — limitações declaradas de frente: anos de referência
heterogêneos; capital fora; 149 municípios abaixo de 5.000 habitantes;
`taxa_trafico` medindo também intensidade de policiamento.

---

## 4. Pendências e riscos

| Item | Situação |
|---|---|
| `.bib` e template SBC | Resolvido — está no Overleaf |
| Trilha B (5 páginas sem dependência de dados) | **Não começou. Maior risco.** |
| Kernel dos notebooks | 4 Pythons na máquina; o que tem as bibliotecas é `C:\Python314\python.exe`. Rodar `pip install -r requirements.txt` e conferir o `sys.executable` que a 1ª célula imprime |
| Nome de município ambíguo | `3547908` aparece como `S.ANTONIO DA ALEGRIA` e `SANTO ANTONIO DA ALEGRIA` — mesma cidade, abreviação diferente. Inofensivo, porque a junção é por código |
| `*_conceito` ≠ `*_ord` | Por construção: `_ord` é a média dos 3 exercícios, `_conceito` é a letra do mais recente. Campinas: `B` e `1,667` |

**Ordem de corte**, se 12/09 chegar com a Trilha A atrasada: (1) mapa
coroplético; (2) DBSCAN; (3) caracterização de perfis. **Nunca cortar** as
Fases 0, 2 e 6 — as duas primeiras já estão feitas.

---

## 5. Changelog

### [07/09/2026] Fases 1 e 2 — análise em notebook

**Adicionado**

- `src/estilo.py`: paleta e `rcParams` comuns às figuras. As cores passaram em
  teste de separação para daltonismo e contraste (ΔE protan 24,7; mínimo 8) em
  vez de serem escolhidas a olho.
- `notebooks/01_validacao_temporal.ipynb` — Fase 1. Janela **confirmada**.
- `notebooks/02_exploratoria.ipynb` — Fase 2. **Sem poda**: nenhum par acima
  de |ρ| > 0,85.
- `requirements.txt`: `ipykernel` e `jupyterlab`.
- Painel da SSP agora é **mensal** (`ssp_painel.csv` ganhou a coluna `mes`).
  Mês é superconjunto barato: o `merge_bases.py` soma sobre ele sem saber que
  existe, e a série mensal da Fase 1 deixa de exigir reprocessar 4,8 M de
  linhas. Ocorrências sem `MES_ESTATISTICA` recebem `mes = 0` e continuam
  contando no total anual.
- `SPDadosCriminais_2022.xlsx` incorporado ao painel como série de controle.
  Conferido: **não altera `base_final.csv`** — o filtro `ANOS_JANELA` o exclui.

**Corrigido**

- **Espaços à direita em `CIDADE` (2022) inflavam o diagnóstico.** A taxa de
  "registro ≠ circunscrição" havia saltado de 0,3% para 2,0% ao incluir 2022.
  Não era o dado: o campo vem preenchido com espaços
  (`'S.PAULO                  '`) e a comparação crua contava isso como
  divergência. Com `strip()` nos dois lados, 2022 cai para 0,46%.
- Diagnóstico de circunscrição agora é **por ano**, e não no agregado — o
  painel cobre anos fora da janela de modelagem, e a taxa global misturava os
  dois.
- Apelidos de coluna para 2022: `CIDADE` (município de registro) e
  `DESCR_PERIODO`. Confirmados posicionalmente contra a aba
  `CAMPOS_DA_TABELA_SPDADOS`, que documenta os nomes canônicos em ordem.

**Documentado**

- README: seção de notebooks, aviso sobre o kernel, conclusões das Fases 1 e 2.
- Distinção que ia parar no artigo errada: **os "~60%" da METODOLOGIA da SSP
  não são comparáveis ao nosso 0,34%**. A SSP fala de *delegacia* de
  circunscrição — um BO feito em outra delegacia do mesmo município entra nos
  60% sem mudar de município. Os 60% justificam não usar a delegacia; o 0,34%
  é o erro real na unidade que interessa.

### [07/09/2026] Fase 0 — base construída

O pipeline não rodava: fora escrito contra o export de 2026 e **os nomes das
colunas da SSP mudam a cada ano**.

**Corrigido — os 6 bloqueios**

1. **`COD IBGE` → `CD_IBGE`.** Era a falha mais perigosa: como as abas de
   dados são descobertas pelo conteúdo do cabeçalho, o nome errado não gerava
   erro, gerava **painel vazio**. Toda coluna passou a ser resolvida por
   **lista de apelidos** (`APELIDOS_*` em `src/parse_ssp.py`) — o único lugar
   a mexer quando a SSP renomear algo.
2. **`DESCR_TIPOLOCAL` não existe em 2023 nem 2024.** Levantava `ValueError`.
   `prop_via_publica` passou a usar `DESCR_SUBTIPOLOCAL` em todos os anos:
   consistência ao longo da janela vale mais que casar com o TIPOLOCAL de
   2025, que criaria um degrau artificial na variável de validação externa.
3. **`ANO`/`MES` (2023–24) vs `ANO_REGISTRO_BO`/`MES_REGISTRO_BO` (2025)** em
   veículos e celulares — resolvido pelo mesmo mecanismo.
4. **IEGM: 3 exercícios, não 1.** `IEGM_RAW_PATH` apontava para um
   `ieg-m.xls` inexistente. Agora lê todos os `.xls` da pasta e se orienta
   pela coluna `exercicio_ref` — os nomes dos arquivos enganam
   (`ieg_m_2025.xls` é o exercício **2022**).
5. **`config.py`:** `ANOS_JANELA = [2023, 2024, 2025]` e
   `ANO_POPULACAO_REF = 2024`.
6. **`taxa_urbanizacao` viria do Censo 2010.** A tabela 202 do SIDRA é do
   Censo antigo e seus períodos param em 2010; `period="last"` devolvia 2010
   **sem erro nenhum** — 15 anos de defasagem numa das duas únicas features do
   bloco socioeconômico. Trocada pela tabela **9923** (Censo 2022, nível
   municipal).

**Alterado**

- IEGM: `*_ord` passou a ser a **média dos 3 exercícios** (2022–2024, apurados
  2023–2025 — a mesma janela do crime). Um exercício isolado tem 4–5 níveis
  muito concentrados: `i_planejamento` tinha 83% dos municípios em `C`. A
  média devolveu variância — de 4 níveis distintos para 10 nessa coluna.
  `*_conceito` guarda a letra do exercício mais recente, como rótulo.
- `ibge_sidra.py` rodou pela primeira vez (o docstring registrava que nunca
  fora executado). População fixada em 2024 — `period="last"` traria 2026.
- `merge_bases.py`: `.where(> 0)` no lugar de `.replace(0, pd.NA)`, que
  promovia colunas numéricas a `object` no pandas 3. Relatório ganhou o quadro
  de anos de referência por fonte.
- `parse_ssp.py` passou a **medir** duas coisas que antes eram suposição: a
  taxa de repetição de `(BO, natureza)` — porque a METODOLOGIA da SSP avisa
  que cada linha é uma pessoa/natureza/objeto — e as duas direções da junção
  por nome.

**Resultado**

`base_final.csv` com 645 × 49 e 19 features, validada por reconciliação exata
contra o painel e por comparação da taxa estadual de CVLI com a publicada.
