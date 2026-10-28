# Resultados da entrega final

Data: 28/10/2026 · Commit: `d494101` (último commit antes deste relatório)

Este relatório reúne os resultados das tarefas T7a a T7d de
`tarefas/T7_entrega_final.md`. A partição de referência em todas as
comparações é a do `data/processed/perfis.csv`: K-means com k = 4, sobre 644
municípios (a capital fica fora por não ter IEGM). Os perfis são numerados de
1 a 4 em ordem crescente de condição socioeconômica. Têm 66, 217, 196 e 165
municípios, respectivamente.

## 1. Resumo

- **T7a, sensibilidade (notebook 08).** A retirada de `taxa_trafico`,
  `pib_percapita` e `i_planejamento_ord`, uma de cada vez e as três juntas,
  dá ARI entre **0,849** (as três) e **0,948** (só o tráfico). Nos quatro
  testes, os perfis se mantêm.
- **T7b, taxas suavizadas (notebook 09).** As 9 taxas criminais foram
  suavizadas pelo estimador bayesiano empírico global. Com elas, o ARI contra
  a referência é **0,551** e 113 municípios mudam de perfil: os perfis
  **dependem** da suavização. A partição suavizada é mais estável à retirada
  dos pequenos: o ARI desse teste passa de 0,480 para **0,822**, e a
  silhueta, de 0,101 para 0,115.
- **T7b, conferência dos 5%.** O critério de 5% nos municípios com mais de
  100 mil habitantes **falhou** em 5 das 9 naturezas criminais. A falha foi
  investigada e não é erro de implementação (seção 4.3).
- **T7c, capital (notebook 10).** Nas 15 colunas sem gestão, a capital fica
  mais próxima do **perfil 4** (distância de 1,304) e, em segundo lugar, do
  perfil 3 (1,590). A mesma regra acerta o perfil de **0,781** dos 644
  municípios, mas só 0,648 no perfil 3 e 0,709 no perfil 4. A capital fica
  fora da faixa dos 644 na taxa de roubo de outros.
- **T7d, nomes.** Três sugestões descritivas por perfil, com os números que
  as apoiam (seção 6). Nenhum nome foi escolhido.

## 2. Critério de leitura do ARI

Faixas usadas em T7a e T7b. Estão em `FAIXAS_ARI`, no `src/config.py`, e
foram escritas na primeira célula dos notebooks 08 e 09, antes das células
que calculam.

| ARI | Leitura |
|---|---|
| ≥ 0,80 | os perfis se mantêm |
| 0,65 a 0,80 | os perfis mudam em parte; descrever quais |
| < 0,65 | os perfis dependem da mudança testada |

**O grupo confirmou as faixas em 28/10/2026, antes de qualquer notebook ser
executado.** Elas não foram alteradas depois.

## 3. T7a — Sensibilidade

### 3.1 O que foi feito

Para cada uma das três variáveis, e depois para as três juntas, a coluna
saiu da lista de features. A matriz foi refeita com `montar_matriz`, que
recalcula o peso `1/√n` do bloco com uma coluna a menos. Os municípios foram
agrupados com K-means k = 4 e renumerados pelo critério socioeconômico. A
partição obtida foi comparada com a de referência pelo ARI. Em todas as
matrizes refeitas, um `assert` confirmou que cada bloco continua com um terço
da variância. Antes disso, outro `assert` confirmou que o mesmo procedimento,
com as 22 features, reproduz exatamente o `perfis.csv` (notebook 08,
seção 1).

### 3.2 Tabela de sensibilidade

Fonte: `data/processed/tabela_sensibilidade.csv` (notebook 08, seção 2).

| variavel_retirada | bloco | n_colunas_no_bloco | ari | leitura | municipios_que_mudaram |
|---|---|---|---|---|---|
| taxa_trafico | criminalidade | 8 | 0,948 | os perfis se mantêm | 12 |
| pib_percapita | socioeconomico | 5 | 0,864 | os perfis se mantêm | 33 |
| i_planejamento_ord | gestao | 6 | 0,904 | os perfis se mantêm | 23 |
| as três | criminalidade, socioeconomico, gestao | 8, 5, 6 | 0,849 | os perfis se mantêm | 37 |

`n_colunas_no_bloco` é o número de colunas que ficaram no bloco depois da
retirada.

### 3.3 Tabelas cruzadas

Fonte: notebook 08, seção 3. As linhas trazem o perfil original e as
colunas, o perfil sem a variável. Os municípios fora da diagonal mudaram de
perfil.

**Sem `taxa_trafico`**

| original \ novo | 1 | 2 | 3 | 4 | total |
|---|---|---|---|---|---|
| 1 | 65 | 1 | 0 | 0 | 66 |
| 2 | 0 | 215 | 1 | 1 | 217 |
| 3 | 1 | 4 | 191 | 0 | 196 |
| 4 | 0 | 1 | 3 | 161 | 165 |
| total | 66 | 221 | 195 | 162 | 644 |

