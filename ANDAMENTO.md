# Andamento — o que está pronto, o que falta e o que mudou

**Atualizado em:** 07/10/2026 · **Entrega:** 21/10/2026, 23:59 — relatório
parcial + vídeo (14 dias)

Este arquivo é o estado do projeto. O [README.md](README.md) explica como
rodar. O [PLANEJAMENTO.md](PLANEJAMENTO.md) foi escrito para a entrega de
16/09 e **está desatualizado**; o que vale é o que está aqui.

---

## 1. Escopo da entrega de 21/10

Esta entrega responde às perguntas (ii) e (iii) do artigo; a (i) foi
respondida na entrega de 23/09.

- **(ii) Qual algoritmo?** K-means, Ward e DBSCAN comparados por qualidade
  (silhueta, Calinski–Harabasz, Davies–Bouldin) e por estabilidade (ARI entre
  subjanelas, sem os municípios pequenos e entre sementes), com uma regra de
  decisão definida antes dos testes. Escolha do grupo: **K-means com k = 4**.
- **(iii) Que perfis?** Quatro perfis caracterizados por mapa de calor,
  medianas, municípios típicos, validação externa (Kruskal–Wallis com ε²) e
  mapa.

No `artigo.tex` (pasta do Overleaf), o resumo, o *abstract*, o fim da
Introdução, a seção 3.3 do Método, duas subseções novas dos Resultados
(Comparação dos algoritmos e Perfis) e a Discussão inteira foram reescritos
em 07/10 e estão **em vermelho**, para revisão do grupo.

---

## 2. Onde estamos

| Fase | O que é | Situação |
|---|---|---|
| 0 | Completar as bases | ✅ concluída |
| 1 | Validar a janela temporal | ✅ concluída — janela **confirmada** |
| 2 | Exploratória e seleção de variáveis | ✅ concluída — **sem poda** |
| 3 | Pré-processamento | ✅ concluída — matriz exportada |
| 4 | Clusterização e escolha do modelo | ✅ concluída — **K-means, k = 4** (notebooks 04 e 05) |
| 5 | Perfis, validação externa e mapa | ✅ concluída (notebooks 06 e 07) |
| — | Sensibilidade a 3 variáveis (T5, opcional) | ⬜ não feita — está nos próximos passos do artigo |
| 6 e 7 | Escrita do artigo | 🟨 texto novo em vermelho, **a revisar pelo grupo** |
| 8 | Fechamento | ⬜ a fazer: nomes dos perfis, citações, páginas, vídeo |

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
padronizada e ponderada. É o insumo dos notebooks 04 a 07.

### 3.2 Código

| Arquivo | O que faz |
|---|---|
| `main.py` | orquestra as 4 etapas de construção |
| `src/config.py` | caminhos, janela, tabelas do SIDRA, agrupamento de naturezas, parâmetros da clusterização e o modelo escolhido |
| `src/ibge_sidra.py` | baixa população, PIB, urbanização e 4 indicadores do Censo 2022 da API do SIDRA |
| `src/parse_ssp.py` | 4,8 M de linhas de microdado → painel mensal (streaming) |
| `src/parse_iegm.py` | 3 exercícios do IEGM → média ordinal por município |
| `src/merge_bases.py` | une tudo por `codigo_ibge` → base final + dicionário |
| `src/preprocessamento.py` | `log1p`, padronização e peso por bloco em forma de função (usado nos testes de estabilidade) |
| `src/clusterizacao.py` | agrupamento, métricas, ARI de estabilidade e Kruskal–Wallis com ε² |
| `src/malha.py` | malha municipal do IBGE para os mapas |
| `src/figuras.py` | uma função por figura do artigo; os notebooks só preparam o dado e chamam |
| `src/estilo.py` | estilo pronto do matplotlib e `salvar()` |
| `notebooks/01_validacao_temporal.ipynb` | Fase 1 |
| `notebooks/02_exploratoria.ipynb` | Fase 2, com seção 0 de primeiro contato com a base |
| `notebooks/03_preprocessamento.ipynb` | Fase 3, pipeline do `sklearn` |
| `notebooks/03b_apendice_escalonadores.ipynb` | apêndice: por que `StandardScaler` |
| `notebooks/04_clusterizacao.ipynb` | Fase 4: K-means, Ward e DBSCAN (só mede) |
| `notebooks/05_estabilidade_escolha.ipynb` | Fase 4: estabilidade, regra de decisão, justificativa e `perfis.csv` |
| `notebooks/06_perfis.ipynb` | Fase 5: perfis, Figura 5 e tabelas |
| `notebooks/07_validacao_externa_mapa.ipynb` | Fase 5: validação externa e Figura 6 |

