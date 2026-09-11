# Andamento — o que está pronto, o que falta e o que mudou

**Atualizado em:** 10/09/2026 · **Entrega:** 23/09/2026 (13 dias)

Este arquivo é o estado do projeto. O [README.md](README.md) explica como
rodar. O [PLANEJAMENTO.md](PLANEJAMENTO.md) foi escrito para a entrega de
16/09 com clusterização no escopo — **está desatualizado em prazo e escopo**;
o que vale é o que está aqui.

---

## 1. O escopo desta entrega mudou

A clusterização **saiu** desta entrega e vai para a próxima. Os *Resultados
Parciais* e a *Discussão e Conclusão* passam a ser sobre a **análise
exploratória e o pré-processamento**.

Consequência prática: **a Fase 3 deixou de ser preparação e virou o clímax
dos resultados.** O que seria uma etapa intermediária agora é a última peça
técnica do relatório, e por isso foi tratada como resultado — com comparação
de alternativas e figuras próprias, não como um passo administrativo.

| Seção | Máx. | Conteúdo nesta entrega |
|---|---:|---|
| Título e resumo | 1 p | título revisado; resumo com resultados parciais |
| Introdução | 2 p | ⚠ ponto a melhorar |
| Trabalhos correlatos | 3 p | ⚠ ponto a melhorar |
| Método | 2 p | aquisição, integração, exploratória, pré-processamento |
| Resultados parciais | 3 p | ⚠ ponto a melhorar — Fases 1, 2 e 3 |
| Discussão e conclusão | 1 p | o que a estrutura dos dados sugere + próximos passos |
| Referências | livre | — |

---

## 2. Onde estamos

| Fase | O que é | Situação |
|---|---|---|
| 0 | Completar as bases | ✅ concluída |
| 1 | Validar a janela temporal | ✅ concluída — janela **confirmada** |
| 2 | Exploratória e seleção de variáveis | ✅ concluída — **sem poda** |
| 3 | Pré-processamento | ✅ concluída — matriz exportada |
| 6 | Escrita conceitual (Introdução + Correlatos) | ⬜ **não começou** |
| 7 | Escrita de Método, Resultados e Discussão | ⬜ a fazer |
| 8 | Fechamento | ⬜ a fazer |
| 4 e 5 | Clusterização e perfis | ⏭ **próxima entrega** |

**Toda a Trilha A desta entrega está pronta.** O que falta é exclusivamente
texto — e o `artigo.tex` ainda não teve uma linha alterada: título antigo,
seção `Cronograma` presente, Método inteiro no futuro. São ~9 páginas a
escrever em 13 dias, sem nenhuma dependência de código.

---

## 3. O que está pronto

### 3.1 Base de dados

`data/processed/base_final.csv` — **645 municípios × 54 colunas**.
**22 features:** 9 criminalidade + 6 socioeconômico + 7 gestão. (Em 10/09
entraram quatro indicadores do Censo 2022 e saiu `iegm_ord`, que é composto
pelas 7 dimensões e contaria duas vezes.)

| Fonte | Ano de referência |
|---|---|
| Criminalidade (SSP-SP) | 2023–2025, exposição 3,000 anos |
| Gestão (IEGM/TCE-SP) | exercícios 2022–2024 (apurados 2023–2025), média |
| População (denominador) | 2024 |
| PIB (SIDRA 5938) | 2023 |
| Urbanização (SIDRA 9923) | Censo 2022 |
| Alfabetização, renda mediana, esgoto, lixo (SIDRA 9543, 10295, 6805, 6892) | Censo 2022 |

`data/processed/matriz_modelagem.csv` — **644 × 22**, já transformada,
padronizada e ponderada. É o insumo direto da clusterização da próxima
entrega.

### 3.2 Código

| Arquivo | O que faz |
|---|---|
| `main.py` | orquestra as 4 etapas de construção |
| `src/config.py` | caminhos, janela, tabelas do SIDRA, agrupamento de naturezas |
| `src/ibge_sidra.py` | baixa população, PIB, urbanização e 4 indicadores do Censo 2022 da API do SIDRA |
| `src/parse_ssp.py` | 4,8 M de linhas de microdado → painel mensal (streaming) |
| `src/parse_iegm.py` | 3 exercícios do IEGM → média ordinal por município |
| `src/merge_bases.py` | une tudo por `codigo_ibge` → base final + dicionário |
| `src/figuras.py` | uma função por figura do artigo; os notebooks só preparam o dado e chamam |
| `src/estilo.py` | estilo pronto do matplotlib e `salvar()` |
| `notebooks/01_validacao_temporal.ipynb` | Fase 1 |
| `notebooks/02_exploratoria.ipynb` | Fase 2, com seção 0 de primeiro contato com a base |
| `notebooks/03_preprocessamento.ipynb` | Fase 3, pipeline do `sklearn` (75 linhas de código) |
| `notebooks/03b_apendice_escalonadores.ipynb` | apêndice: por que `StandardScaler` |