**Sem `pib_percapita`**

| original \ novo | 1 | 2 | 3 | 4 | total |
|---|---|---|---|---|---|
| 1 | 65 | 1 | 0 | 0 | 66 |
| 2 | 2 | 215 | 0 | 0 | 217 |
| 3 | 2 | 8 | 186 | 0 | 196 |
| 4 | 0 | 5 | 15 | 145 | 165 |
| total | 69 | 229 | 201 | 145 | 644 |

**Sem `i_planejamento_ord`**

| original \ novo | 1 | 2 | 3 | 4 | total |
|---|---|---|---|---|---|
| 1 | 66 | 0 | 0 | 0 | 66 |
| 2 | 2 | 211 | 2 | 2 | 217 |
| 3 | 3 | 4 | 186 | 3 | 196 |
| 4 | 0 | 1 | 6 | 158 | 165 |
| total | 71 | 216 | 194 | 163 | 644 |

**Sem as três**

| original \ novo | 1 | 2 | 3 | 4 | total |
|---|---|---|---|---|---|
| 1 | 65 | 1 | 0 | 0 | 66 |
| 2 | 2 | 210 | 4 | 1 | 217 |
| 3 | 3 | 6 | 187 | 0 | 196 |
| 4 | 0 | 0 | 20 | 145 | 165 |
| total | 70 | 217 | 211 | 146 | 644 |

### 3.4 Frases para o artigo

- A retirada da taxa de tráfico de entorpecentes produz ARI de 0,948 em
  relação à partição de referência, com 12 dos 644 municípios mudando de
  perfil, de modo que os perfis se mantêm.
- Sem o PIB per capita, o ARI é de 0,864 e 33 municípios mudam de perfil. A
  maior parte deles sai do perfil 4 (15 para o perfil 3 e 5 para o perfil 2)
  e do perfil 3 (8 para o perfil 2). Os perfis se mantêm.
- A retirada da nota de planejamento do IEGM produz ARI de 0,904, com 23
  municípios mudando de perfil, e os perfis se mantêm.
- Com as três variáveis retiradas ao mesmo tempo, o ARI é de 0,849 e 37
  municípios mudam de perfil, 20 deles do perfil 4 para o perfil 3. Os
  perfis se mantêm.
- Em todos os testes, o perfil 1 mantém pelo menos 65 dos seus 66
  municípios.

### 3.5 Desvios do plano

Nenhum no cálculo. Duas observações:

- A conta do `orcamento` do notebook 03 foi copiada para
  `src/preprocessamento.py` sem o arredondamento, para servir ao `assert`. O
  notebook 03 não mudou.
- A contagem `municipios_que_mudaram` depende da renumeração pelo critério
  socioeconômico. O ARI não depende da numeração.

## 4. T7b — Taxas suavizadas

### 4.1 Fórmula usada e fontes conferidas

Para cada natureza criminal, `y` são as ocorrências do município na janela
2023–2025 e `n` são as pessoas-ano (população de 2024 × exposição de 3,0
anos):

```
r   = y / n                                         taxa bruta
m   = soma(y) / soma(n)                             taxa do conjunto
s²  = soma(n · (r − m)²) / soma(n) − m / média(n),  e 0 se der negativo
C   = s² / (s² + m / n)                             quanto da taxa bruta é mantido
r_suavizada = m + C · (r − m)                       depois, × 100 mil
```

É a fórmula do plano, sem nenhuma diferença. Foi conferida em duas fontes:

1. **Documentação da função `EBest` do pacote `spdep` do R**
   (<https://cran.r-project.org/web/packages/spdep/refman/spdep.html>, seção
   `EBest`). Ela traz `b = Σnᵢ/Σxᵢ`, `s² = Σxᵢ(pᵢ − b)²/Σxᵢ` e
   `a = s² − b/(Σxᵢ/m)`, com `m` = número de áreas. Na notação acima, `b` é
   o nosso `m`, `a` é o nosso `s²`, e `Σxᵢ/m` é a média de `n`. A
   documentação remete a Marshall (1991, p. 284–285) e a Bailey e Gatrell
   (1995, p. 303–306).