Ambiente: os notebooks 04 a 07 rodam com Python 3.14 em `.venv` (ver README).

### 3.3 Figuras e tabelas geradas

| Saída | Arquivo |
|---|---|
| **Figura 1** — série mensal 2022–2025 | `figuras/figura1_serie_mensal.png` |
| **Figura 2** — correlação de Spearman | `figuras/figura2_spearman.png` |
| **Figura 3** — variância explicada do PCA | `figuras/figura3_variancia_pca.png` |
| **Figura 4** — seleção de k (K-means e Ward) | `figuras/figura4_selecao_k.png` |
| **Figura 5** — perfis em relação à média | `figuras/figura5_perfis.png` |
| **Figura 6** — mapa dos perfis | `figuras/figura6_mapa_perfis.png` |
| Apoio: série por natureza, EDA, `log1p`, orçamento por bloco, PC1 × PC2 | `figuras/figura1b_*`, `figura_eda_*`, `figura_distribuicoes_log1p`, `figura_orcamento_blocos`, `figura_pc1_pc2` |
| Apoio: dendrograma, k-distância, via pública por perfil | `figuras/figura_dendrograma`, `figura_k_distancia`, `figura_via_publica_perfis` |
| Descritivas das taxas | `data/processed/tabela2_descritivas.csv` |
| Comparação dos algoritmos | `data/processed/tabela_comparacao_algoritmos.csv` |
| Perfis: medianas e exemplos | `data/processed/tabela_perfis.csv`, `tabela_exemplos_perfis.csv` |
| Kruskal–Wallis e ε² | `data/processed/tabela_kruskal.csv` |

### 3.4 Números verificados — prontos para o artigo

Todos medidos, nenhum estimado. Entre parênteses, de onde cada grupo de
números foi copiado.

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

**Conferência da base**

- **CVLI estadual: 6,0 por 100 mil/ano**, compatível com a taxa publicada.
  Capital em 4,6 — abaixo da média estadual, como se espera.
- `taxa × população × exposição` reconstrói o painel exatamente (8.298 CVLI,
  94.191 roubos de veículo).

**Fase 1 — janela confirmada**

- Sem degrau em jan/2023. Na virada 2022→2023, **5 naturezas sobem e 5
  descem**; variação mediana 6,2% contra 5,8% nas viradas seguintes (saída do
  notebook 01).
- As únicas que destoam são `cvli` e `estupro_total` — as *menos* sensíveis ao
  sistema de registro, o oposto do que a hipótese de artefato previria.

**Fase 2 — features**

- Zero-inflação do CVLI: **20,3%**.
- Nenhum par com |ρ| > 0,85. Máximo **0,763** (`roubo_outros × roubo_veiculo`).
  **As 22 features seguem inteiras.**
- `pib_percapita` × `renda_domiciliar_mediana`: ρ = 0,41.
- `log1p` mantido: a assimetria negativa que ele parece introduzir é
  zero-inflação, não excesso de correção. Sem os zeros, tudo cai para −0,5 a
  +0,7.

**Fase 3 — pré-processamento**

- `StandardScaler` no lugar de `RobustScaler`: só assim o peso `1/√n` entrega
  **33,3% para cada bloco**. Sem peso, o orçamento é 40,9 / 27,3 / 31,8.
- **12 componentes para 80% da variância**, de 22. PC1 (24,6%) é um eixo
  socioeconômico; PC2 (12,5%) opõe saúde e educação do IEGM às taxas de
  roubo. A nuvem PC1 × PC2 é um **gradiente contínuo**.

**Fase 4 — clusterização e escolha** (`metricas_clusterizacao.csv`,
`dbscan_grade.csv`, `tabela_comparacao_algoritmos.csv` e saídas dos notebooks
04 e 05)

- Silhueta máxima **0,136** (K-means, k = 2); nenhuma partição chega a 0,25.
  Silhueta e Calinski–Harabasz caem com k nos dois algoritmos; o K-means
  supera o Ward em ambas para todo k.