### 3.3 Figuras e tabelas geradas

| Saída | Arquivo |
|---|---|
| **Figura 1** — série mensal 2022–2025 | `figuras/figura1_serie_mensal.png` |
| Figura 1b — série por natureza | `figuras/figura1b_serie_por_natureza.png` |
| **Figura 2** — correlação de Spearman | `figuras/figura2_spearman.png` |
| **Figura 3** — variância explicada do PCA | `figuras/figura3_variancia_pca.png` |
| Orçamento de distância por bloco | `figuras/figura_orcamento_blocos.png` |
| Distribuições antes/depois de `log1p` | `figuras/figura_distribuicoes_log1p.png` |
| Municípios em PC1 × PC2 | `figuras/figura_pc1_pc2.png` |
| EDA: população em escala log | `figuras/figura_eda_populacao.png` |
| EDA: boxplot das taxas | `figuras/figura_eda_boxplot_taxas.png` |
| **Tabela 2** — descritivas + zero-inflação | `data/processed/tabela2_descritivas.csv` |

São 9 figuras para 3 páginas de resultados — **mais do que cabe**. Escolher
quais entram é parte do trabalho de escrita (ver §4.2).

### 3.4 Números verificados — prontos para o artigo

Todos medidos, nenhum estimado.

**Volume e integridade**

- 4.792.830 linhas de microdado lidas (2022–2025); 3.594.857 na janela.
- Repetição de `(delegacia, ano_bo, num_bo, natureza)`: **0,01%** em 2023 e
  2024, 0,00% em 2025 — contar linhas é contar ocorrências, medido.
- Registro ≠ circunscrição: **0,37%** (2023), 0,34% (2024), 0,31% (2025).
- Dos 683 valores distintos de `NOME_MUNICIPIO`, **532 apontam para mais de um
  código IBGE**.

**Base**

- 645 municípios; **644** na modelagem (São Paulo fora: TCM-SP, sem IEGM).
- **149 municípios (23,1%)** com menos de 5.000 habitantes; mediana estadual
  13.399.
- Ausentes: só `taxa_recuperacao_veiculo` e `prop_veiculo_motocicleta`, em 44
  municípios (6,8%) sem veículo subtraído em 3 anos.
- População de SP em 2024: 45.973.194.

**Validação externa**

- **CVLI estadual: 6,0 por 100 mil/ano**, compatível com a taxa publicada.
  Capital em 4,6 — abaixo da média estadual, como se espera.
- `taxa × população × exposição` reconstrói o painel exatamente (8.298 CVLI,
  94.191 roubos de veículo).

**Fase 1 — janela confirmada**

- Sem degrau em jan/2023. Na virada 2022→2023, **5 naturezas sobem e 5
  descem**; variação mediana 6,2% contra 5,6% nas viradas seguintes.
- As únicas que destoam são `cvli` e `estupro_total` — as *menos* sensíveis ao
  sistema de registro, o oposto do que a hipótese de artefato previria.

**Fase 2 — features**

- Zero-inflação do CVLI: **20,3%**, abaixo dos ~23% projetados.
- Nenhum par com |ρ| > 0,85. Máximo **0,763** (`roubo_outros × roubo_veiculo`).
  Entre os novos indicadores, urbanização × lixo coletado chega a 0,74 e
  urbanização × esgoto a 0,67, abaixo do limiar. **As 22 features seguem
  inteiras.**
- `pib_percapita` × `renda_domiciliar_mediana`: ρ = 0,41. Medem coisas
  diferentes; o PIB fica, com o caveat dos enclaves para a Discussão.
- `log1p` mantido: a assimetria negativa que ele parece introduzir é
  zero-inflação, não excesso de correção. Sem os zeros, tudo cai para −0,5 a
  +0,7. Em `taxa_estupro_total`, **7 municípios** produzem assimetria −2,3.

**Fase 3 — pré-processamento**