2. **Código da classe `Empirical_Bayes` do pacote `esda` (PySAL)**
   (<https://github.com/pysal/esda>, arquivo `esda/smoothing.py`). A conta é
   a mesma, e o peso é `r_var / (r_var + r_mean / b)`. Num exemplo de teste
   com dados sorteados, a implementação de `estimador_bayesiano_global` deu
   o mesmo resultado desse código. Essa comparação foi feita fora dos
   notebooks e não está no repositório.

Referências citadas pelas fontes:

- Marshall, R. M. (1991). Mapping disease and mortality rates using
  empirical Bayes estimators. *Applied Statistics*, 40, 283–294.
- Bailey, T.; Gatrell, A. (1995). *Interactive Spatial Data Analysis*.
  Harlow: Longman, p. 303–306.

**Não conferido:** os artigos originais de Marshall (1991) e de Assunção et
al. (1998) não foram consultados. A afirmação do plano de que Assunção et al.
(1998) usam este estimador também não foi conferida no artigo deles. O
`max(s², 0)` está no plano e é a leitura usual, mas a documentação
consultada não o descreve.

**Decisão de implementação:** a taxa do conjunto `m` foi calculada sobre os
644 municípios da modelagem, sem a capital. O motivo é o mesmo de a
padronização ser ajustada só neles: a capital não participa do agrupamento.
O grupo precisa confirmar essa decisão (seção 9).

### 4.2 Mediana de C por natureza

Fonte: notebook 09, seção 2. A taxa do conjunto está em ocorrências por 100
mil hab./ano.

| natureza | taxa do conjunto (m) | mediana de C, 149 pequenos | mediana de C, 495 demais |
|---|---|---|---|
| taxa_cvli | 6,495 | 0,151 | 0,524 |
| taxa_tentativa_homicidio | 8,708 | 0,191 | 0,594 |
| taxa_estupro_total | 33,794 | 0,336 | 0,757 |
| taxa_lesao_dolosa | 346,257 | 0,664 | 0,924 |
| taxa_trafico | 99,940 | 0,799 | 0,961 |
| taxa_roubo_veiculo | 55,489 | 0,835 | 0,969 |
| taxa_furto_veiculo | 150,671 | 0,886 | 0,980 |
| taxa_furto_outros | 918,065 | 0,924 | 0,987 |
| taxa_roubo_outros | 223,692 | 0,953 | 0,992 |

### 4.3 Conferência nos municípios grandes (critério dos 5%)

O plano pedia um `assert` de que, nos municípios com mais de 100 mil
habitantes, a taxa suavizada diferisse menos de 5% da bruta. **O critério
falhou.** No notebook, ele virou uma tabela em vez de um `assert`, para o
notebook rodar até o fim e a falha ficar documentada. Fonte: notebook 09,
seção 3 (79 municípios grandes).

| natureza | mediana de C | diferença mediana | diferença máxima | municípios acima de 5% |
|---|---|---|---|---|
| taxa_cvli | 0,9174 | 0,0227 | 0,4089 | 18 |
| taxa_estupro_total | 0,9692 | 0,0061 | 0,0552 | 1 |
| taxa_furto_outros | 0,9987 | 0,0002 | 0,0017 | 0 |
| taxa_furto_veiculo | 0,9979 | 0,0006 | 0,0093 | 0 |
| taxa_lesao_dolosa | 0,9919 | 0,0010 | 0,0089 | 0 |
| taxa_roubo_outros | 0,9992 | 0,0006 | 0,0116 | 0 |
| taxa_roubo_veiculo | 0,9968 | 0,0021 | 0,1301 | 6 |
| taxa_tentativa_homicidio | 0,9365 | 0,0119 | 0,1303 | 10 |
| taxa_trafico | 0,9960 | 0,0013 | 0,0819 | 1 |

**O que a investigação encontrou:**

- **As conferências da implementação passam** (notebook 09, seção 1). O C
  fica entre 0 e 1 e cresce com a população. A taxa suavizada fica sempre
  entre a bruta e a do conjunto. As taxas brutas refeitas do painel são
  iguais às da base.
- **Em proporção, a diferença nos grandes é pequena.** A diferença mediana
  não passa de 2,27% (CVLI) em nenhuma natureza, e a mediana de C fica entre
  0,917 e 0,999.
- **A falha vem de duas coisas.** Nos crimes raros, C fica abaixo de 1 mesmo
  em cidade grande. E, quando a taxa bruta está bem abaixo da taxa do
  conjunto, um deslocamento pequeno em valor absoluto vira uma diferença
  grande em proporção.
- **O maior caso é Valinhos** (131.277 habitantes): CVLI bruto de 1,523,
  suavizado de 2,146 e C de 0,875. É um deslocamento de 0,6 por 100 mil
  hab./ano, que equivale a 40,9% da taxa bruta. Os cinco piores casos no
  CVLI têm taxa bruta abaixo de 3,4 e C entre 0,875 e 0,910. Além de
  Valinhos, são São Caetano do Sul, Santana de Parnaíba, Santa Bárbara
  d'Oeste e Botucatu (notebook 09, seção 3).

O critério não foi alterado, e a suavização foi mantida como especificada.

### 4.4 Original × suavizado

Fonte: `data/processed/tabela_taxas_suavizadas.csv` (notebook 09, seções 5
a 7). Nas três primeiras linhas, o valor original é 1 por definição: a
partição comparada consigo mesma.

| medida | original | suavizado | leitura do ARI suavizado |
|---|---|---|---|
| ARI contra perfis.csv, 644 municípios | 1,000 | 0,551 | os perfis dependem da mudança testada |
| ARI contra perfis.csv, 149 pequenos | 1,000 | 0,713 | os perfis mudam em parte |
| ARI contra perfis.csv, 495 demais | 1,000 | 0,504 | os perfis dependem da mudança testada |
| ARI do teste sem os pequenos | 0,480 | 0,822 | — |
| silhueta | 0,101 | 0,115 | — |
| municípios que mudaram de perfil | 0 | 113 | — |

Os dois valores originais foram recalculados no notebook. Um `assert`
confirmou que são iguais aos da `tabela_comparacao_algoritmos.csv` (0,480 e
0,101).

### 4.5 Tabela cruzada perfil original × suavizado

Fonte: notebook 09, seção 5.

| original \ suavizado | 1 | 2 | 3 | 4 | total |
|---|---|---|---|---|---|
| 1 | 65 | 1 | 0 | 0 | 66 |
| 2 | 2 | 213 | 0 | 2 | 217 |
| 3 | 4 | 59 | 131 | 2 | 196 |
| 4 | 0 | 31 | 12 | 122 | 165 |
| total | 71 | 304 | 143 | 126 | 644 |

### 4.6 Municípios que mudaram de perfil

Foram **113** municípios, mais que os 30 do limite do plano para listar um a
um. A lista completa está em `data/processed/perfis_suavizados.csv` (colunas
`perfil_original` e `perfil_suavizado`). Resumo por mudança (notebook 09,
seção 7):

| de | para | municípios | pequenos (< 5.000 hab.) | população mediana |
|---|---|---|---|---|
| 1 | 2 | 1 | 1 | 4.896 |
| 2 | 1 | 2 | 2 | 3.413 |
| 2 | 4 | 2 | 2 | 1.528,5 |
| 3 | 1 | 4 | 0 | 17.572 |
| 3 | 2 | 59 | 4 | 12.529 |
| 3 | 4 | 2 | 0 | 33.748,5 |
| 4 | 2 | 31 | 3 | 17.156 |
| 4 | 3 | 12 | 0 | 100.497 |

Nos perfis 3 e 4, os municípios que saem e os que ficam se comparam assim
(medianas; notebook 09, seção 7):

| perfil original | situação | municípios | roubo de outros, bruta | roubo de outros, suavizada | CVLI, bruta | CVLI, suavizada | população |
|---|---|---|---|---|---|---|---|
| 3 | ficaram | 131 | 58,39 | 59,89 | 8,14 | 7,46 | 32.888 |
| 3 | saíram | 65 | 26,96 | 29,62 | 5,56 | 6,05 | 13.058 |
| 4 | ficaram | 122 | 61,96 | 62,75 | 4,86 | 5,30 | 69.056 |
| 4 | saíram | 43 | 33,33 | 34,31 | 7,02 | 6,79 | 24.423 |

### 4.7 Frases para o artigo

- Com as taxas criminais suavizadas pelo estimador bayesiano empírico global
  (Marshall, 1991), o ARI em relação à partição de referência é de 0,551, e
  113 dos 644 municípios mudam de perfil. Pelo critério adotado, os perfis
  dependem do tratamento dado às taxas.
- A mudança não se concentra nos municípios pequenos: 12 dos 113 têm menos
  de 5.000 habitantes. O ARI é de 0,713 entre os 149 pequenos e de 0,504
  entre os 495 demais.
- Os perfis 1 e 2 praticamente se mantêm (65 de 66 e 213 de 217
  municípios). Os perfis 3 e 4 perdem 65 e 43 municípios, a maior parte para
  o perfil 2, que passa de 217 para 304 municípios.
- Com as taxas suavizadas, o teste de retirada dos municípios pequenos passa
  de ARI 0,480 para 0,822, e a silhueta, de 0,101 para 0,115.

As frases citam Marshall (1991), que não está no `sbc-template.bib` (seção
9).

### 4.8 Desvios do plano

1. **Critério dos 5%:** virou tabela em vez de `assert`, porque falhou. A
   investigação está na seção 4.3.
2. **Taxa do conjunto `m`:** calculada sobre os 644, sem a capital. O plano
   dizia "taxa do estado" sem especificar.
3. **Naturezas suavizadas:** `suavizar_taxas` suaviza todos os grupos de
   `GRUPOS_NATUREZA`, como a `taxas_da_janela`. Isso inclui
   `taxa_roubo_carga`, que não é feature e não entra na matriz.
4. **Colunas extras:** a função devolve, além das taxas, uma coluna
   `c_<grupo>` com o C de cada município, usada nas conferências.

## 5. T7c — Capital

### 5.1 Perfil mais próximo e distâncias

Fonte: `data/processed/tabela_capital.csv` (notebook 10, seções 2 e 3).

**Como a capital foi posta na escala dos 644:**

- Recebeu `log1p` nas mesmas colunas que os 644.
- Foi padronizada com a média e o desvio dos 644. Um `assert` confirmou que
  essa escala, aplicada aos 644, reproduz exatamente a matriz padronizada da
  `montar_matriz`.
- Foram usadas 15 colunas: as 9 de criminalidade, com peso 0,333, e as 6
  socioeconômicas, com peso 0,408, os mesmos da matriz original.

| perfil | distância da capital ao centro |
|---|---|
| 1 | 3,030 |
| 2 | 2,453 |
| 3 | 1,590 |
| **4** | **1,304** (mais próximo) |

- Perfil mais próximo: **4**. Segundo mais próximo: **3** (1,590).
- Para comparação: a distância mediana dos 644 ao seu centro mais próximo é
  de 0,986. **23,4%** dos 644 ficam mais longe do seu centro do que a
  capital fica do perfil 4.

### 5.2 Taxa de acerto do método nos 644

Fonte: notebook 10, seção 3. A regra é a mesma usada para a capital (centro
mais próximo nas 15 colunas, sem gestão), aplicada a cada um dos 644
municípios.

- **Taxa de acerto: 0,781** (503 de 644).
- Por perfil original: 0,970 no perfil 1, 0,899 no 2, **0,648 no 3** e
  **0,709 no 4**.

| original \ apontado | 1 | 2 | 3 | 4 | total |
|---|---|---|---|---|---|
| 1 | 64 | 2 | 0 | 0 | 66 |
| 2 | 1 | 195 | 17 | 4 | 217 |
| 3 | 0 | 13 | 127 | 56 | 196 |
| 4 | 0 | 11 | 37 | 117 | 165 |
| total | 65 | 221 | 181 | 177 | 644 |

O teste favorece o método, porque os centros são calculados com os próprios
644. Mesmo assim, a regra separa mal justamente os perfis 3 e 4: 56 do
perfil 3 são apontados para o 4, e 37 do perfil 4 para o 3. São os dois
perfis mais próximos da capital.

### 5.3 A capital em cada variável

Fonte: `data/processed/tabela_capital_variaveis.csv` (notebook 10, seção 4).

- **Valor da capital e faixa dos 644:** em unidades originais. Taxas em
  ocorrências por 100 mil hab./ano, PIB e renda em R$, demais em %.
- **Desvios:** na escala da matriz (depois do `log1p` nas taxas e nas
  variáveis em R$), em relação à média dos 644. As médias dos perfis estão
  na mesma escala, como na Figura 5.
- **⚠:** a capital fica fora da faixa dos 644 nessa variável (extrapolação).

| variável | capital (valor) | mín. 644 | máx. 644 | capital (desvios) | perfil 1 | perfil 2 | perfil 3 | perfil 4 | fora da faixa |
|---|---|---|---|---|---|---|---|---|---|
| taxa_cvli | 4,65 | 0,00 | 50,47 | 0,06 | 0,08 | −0,40 | 0,35 | 0,07 | |
| taxa_estupro_total | 25,18 | 0,00 | 183,43 | −0,68 | 0,41 | 0,06 | 0,08 | −0,34 | |
| taxa_furto_outros | 2.079,07 | 95,13 | 2.947,45 | 2,80 | −0,34 | −0,62 | 0,45 | 0,42 | |
| taxa_furto_veiculo | 340,61 | 0,00 | 522,62 | 2,06 | −0,31 | −0,72 | 0,40 | 0,60 | |
| taxa_lesao_dolosa | 312,42 | 145,94 | 1.169,15 | −0,77 | −0,39 | 0,32 | 0,08 | −0,35 | |
| taxa_roubo_outros | **952,88** | 0,00 | **751,84** | 2,40 | −0,17 | −0,81 | 0,52 | 0,52 | ⚠ |
| taxa_roubo_veiculo | 104,98 | 0,00 | 255,60 | 1,79 | −0,05 | −0,84 | 0,53 | 0,51 | |
| taxa_tentativa_homicidio | 5,80 | 0,00 | 73,56 | −0,31 | 0,26 | −0,28 | 0,23 | −0,01 | |
| taxa_trafico | 47,28 | 0,00 | 898,17 | −0,52 | −0,39 | −0,38 | 0,34 | 0,26 | |
| pib_percapita | 89.682,49 | 13.076,43 | 579.715,62 | 1,18 | −0,84 | −0,21 | −0,01 | 0,63 | |
| prop_esgoto_adequado | 96,08 | 30,42 | 100,00 | 0,53 | −2,23 | 0,14 | 0,17 | 0,51 | |
| prop_lixo_coletado | 99,72 | 54,16 | 100,00 | 0,85 | −1,21 | −0,38 | 0,37 | 0,54 | |
| renda_domiciliar_mediana | 1.340,00 | 700,00 | 2.500,00 | 0,98 | −1,38 | −0,05 | −0,13 | 0,78 | |
| taxa_alfabetizacao | 97,42 | 87,77 | 98,84 | 1,40 | −0,99 | −0,65 | 0,33 | 0,85 | |
| taxa_urbanizacao | 99,85 | 27,04 | 100,00 | 1,03 | −2,10 | −0,16 | 0,35 | 0,64 | |

Só uma variável fica fora da faixa: a taxa de roubo de outros. Nos crimes
patrimoniais, porém, a capital fica bem acima da média de todos os perfis,
mesmo dentro da faixa:

- furto de outros: 2,80 desvios, contra 0,42 no perfil 4;
- roubo de outros: 2,40, contra 0,52;
- furto de veículo: 2,06, contra 0,60.

### 5.4 Frases para o artigo

- Para situar a capital, excluída da modelagem por não ter IEGM, os dados
  dela foram transformados com a mesma escala dos 644 municípios. A seguir,
  calculou-se a sua distância ao centro de cada perfil nas 15 variáveis de
  criminalidade e condição socioeconômica.
- A capital fica mais próxima do perfil 4 (distância de 1,304) e, em segundo
  lugar, do perfil 3 (1,590).
- Aplicada aos 644 municípios, a mesma regra devolve o perfil original de
  78,1% deles, mas apenas de 64,8% do perfil 3 e de 70,9% do perfil 4. Assim,
  a distinção entre os dois perfis mais próximos da capital é a parte menos
  confiável do resultado.
- **Ressalva de extrapolação:** a taxa de roubo da capital (952,88 por 100
  mil hab./ano) supera o máximo observado entre os 644 municípios (751,84).
  Nos furtos e no roubo de veículo, a capital fica bem acima da média de
  todos os perfis, de modo que a sua posição é uma aproximação, e não uma
  classificação.

### 5.5 Desvios do plano

- Além das saídas pedidas, foram gerados `tabela_capital_variaveis.csv` e a
  figura opcional `figura_mapa_perfis_com_capital`. A figura tem a capital
  pintada com o perfil 4 e o contorno reforçado; a Figura 6 não mudou.
- A `tabela_capital.csv` está no formato "uma medida por linha". Além das
  distâncias e da taxa de acerto, traz o segundo perfil mais próximo, a
  distância mediana dos 644, o % dos 644 mais longe que a capital e o número
  de variáveis fora da faixa.

## 6. T7d — Sugestões de nomes

Nomes descritivos, de até quatro palavras, sem sugerir causa nem
julgamento. Os números vêm da Figura 5 (desvios em relação à média dos 644)
e da `tabela_perfis.csv` (medianas; entre parênteses, a mediana dos 644).
**A escolha é do grupo.** As figuras e os notebooks não foram alterados.

| perfil | opção | números que apoiam |
|---|---|---|
| **1** (66) | rural de maior privação | urbanização de 60,81% (90,54%), −2,1; renda de R$ 941,66 (R$ 1.200,00), −1,4 |
| | baixa urbanização e saneamento | esgoto adequado de 69,49% (94,45%), −2,2; coleta de lixo −1,2; urbanização −2,1 |
| | menor renda e escolaridade | renda −1,4; alfabetização de 93,28% (95,00%), −1,0; PIB per capita de R$ 27.329,21 (R$ 45.480,16), −0,8 |
| **2** (217) | pequenos de baixo roubo | população mediana de 4.706 (13.285), 53,5% com menos de 5.000 hab.; roubo de 10,30 (27,85), −0,8 |
| | pequenos, crime patrimonial baixo | roubo de outros e de veículo −0,8; furto de veículo −0,7; furto de outros de 469,31 (620,93), −0,6 |
| | pequenos de renda intermediária | renda de R$ 1.200,00, igual à mediana dos 644, entre a do perfil 1 (R$ 941,66) e a do 4 (R$ 1.258,33); esgoto +0,1 |
| **3** (196) | urbano de IEGM baixo | IEGM geral mediano de 1,00 (1,33); saúde −0,7, educação −0,6; urbanização de 93,19%, +0,4 |
| | urbano de renda intermediária | urbanização +0,4 e coleta de lixo +0,4; renda de R$ 1.175,00 (R$ 1.200,00), −0,1 |
| | crime patrimonial, IEGM baixo | roubo de 46,24 (27,85), +0,5; furtos +0,4; as sete dimensões do IEGM abaixo da média (de −0,2 em tecnologia da informação a −0,7 em saúde) |
| **4** (165) | urbano de IEGM alto | único perfil acima da média nas sete dimensões do IEGM (tecnologia da informação +1,1, cidades +1,0); IEGM geral mediano de 2,00 (1,33) |
| | polos de maior renda | renda de R$ 1.258,33, +0,8; PIB per capita de R$ 62.956,14, +0,6; população mediana de 53.157 |
| | urbano de maior escolaridade | alfabetização de 96,53% (95,00%), +0,9; urbanização de 96,48%, +0,6 |

Duas observações para a escolha:

- O IEGM geral (`iegm_ord`) não é feature; aparece na `tabela_perfis.csv`
  só como contexto. Os nomes com "IEGM" se apoiam também nas dimensões da
  Figura 5: no perfil 3, as sete ficam abaixo da média (ambiental −0,4,
  cidades −0,3, educação −0,6, fiscal −0,4, tecnologia da informação −0,2,
  planejamento −0,3, saúde −0,7); no perfil 4, as sete ficam acima.
- Se o grupo adotar a partição com taxas suavizadas (seção 4), os perfis 2,
  3 e 4 mudam de composição, e os nomes precisam ser revistos.

## 7. Figuras e tabelas geradas

| arquivo | o que mostra | uso |
|---|---|---|
| `data/processed/tabela_sensibilidade.csv` | ARI, leitura e municípios que mudaram, sem cada uma das 3 variáveis e sem as três | artigo (tabela ou texto da robustez) |
| `data/processed/tabela_taxas_suavizadas.csv` | ARI (644, 149, 495, sem os pequenos), silhueta e municípios que mudaram, original × suavizado | artigo (tabela ou texto da robustez) |
| `data/processed/perfis_suavizados.csv` | perfil original e suavizado de cada um dos 644 municípios | apoio (lista dos 113 que mudaram) |
| `data/processed/tabela_capital.csv` | distâncias da capital aos 4 perfis, perfis mais próximos, taxa de acerto e comparações | artigo (texto) |
| `data/processed/tabela_capital_variaveis.csv` | a capital e a média de cada perfil nas 15 variáveis, com a faixa dos 644 | apoio (ressalva de extrapolação) |
| `figuras/figura_taxas_suavizadas.png` | CVLI bruto × suavizado de cada município, com os pequenos destacados | apoio |
| `figuras/figura_mapa_perfis_com_capital.png` | Figura 6 com a capital pintada no perfil 4 e o contorno reforçado | apoio (pode substituir a Figura 6 se o grupo quiser mostrar a capital) |
| `notebooks/08_sensibilidade.ipynb`, `09_taxas_suavizadas.ipynb`, `10_capital.ipynb` | os cálculos e as conferências desta entrega | — |

Nenhum arquivo existente foi alterado: `base_final.csv`,
`matriz_modelagem.csv`, `perfis.csv`, os notebooks 01 a 07, as figuras 1 a 6
e as tabelas anteriores. O código novo está em `src/`: `orcamento`,
`escala_de_referencia`, `transformar_com_escala`,
`estimador_bayesiano_global` e `suavizar_taxas` em `preprocessamento.py`;
`faixa_ari`, `refazer_particao` e `distancias_aos_centros` em
`clusterizacao.py`; `plot_taxas_suavizadas` e `plot_mapa_com_destaque` em
`figuras.py`; e `FAIXAS_ARI`, `VARIAVEIS_SENSIBILIDADE`, `POPULACAO_GRANDE` e
`DIFERENCA_MAXIMA_GRANDES` em `config.py`.

## 8. O que muda no artigo

As seções citadas são as do `artigo.tex` na pasta do Overleaf, versão de
09/10.

**Método — Clusterização e caracterização dos perfis (3.3)**

- **O que acrescentar:** um parágrafo sobre os três testes desta entrega.
  1. **Sensibilidade:** retirada de cada uma das três variáveis e das três
     juntas, com o peso recalculado.
  2. **Taxas suavizadas:** estimador bayesiano empírico global, com a taxa
     do conjunto calculada sobre os 644. Citar Marshall (1991) e manter
     `\cite{assuncao1998}`.
  3. **Capital:** escala dos 644, 15 colunas, centro mais próximo e teste de
     acerto da mesma regra nos 644.
- **As faixas do ARI** (0,65 e 0,80) foram um critério do grupo, definido
  antes de rodar. Se o texto as apresentar como faixas da literatura,
  precisa de citação: [CITAÇÃO?] — afirmação "ARI acima de 0,80 indica
  partições equivalentes". Recomenda-se apresentá-las como critério do
  próprio estudo.
- **Por quê:** os Resultados vão trazer esses testes, e o método precisa
  descrevê-los antes.

**Resultados**

- **O que acrescentar:** uma subseção nova, por exemplo "Robustez dos perfis
  e posição da capital", depois de "Perfis":
  - a tabela de sensibilidade (seção 3.2 ou as frases da 3.4);
  - a comparação original × suavizado (seção 4.4) e a frase sobre quais
    perfis mudam (seção 4.7);
  - um parágrafo sobre a capital, com a ressalva de extrapolação (seção
    5.4).
- **Figura 6:** se o grupo quiser mostrar a capital, a
  `figura_mapa_perfis_com_capital` pode entrar no lugar dela. A legenda
  precisa dizer que a capital não foi agrupada.
- **Por quê:** os três testes eram os "próximos passos" do relatório
  parcial.

**Discussão — limitações**

Das seis limitações atuais:

- **Segunda (capital fora da modelagem): continua, mas atenuada.** A capital
  ainda não participa do agrupamento. Agora, porém, sabe-se que ela se
  aproxima do perfil 4, com a ressalva da extrapolação no roubo e da
  separação fraca entre os perfis 3 e 4 sem as notas de gestão.
- **Terceira (taxas instáveis dos pequenos): não deixa de ser limitação, e
  muda de natureza.**
  - A frase atual ("ARI de 0,480") continua correta para a partição
    escolhida.
  - O teste novo mostra que, com taxas suavizadas, esse ARI sobe para 0,822,
    mas a partição muda em 113 municípios (ARI 0,551).
  - A mudança atinge sobretudo municípios com 5.000 habitantes ou mais, que
    passam dos perfis 3 e 4 para o 2.
  - O texto precisa dizer que os perfis 3 e 4 dependem de como as taxas
    raras são tratadas. A redação final depende da decisão do grupo (seção
    9).
- **Quarta (tráfico, PIB per capita e planejamento): deixa de ser
  limitação para os perfis.** A retirada dessas variáveis não muda os perfis
  (ARI de 0,849 a 0,948). A frase pode virar resultado: as três variáveis
  continuam com os problemas de medida descritos, mas os perfis não dependem
  delas.
- **Primeira, quinta e sexta: não mudam.** A sexta (silhuetas baixas)
  continua: a silhueta da partição suavizada também é baixa (0,115).

**Discussão — próximos passos**

- **Saem os três itens atuais:** sensibilidade, encolhimento bayesiano e
  comparação da capital. Os três foram feitos.
- **Podem entrar, se o grupo quiser:**
  - repetir a caracterização dos perfis com as taxas suavizadas, caso o
    grupo decida mantê-las como teste e não como modelo;
  - uma versão local do estimador bayesiano, que usa os municípios vizinhos
    em vez do estado inteiro. É preciso conferir se Assunção et al. (1998)
    a descrevem antes de citar: [CITAÇÃO?] — afirmação "o estimador
    bayesiano empírico local usa a vizinhança geográfica de cada município".

**Resumo e Abstract**

- **O que acrescentar:** uma frase sobre a robustez. Por exemplo, que os
  perfis se mantêm com a retirada das três variáveis de medida discutível
  (ARI ≥ 0,849) e que a capital se aproxima do perfil 4. O Abstract precisa
  da mesma frase em inglês.
- **Taxas suavizadas:** só entram no resumo depois da decisão do grupo.
  Pelo critério adotado, a mudança é grande o bastante para precisar ser
  mencionada se o resumo falar em estabilidade.

## 9. Pendências e avisos

1. **Decisão do grupo — taxas suavizadas.** Com as taxas suavizadas, os
   perfis dependem da mudança (ARI 0,551; 113 municípios mudam), mas a
   estabilidade sem os pequenos melhora (0,480 → 0,822). O grupo precisa
   decidir entre duas opções:
   - (a) manter a partição atual e relatar a suavização como limitação;
   - (b) rever o modelo com as taxas suavizadas.

   A opção (b) mudaria o `perfis.csv`, as Figuras 5 e 6 e os notebooks 06 e
   07, e isso não foi feito.
2. **Critério dos 5% falhou** em 5 das 9 naturezas (seção 4.3). Foi
   investigado e não é erro de implementação. O grupo precisa registrar que
   o critério, definido antes, não se cumpriu.
3. **Taxa do conjunto `m` sobre os 644, sem a capital.** É uma decisão de
   implementação que o grupo precisa confirmar. Com a capital, `m` mudaria,
   e as taxas suavizadas também; esse cálculo não foi feito.
4. **Fontes da fórmula.** A fórmula foi conferida na documentação do `spdep`
   e no código do `esda`. Os artigos originais de Marshall (1991) e Assunção
   et al. (1998) não foram consultados. Marshall (1991) e Bailey e Gatrell
   (1995) não estão no `sbc-template.bib` (seção 4.1 tem as referências).
5. **Faixas do ARI sem citação:** se forem apresentadas como da literatura,
   precisam de citação (seção 8).
6. **Teste de acerto da capital** é favorável ao método (os centros saem dos
   próprios 644). A confusão entre os perfis 3 e 4 é a principal ressalva.
7. **Nomes dos perfis:** escolha do grupo (seção 6).
8. **`municipios_que_mudaram`** depende da renumeração pelo critério
   socioeconômico. O ARI não depende.
9. **Commits** feitos localmente, um por tarefa, sem push: `e50f3cb` (T7a),
   `aabcf56` (T7b), `dea21d4` (T7c), `d494101` (T7d/T7e) e o commit deste
   relatório.

**Números não conferidos:** nenhum número deste relatório deixou de ser
copiado das saídas dos notebooks 08 a 10 ou dos CSVs. As exceções são as
referências bibliográficas e a afirmação de que Assunção et al. (1998) usam
o estimador de Marshall, que vêm do plano e não foram conferidas (item 4).