- Menor grupo abaixo de 5% a partir de k = 7 no K-means e k = 8 no Ward.
- **DBSCAN: 1 grupo nas 14 configurações** (`min_pts` 13 e 24), ruído de 0,3%
  a 23,8%. Excluído no passo 1 da regra.
- Sem os municípios pequenos ficam **495** municípios.
- `ari_estabilidade`: K-means de 0,447 a 0,850; Ward de 0,311 a 0,477.
- Divisão mais robusta: K-means k = 2 (**0,850**).
- Perfis: K-means k = 4 (**0,761**) e k = 3 (0,743) empatados; o grupo
  escolheu **k = 4**. Sementes: ARI médio **0,929** em k = 4 e 0,451 em
  k = 3. Silhueta 0,101 (k = 4) e 0,129 (k = 3).
- k = 4, ARI por teste: 0,891 (2023–2024), 0,912 (2024–2025), **0,480** (sem
  os pequenos, o teste mais exigente).
- k = 3 × k = 4: o grupo 3 do k = 3 recebe 119 municípios do perfil 3 e 159
  do perfil 4; perfis 1 e 2 se mantêm (65 de 66, 214 de 217).

**Fase 5 — perfis** (`perfis.csv`, `tabela_perfis.csv`, `tabela_kruskal.csv`
e saídas dos notebooks 06 e 07)

- Tamanhos dos perfis 1 a 4: **66, 217, 196 e 165**. Municípios com menos de
  5.000 habitantes: 25,8%, 53,5%, 4,6% e 4,2%.
- Roubo mediano (por 100 mil/ano): 26,0, 10,3, 46,2 e 51,4 (total 27,9).
  Renda mediana: R$ 942, R$ 1.200, R$ 1.175 e R$ 1.258 (total R$ 1.200).
- Perfil 4 − perfil 3 (desvios): de 1,05 a 1,32 em cinco dimensões do IEGM,
  0,91 na renda e quase zero nas taxas de roubo e furto.
- **Validação externa: ε² = 0,356** na `prop_via_publica` (H = 229,2;
  p = 2,0 × 10⁻⁴⁹), relativamente forte. Medianas de 33,1%, 30,0%, 41,3% e
  48,4%. **Ressalva:** ρ de 0,68 com a taxa de roubo e de 0,60 a 0,65 com
  furto e roubo de veículo, lixo, alfabetização e urbanização.
- ε² das features: alfabetização 0,494, urbanização 0,490, roubo 0,428;
  CVLI 0,057, tentativa de homicídio 0,030, planejamento 0,035.
- Malha: 645 polígonos; 644 municípios com perfil e a capital sem perfil.

---

## 4. O que falta

- [ ] **Revisar todo o texto em vermelho do artigo** e reescrever no estilo do
      grupo. Quando terminar, trocar no preâmbulo `\textcolor{red}{#1}` por
      `#1` e `\color{red}` por nada (ou apagar as marcações).
- [ ] **Resolver os 4 `[CITAÇÃO?]`**: Davies–Bouldin; regra do `min_pts`
      (d + 1 e 2d); ARI; faixas do ε² (0,04 / 0,16 / 0,36 / 0,64).
- [ ] **Dar nome aos 4 perfis** e usar os nomes no texto e nas figuras.
- [ ] **Conferir o teto de páginas** desta entrega: os Resultados ganharam
      duas figuras, duas tabelas e o mapa.
- [ ] Frase antiga ainda no futuro, na Análise exploratória: "o efeito dos
      zeros será avaliado na análise de sensibilidade" — não foi feito.
- [ ] Vídeo.
- [ ] (Opcional) T5 — sensibilidade a `taxa_trafico`, `pib_percapita` e
      `i_planejamento_ord`.

---

## 5. Pendências e riscos

| Item | Situação |
|---|---|
| Validação externa parcialmente circular | `prop_via_publica` correlaciona 0,68 com o roubo. Declarado no notebook 07 e na Discussão; não trocar a variável depois de ver o resultado |
| Municípios pequenos | Retirá-los é o teste de estabilidade mais exigente (ARI 0,480 em k = 4); declarado nas limitações |
| `pib_percapita`, `taxa_trafico`, `i_planejamento_ord` | Caveats na Discussão; sensibilidade (T5) não feita, ficou como próximo passo |
| Python | Em uma das máquinas do grupo, `C:\Python314` não existe; nela, usar `.venv` (Python 3.14.7). A 1ª célula de cada notebook imprime `sys.executable` |
| `*_conceito` ≠ `*_ord` | Por construção: `_ord` é a média dos 3 exercícios, `_conceito` é a letra do mais recente |