- **`StandardScaler` no lugar de `RobustScaler`** (desvio do plano, ver §5).
  Só assim o peso `1/√n` entrega a paridade que promete: **33,3% para cada
  bloco**, contra 34/36/30 com `RobustScaler`.
- Com `RobustScaler`, `i_planejamento_ord` respondia sozinha pela segunda
  componente (carga **0,93**) — IQR de 0,333 (70% dos municípios no mesmo
  valor) fazia o escalonador multiplicá-la por três.
- Sem peso, o orçamento de distância é 40,9 / 27,3 / 31,8.
- **12 componentes para 80% da variância**, de 22. Não há estrutura de baixa
  dimensão.
- PC1 (24,6%) é um eixo de condição socioeconômica: alfabetização,
  urbanização, coleta de lixo, renda e esgoto, todos com carga positiva.
  PC2 (12,5%) opõe saúde e educação do IEGM às taxas de roubo. A nuvem
  PC1×PC2 é um **gradiente contínuo**, sem grupos naturalmente separados.
- O peso `1/√n` tem ancoragem: é a simplificação da ponderação por grupo da
  Análise Fatorial Múltipla (Escofier e Pagès, 1994). Entrada BibTeX no
  README.

---

## 4. O que falta produzir

**Só texto.** Nenhuma linha de código é necessária para esta entrega.

### 4.1 Ajustes estruturais no `artigo.tex`

- [ ] Aplicar o título revisado (com *"indicadores integrados de"*). O atual
      usa `relacionando-os a`, que descreve duas etapas — o oposto do desenho
      de etapa única.
- [ ] **Remover a seção `Cronograma`.**
- [ ] Renomear `Materiais e Métodos` → `Método`.
- [ ] Criar `Resultados Parciais` e `Discussão e Conclusão`.
- [ ] Atualizar resumo e *abstract*: hoje estão inteiramente no futuro, e
      precisam mencionar que há resultados parciais **e** que a clusterização
      é etapa seguinte.

### 4.2 Resultados Parciais (3 p) — seção nova

Há mais material do que espaço. Sugestão de corte, em ordem de valor:

| Entra | Elemento | Origem |
|---|---|---|
| ✅ | Tabela 1 — composição da base (fontes, n, cobertura, ausentes) | Fase 0 |
| ✅ | Figura 1 — série mensal e validação da janela | Fase 1 |
| ✅ | Tabela 2 — descritivas das taxas + zero-inflação | Fase 2 |
| ✅ | Figura 2 — correlação de Spearman | Fase 2 |
| ✅ | Figura 3 — variância explicada do PCA | Fase 3 |
| ⚠ | Orçamento por bloco — se sobrar espaço; senão vira texto | Fase 3 |
| ❌ | Distribuições `log1p`, PC1×PC2, série por natureza, figuras de EDA | apoio |

Os três achados que a seção precisa deixar claros:

1. A janela foi **testada**, não escolhida por conveniência.
2. Nenhuma feature foi podada — os blocos **não são redundantes**.
3. São necessárias 12 das 22 componentes para 80% da variância — **a
   integração das três fontes acrescenta informação**, e não repetição.

### 4.3 Método (2 p) — reescrever no passado

Incorporar o que hoje só existe no código e no README: janela e sua validação
empírica; junção por `codigo_ibge`; município de **circunscrição**; taxa por
100 mil habitantes-ano com população de 2024; CVLI; naturezas excluídas e por
quê; exclusão da capital; `log1p`, `StandardScaler` e peso por bloco.

### 4.4 Introdução (2 p) e Trabalhos Correlatos (3 p)

Sem dependência de dados — **é o que está travando a entrega**.

**Introdução:** dimensionar o problema com números (temos vários em §3.4);
**citar a literatura de desorganização social** — a linha 48 do tex invoca
essa literatura *sem nenhuma citação* (Shaw & McKay, Sampson); explicitar as
perguntas de pesquisa.

**Trabalhos Correlatos**, por custo-benefício: (1) promover `silva2025` e
`soliani2024`, já citados mas nunca discutidos na §2 — dois parágrafos sem
leitura nova; (2) **tabela comparativa** (`trabalho | recorte | fonte |
método | validação | integra gestão pública?`); (3) buscar 2 trabalhos novos.

### 4.5 Discussão e Conclusão (1 p) — seção nova

- O que a estrutura dos dados já sugere: os três blocos são complementares
  (Spearman e PCA, por caminhos independentes); a distribuição é um gradiente
  contínuo, não grupos separados.