**Calendário sugerido**

| Dias | O quê |
|---|---|
| 08–11/10 | Nomes dos perfis; revisão do texto em vermelho; citações |
| 12–15/10 | Contagem de páginas e cortes; (opcional) T5 |
| 16–19/10 | Roteiro e gravação do vídeo |
| 20/10 | Revisão final e remoção das marcações em vermelho |
| 21/10 | Submissão — **não deixar para as 23h** |

---

## 6. Changelog

### [07/10/2026] T6 — README e ANDAMENTO

**Alterado**

- `README.md`: notebooks 04 a 07 (seção 3.2), saídas novas em
  `data/processed/` e em `figuras/` (seções 4.1 e 4.2), `preprocessamento.py`,
  `clusterizacao.py`, `malha.py` e a malha em `data/raw/ibge/` (seção 5), e
  nota sobre o Python 3.14 em `.venv`.
- `ANDAMENTO.md`: seções 1 a 5 reescritas para a entrega de 21/10, com os
  números da clusterização e dos perfis copiados dos CSVs e das saídas dos
  notebooks 04 a 07.

**Corrigido**

- Variação mediana das viradas seguintes à de 2022→2023: **5,8%** (saída do
  notebook 01 e artigo), e não 5,6%.

**Conferido**

- `requirements.txt` cobre todos os imports dos notebooks e de `src/`; o
  `numpy` não está listado, mas é instalado junto com o `pandas`.

### [07/10/2026] T4b parte 2 — validação externa e mapa dos perfis

**Adicionado**

- `notebooks/07_validacao_externa_mapa.ipynb`, seções 1 a 4: Kruskal–Wallis
  e ε² da `prop_via_publica` (com boxplot), ε² das 22 features (descritivo),
  Figura 6 e leitura do mapa, com `assert` conferindo o perfil de cada
  município citado no texto.
- `src/clusterizacao.py`: `kruskal_epsilon2` e `faixa_epsilon2`.
- `src/figuras.py`: `plot_boxplot_perfis`.
- `src/config.py`: `FAIXAS_EPSILON2` (fraco, moderado, relativamente forte,
  forte e, acima de 0,64, muito forte).
- `figuras/figura6_mapa_perfis.png`, `figuras/figura_via_publica_perfis.png`
  e `data/processed/tabela_kruskal.csv` (23 linhas).
- `notebooks/05_estabilidade_escolha.ipynb`, seção 7: tabela cruzada entre
  o K-means com k = 3 e os perfis escolhidos e a justificativa da escolha de
  k = 4 (passo 5 da regra).

**Números**

- `prop_via_publica`: H = 229,2, p = 2,0 × 10⁻⁴⁹, **ε² = 0,356**
  (relativamente forte). Mediana de 33,1%, 30,0%, 41,3% e 48,4% nos perfis
  1 a 4.
- **Ressalva:** a `prop_via_publica` tem correlação de Spearman de 0,68 com
  a taxa de roubo de outros e de 0,60 a 0,65 com furto de veículo, coleta de
  lixo, roubo de veículo, alfabetização e urbanização. A validação é
  parcialmente circular e isso precisa constar no artigo.
- ε² das features: maiores em alfabetização (0,494) e urbanização (0,490);
  sete com efeito forte, dos três blocos. Crimes contra a pessoa entre 0,030
  e 0,090; planejamento do IEGM 0,035.
- Mapa: perfil 1 no Vale do Ribeira, região de Itapeva e extremo leste;
  perfil 2 no oeste e noroeste; perfil 3 na periferia da Grande São Paulo,
  no litoral e em cidades médias do Vale do Paraíba; perfil 4 nos polos
  regionais e no núcleo da Grande São Paulo.

### [07/10/2026] T4a — notebook 06, perfis

**Adicionado**

- `notebooks/06_perfis.ipynb`: tamanho dos perfis e tabela cruzada com a
  `divisao_k2`, Figura 5, medianas em unidades originais, municípios típicos
  e mais populosos, e uma leitura por perfil (sem nome; `Nome: [a definir
  pelo grupo]`).
- `src/figuras.py`, seção "Fase 5 - perfis": `plot_perfis` (Figura 5).
- `figuras/figura5_perfis.png`, `data/processed/tabela_perfis.csv` e
  `data/processed/tabela_exemplos_perfis.csv`.

**Alterado**

- `src/config.py`: o grupo preencheu `ALGORITMO_ESCOLHIDO = "kmeans"` e
  `K_ESCOLHIDO = 4`. O notebook 05 rodou de novo e gerou
  `data/processed/perfis.csv`.

**Números**

- Perfis 1 a 4 (em ordem crescente de condição socioeconômica): 66, 217,
  196 e 165 municípios.
- População mediana: 8.444, 4.706, 22.575,5 e 53.157; municípios com menos
  de 5.000 habitantes: 25,8%, 53,5%, 4,6% e 4,2%.
- Divisão em dois grupos (`divisao_k2`): perfis 1 e 2 no grupo 1 (66 de 66
  e 211 de 217), perfil 4 no grupo 2 (164 de 165) e perfil 3 dividido (64 e
  132).

### [07/10/2026] T4b parte 1 — malha municipal e mapa de teste

**Adicionado**

- `src/malha.py` com `carregar_malha_sp()`: baixa a malha dos municípios
  paulistas da API de malhas do IBGE (código do município na propriedade
  `codarea`, conferido na resposta real) e guarda em
  `data/raw/ibge/malha_sp_municipios.geojson`, fora do Git. Nas execuções
  seguintes lê do disco. Se a API falhar, usa o shapefile municipal de 2022
  do geoftp do IBGE (coluna `CD_MUN`, também conferida).
- `src/figuras.py`, seção "Fase 5 - perfis": `plot_mapa_categorias`, que
  será a Figura 6. Tons de `Blues` em ordem (sem as pontas quase brancas) e
  hachura para os municípios sem perfil (a capital).
- `notebooks/07_validacao_externa_mapa.ipynb`: abertura e seção 0, com o
  `assert` dos 645 códigos e o mapa de teste da urbanização em quartis (não
  salvo). As seções 1 a 4 dependem do `perfis.csv`.

**Números**

- Malha: 645 polígonos; os 645 municípios da base encontrados.
- Ambiente novo (`.venv`, Python 3.14.7, pandas 3.0.6, scikit-learn 1.9.1,
  geopandas 1.2.0) reproduz os notebooks 04 e 05 sem mudar nenhum CSV ou
  figura.

### [02/10/2026] T3 — notebook 05, estabilidade e regra de decisão

**Adicionado**

- `notebooks/05_estabilidade_escolha.ipynb`: os três testes de
  estabilidade (subjanelas 2023–2024 e 2024–2025, sem os municípios
  pequenos, sementes do K-means), a tabela de comparação e a regra de
  decisão de 02/10 (passos 1 a 4b) aplicada passo a passo. Só sugere; a
  seção 7 não salva nada enquanto a escolha estiver pendente.
- `src/clusterizacao.py`: `ari_sementes`, `matriz_subjanela`,
  `ari_subjanela`, `ari_sem_pequenos`, `marcar_qualidade` (passo 3),
  `renumerar_por_socioeconomico` e `distancia_ao_centro`. A matriz de cada
  subjanela é montada uma vez por `matriz_subjanela` e reaproveitada, por
  isso `ari_subjanela` recebe a matriz pronta em vez dos dados brutos.
- `data/processed/tabela_comparacao_algoritmos.csv` (18 partições + 1 linha
  de resumo do DBSCAN, com a coluna `observacao`).

**Alterado**

- `src/config.py`: `ALGORITMO_ESCOLHIDO` e `K_ESCOLHIDO` (vazios),
  `SUBJANELAS`, `RUIDO_MAXIMO_DBSCAN`, `N_MELHORES_QUALIDADE`,
  `TOLERANCIA_ARI`, `K_MIN_PERFIS` e `N_SEMENTES`.
- `src/preprocessamento.py`: a conta da exposição virou a função
  `exposicao_da_janela`, usada no `assert` de 2,0 anos das subjanelas. O
  resultado de `taxas_da_janela` não muda.

**Números**

- Sem os municípios pequenos ficam 495 municípios.
- `ari_estabilidade`: K-means de 0,447 a 0,850; Ward de 0,311 a 0,477.
- Regra: DBSCAN fora no passo 1; 11 partições passam no tamanho; 6 na
  qualidade (k = 2, 3 e 4 nos dois algoritmos).