- **Limitações declaradas de frente:** anos de referência heterogêneos;
  capital fora; 149 municípios abaixo de 5.000 habitantes; `taxa_trafico`
  medindo também intensidade de policiamento; `i_planejamento_ord` com 70% dos
  municípios no mesmo valor.
- **Próximos passos:** clusterização (K-means, hierárquico, DBSCAN) com
  comparação por métricas internas; análise de estabilidade por ARI; mapas
  coropléticos; encolhimento bayesiano das taxas.

---

## 5. Pendências e riscos

| Item | Situação |
|---|---|
| `.bib` e template SBC | Resolvido — está no Overleaf |
| **Introdução e Trabalhos Correlatos** | **Não começaram. 5 das ~9 páginas. Maior risco.** |
| Kernel dos notebooks | 4 Pythons na máquina; o que tem as bibliotecas é `C:\Python314\python.exe`. A 1ª célula imprime `sys.executable` |
| `StandardScaler` vs `RobustScaler` | Desvio do plano, com evidência no apêndice 03b. **Confirmem se concordam** — a decisão vale para a clusterização da próxima entrega |
| `pib_percapita` | Proxy ruim de renda (enclaves: Paulínia, Ilhabela, Louveira, Gavião Peixoto, Queiroz). Fica como feature porque ρ com a renda mediana é 0,41; **caveat obrigatório na Discussão** |
| `taxa_trafico` | Mede também intensidade de policiamento; caveat na Discussão |
| `i_planejamento_ord` | 70% dos municípios no mesmo valor. Mantida, mas pede sensibilidade com e sem ela na próxima entrega |
| `*_conceito` ≠ `*_ord` | Por construção: `_ord` é a média dos 3 exercícios, `_conceito` é a letra do mais recente. Campinas: `B` e `1,667` |

**Calendário sugerido**

| Dias | O quê |
|---|---|
| 08–14/09 | Introdução e Trabalhos Correlatos (as 5 páginas travadas) |
| 12–17/09 | Método reescrito no passado |
| 15–20/09 | Resultados Parciais e Discussão |
| 20–22/09 | Revisão cruzada, contagem de páginas, figuras em cinza |
| 23/09 | Submissão — **não deixar para as 23h** |

---

## 6. Changelog

### [10/09/2026] Revisão cruzada com o artigo — base e notebooks

Implementa as nove tarefas de `REVISAO_BASE_E_NOTEBOOKS.md`. Regra adotada
em todo o código: cada célula tem que ser explicável em duas frases por
qualquer membro do grupo; o que não é, vai para função em `src/` ou para
apêndice.

**Base**

- **Bloco socioeconômico de 2 para 6 features.** Entraram, do Censo 2022 e
  em nível municipal: `taxa_alfabetizacao` (SIDRA 9543), `renda_domiciliar_mediana`
  (10295, mediana e não média, por causa dos enclaves), `prop_esgoto_adequado`
  (6805) e `prop_lixo_coletado` (6892). Nenhum ausente nos 645 municípios.
  Números de tabela, variável e categoria conferidos na API de metadados e
  comentados em `config.py`.
- **`iegm_ord` saiu das features** (papel `contexto`). É composto pelas 7
  dimensões; ρ = 0,86 com a média delas. Ficam as dimensões, que dizem em
  qual área de gestão os perfis diferem. Gestão: 8 → 7 features.
- **`pib_percapita` reavaliado.** Fica como feature por regra automática no
  `merge_bases.py`: sairia se ρ com a renda mediana passasse de
  `LIMIAR_REDUNDANCIA` (0,85); mediu 0,41.
- **Dicionário corrigido, com números recalculados a cada execução:**
  `taxa_recuperacao_veiculo` vira `contexto` e a descrição diz que a razão
  passa de 1 em 477 de 601 municípios porque inclui veículos subtraídos em
  outros municípios — não mede efetividade; `prop_noturno` e
  `cobertura_periodo` trazem a cobertura real da janela (mediana 20%), no
  lugar do "~42% em 2026".
- Base final: 645 × **54** colunas; **22** features (9 + 6 + 7). Pesos:
  0,333 / 0,408 / 0,378.

**Notebooks**

- `src/figuras.py`, novo: uma função por figura, com docstring dizendo o
  que a figura mostra. Nos notebooks, célula de figura = preparar dado +
  chamar + `salvar`. Nenhum `ax.text` posicionado à mão em notebook.
- `src/estilo.py` reduzido a `plt.style.use("seaborn-v0_8-whitegrid")`,
  `rcParams` mínimos e `salvar()`. Cores: `RdBu`, `Blues`, `C0`/`C1`. A
  discussão de ΔE/daltonismo saiu do código.
- `02_exploratoria` ganhou a **seção 0 de primeiro contato**: `info()`,
  ausentes, `describe()` por bloco, histograma da população em log,
  boxplots das taxas, top-10 de CVLI e de roubo, distribuição das notas do
  IEGM. Só depois vêm Tabela 2, `log1p` e Spearman.
- `03_preprocessamento` reescrito com `ColumnTransformer` + `Pipeline` do
  `sklearn`: 75 linhas de código. Conferido com `assert_frame_equal` que a
  matriz é idêntica ao cálculo manual.
- `03b_apendice_escalonadores`, novo: a comparação A/B/C que justifica o
  `StandardScaler`, fora do pipeline.
- Seleção das taxas criminais passou a ser pelo bloco do dicionário, não
  pelo prefixo `taxa_` — que agora também casaria com `taxa_alfabetizacao`.

**Números que mudaram (22 features)**

- Spearman: continua sem par acima de 0,85; máximo 0,763.
- Orçamento sem peso: 40,9 / 27,3 / 31,8 (era 47,4 / 10,5 / 42,1).
- Componentes para 80%: **12** de 22 (era 9 de 19). PC1: 24,6% (era 27,5%).
- `RobustScaler`: PC2 dominada por `i_planejamento_ord` com carga 0,93.

**Documentação**

- Peso `1/√n` ancorado na Análise Fatorial Múltipla (Escofier e Pagès,
  1994), com a diferença explicada e entrada BibTeX no README.
- README lista os indicadores do IBGE em tabela, com tabela SIDRA e ano.

**Removido**

- `src/__pycache__/` e `data/processed/.gitkeep` (a pasta tem arquivos
  versionados).

### [07/09/2026] Fase 3 — pré-processamento, e uma decisão revista

**Adicionado**

- `notebooks/03_preprocessamento.ipynb` — Fase 3.
- `data/processed/matriz_modelagem.csv` (644 × 19), insumo direto da
  clusterização.
- `src/estilo.py`: rampa sequencial de um matiz só (`CMAP_SEQUENCIAL`), que é
  a única que sobrevive à impressão em cinza, porque a informação fica na
  luminosidade e não no matiz.
- Figuras: variância do PCA, orçamento por bloco, PC1×PC2.

**Alterado — `RobustScaler` → `StandardScaler`**

Desvio deliberado do plano, com a evidência no notebook. O peso `1/√n` é
deduzido supondo que **cada coluna padronizada contribua com uma unidade de
variância**. `RobustScaler` normaliza o intervalo interquartil, não a
variância — então a suposição não vale e o peso não entrega o que promete:

- Com `RobustScaler`: blocos em 37 / 33 / 30, e a PC2 (15% da variância) era
  **uma variável só** — `i_planejamento_ord`, carga 0,88. O IQR dela é 0,333
  porque 70% dos municípios estão no mesmo valor; dividir por 0,333 multiplica
  a coluna por três. O escalonador amplificava justamente a variável com menos
  informação.
- Com `StandardScaler`: blocos em **33,3 / 33,3 / 33,3** — exatamente a
  paridade pretendida — e a maior carga da PC2 cai de 0,88 para 0,38.

O motivo original de usar `RobustScaler` era conter valores extremos. Mas isso
quem faz é o `log1p`, e a Fase 2 mostrou que ele já deixa a assimetria entre
−0,5 e +0,7. Aplicar `RobustScaler` em cima disso não protegia de nada e
quebrava a equalização.

Também foi testado preservar a escala teórica 1–5 nas ordinais: derruba o
bloco de gestão para **2,3%** do orçamento. Descartado — esvaziar a gestão
contradiz a contribuição que o artigo reivindica.

**Escopo**

- Clusterização e caracterização de perfis movidas para a entrega seguinte.
- Prazo atualizado para 23/09/2026.

### [07/09/2026] Fases 1 e 2 — análise em notebook

**Adicionado**

- `src/estilo.py`: paleta e `rcParams` comuns às figuras. As cores passaram em
  teste de separação para daltonismo e contraste (ΔE protan 24,7; mínimo 8) em
  vez de serem escolhidas a olho.