- Divisão mais robusta (4b): K-means k = 2, `ari_estabilidade` 0,850.
- Perfis (k ≥ 3): K-means k = 4 (0,761) e k = 3 (0,743) empatados
  (diferença 0,018 < 0,05). Escolha pendente para a reunião de 07/10.
- Sementes: ARI médio 0,929 em k = 4 e 0,451 em k = 3.

### [02/10/2026] T2 — notebook 04, três algoritmos

**Adicionado**

- `notebooks/04_clusterizacao.ipynb`: K-means e Ward para k de 2 a 10 e
  DBSCAN sobre as 12 componentes do PCA. Só mede; a escolha fica para o
  notebook 05.
- `src/clusterizacao.py`: `agrupar`, `soma_quadrados_interna`,
  `metricas_por_k`, `componentes_pca`, `distancia_k_vizinho` e
  `grade_dbscan`.
- `src/figuras.py`, seção "Fase 4": `plot_selecao_k` (Figura 4),
  `plot_k_distancia` e `plot_dendrograma`.
- `data/processed/metricas_clusterizacao.csv` (18 linhas) e
  `data/processed/dbscan_grade.csv` (14 linhas; além das colunas pedidas,
  traz o `quantil` que gerou cada `eps`).
- Figuras: `figura4_selecao_k`, `figura_dendrograma`, `figura_k_distancia`.

**Alterado**

- `src/config.py`: seção "Clusterização" com `RANDOM_STATE`, `N_INIT`,
  `K_MIN`, `K_MAX`, `TAMANHO_MINIMO_GRUPO`, `VARIANCIA_PCA_DBSCAN` e
  `QUANTIS_EPS_DBSCAN`.

**Números**

- Silhueta máxima: 0,136 (K-means, k = 2); Ward: 0,114 (k = 2). Todas
  abaixo de 0,25, coerente com a nuvem contínua do notebook 03.
- Calinski–Harabasz máximo em k = 2 nos dois (119,0 e 100,5);
  Davies–Bouldin mínimo em k = 4 no K-means (2,169) e k = 10 no Ward
  (2,236, com um grupo de 4 municípios).
- Menor grupo abaixo de 5% a partir de k = 7 no K-means e k = 8 no Ward.
- DBSCAN: 1 grupo em todas as 14 configurações (`min_pts` 13 e 24); ruído
  entre 0,3% e 23,8%.

### [02/10/2026] T1 — pré-processamento em `src/preprocessamento.py`

**Adicionado**

- `src/preprocessamento.py`, com o cálculo das células 3, 5 e 7 do notebook
  03 em forma de função, para os testes de estabilidade (T3) e de
  sensibilidade (T5) refazerem a matriz sem copiar código:
  `carregar_features` (22 features ordenadas por bloco e nome),
  `taxas_da_janela` (taxas criminais refeitas para qualquer lista de anos,
  reaproveitando `agregar_janela` do `merge_bases.py`) e `montar_matriz`
  (devolve `Z`, `W` e o peso `1/√n`, calculado a partir da lista de features
  recebida).
- Notebook 03, seção 7: conferência com dois `assert` de que as funções
  reproduzem a `W` do notebook e as 9 taxas criminais da `base_final.csv`.

**Números**

- Os dois `assert` passam: `W` igual (644 × 22) e 9 taxas criminais iguais
  nos 644 municípios. `matriz_modelagem.csv` e as figuras do notebook 03 não
  mudaram.

### [11/09/2026] Relatório da base — seleção das taxas e transformações

**Corrigido**

- `relatorio()` em `src/merge_bases.py` escolhia o Bloco B por prefixo
  `taxa_` com exceções à mão, e `taxa_alfabetizacao` (Censo 2022, 94,9%)
  saía listada como taxa criminal por 100 mil hab./ano; a seleção passou a
  ser por `bloco == "criminalidade"` no dicionário, como já faziam os
  notebooks, e a seção volta a ter exatamente as 10 taxas criminais.

**Alterado**

- O bloco final de `relatorio_base.txt` passa a descrever o que o notebook
  de modelagem faz de fato — `log1p` nas taxas criminais e nas duas
  variáveis em R$, `StandardScaler` e peso `1/√n` por bloco — no lugar do
  `RobustScaler` abandonado em 07/09.

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