- `notebooks/01_validacao_temporal.ipynb` — janela **confirmada**.
- `notebooks/02_exploratoria.ipynb` — **sem poda**.
- `requirements.txt`: `ipykernel` e `jupyterlab`.
- Painel da SSP agora é **mensal**. Mês é superconjunto barato: o
  `merge_bases.py` soma sobre ele sem saber que existe, e a série mensal da
  Fase 1 deixa de exigir reprocessar 4,8 M de linhas. Ocorrências sem
  `MES_ESTATISTICA` recebem `mes = 0` e continuam contando no total anual.
- `SPDadosCriminais_2022.xlsx` incorporado como série de controle. Conferido:
  **não altera `base_final.csv`** — o filtro `ANOS_JANELA` o exclui.

**Corrigido**

- **Espaços à direita em `CIDADE` (2022) inflavam o diagnóstico.** A taxa de
  "registro ≠ circunscrição" havia saltado de 0,3% para 2,0% ao incluir 2022.
  Não era o dado: o campo vem preenchido com espaços e a comparação crua
  contava isso como divergência. Com `strip()` nos dois lados, 2022 cai para
  0,46%.
- Diagnóstico de circunscrição agora é **por ano**, não no agregado.
- Apelidos de coluna para 2022: `CIDADE` e `DESCR_PERIODO`, confirmados
  posicionalmente contra a aba `CAMPOS_DA_TABELA_SPDADOS`.

**Documentado**

- **Os "~60%" da METODOLOGIA da SSP não são comparáveis ao nosso 0,34%.** A
  SSP fala de *delegacia* de circunscrição — um BO feito em outra delegacia do
  mesmo município entra nos 60% sem mudar de município. Os 60% justificam não
  usar a delegacia; o 0,34% é o erro real na unidade que interessa.

### [07/09/2026] Fase 0 — base construída

O pipeline não rodava: fora escrito contra o export de 2026 e **os nomes das
colunas da SSP mudam a cada ano**.

**Corrigido — os 6 bloqueios**

1. **`COD IBGE` → `CD_IBGE`.** A falha mais perigosa: como as abas de dados
   são descobertas pelo conteúdo do cabeçalho, o nome errado não gerava erro,
   gerava **painel vazio**. Toda coluna passou a ser resolvida por **lista de
   apelidos** (`APELIDOS_*` em `src/parse_ssp.py`).
2. **`DESCR_TIPOLOCAL` não existe em 2023 nem 2024.** `prop_via_publica`
   passou a usar `DESCR_SUBTIPOLOCAL` em todos os anos: consistência ao longo
   da janela vale mais que casar com o TIPOLOCAL de 2025, que criaria um
   degrau artificial na variável de validação externa.
3. **`ANO`/`MES` (2023–24) vs `ANO_REGISTRO_BO`/`MES_REGISTRO_BO` (2025)** em
   veículos e celulares.
4. **IEGM: 3 exercícios, não 1.** Agora lê todos os `.xls` da pasta e se
   orienta pela coluna `exercicio_ref` — os nomes dos arquivos enganam
   (`ieg_m_2025.xls` é o exercício **2022**).
5. **`config.py`:** `ANOS_JANELA = [2023, 2024, 2025]` e
   `ANO_POPULACAO_REF = 2024`.
6. **`taxa_urbanizacao` viria do Censo 2010.** A tabela 202 do SIDRA é do
   Censo antigo e seus períodos param em 2010; `period="last"` devolvia 2010
   **sem erro nenhum**. Trocada pela tabela **9923** (Censo 2022).

**Alterado**

- IEGM: `*_ord` passou a ser a **média dos 3 exercícios** (2022–2024, apurados
  2023–2025 — a mesma janela do crime). `i_planejamento` foi de 4 níveis
  distintos para 10. `*_conceito` guarda a letra do exercício mais recente.
- `ibge_sidra.py` rodou pela primeira vez (o docstring registrava que nunca
  fora executado). População fixada em 2024 — `period="last"` traria 2026.
- `merge_bases.py`: `.where(> 0)` no lugar de `.replace(0, pd.NA)`, que
  promovia colunas numéricas a `object` no pandas 3.
- `parse_ssp.py` passou a **medir** o que antes era suposição: a taxa de
  repetição de `(BO, natureza)` e as duas direções da junção por nome.

**Resultado**

`base_final.csv` com 645 × 49 e 19 features, validada por reconciliação exata
contra o painel e por comparação da taxa estadual de CVLI com a publicada.
