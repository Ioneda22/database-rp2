# Planejamento — Entrega dos avanços do relatório (16/09/2026)

> ## ⚠ DESATUALIZADO — leiam o [ANDAMENTO.md](ANDAMENTO.md)
>
> Este documento foi escrito em 02/09 e duas premissas dele mudaram:
>
> - **O prazo passou para 23/09/2026.**
> - **A clusterização saiu do escopo desta entrega** e vai para a seguinte.
>   Os Resultados Parciais e a Discussão passam a ser sobre a análise
>   exploratória e o pré-processamento, ou seja, as Fases 1 a 3.
>
> As Fases 0 a 3 já estão **concluídas**. As Fases 4 e 5 (clusterização e
> perfis) continuam válidas, mas para a próxima entrega. O restante do texto
> abaixo permanece útil como referência metodológica.

**Prazo original:** quarta-feira, 16 set. 2026, 23h59 · **Escrito em:** 02 set. 2026
**Janela de dados definida:** 2023–2025 (três anos civis completos) — confirmada
empiricamente na Fase 1

---

## 1. O que a entrega exige

O enunciado lista três pontos a melhorar (**Introdução**, **Trabalhos
Correlatos**, **Resultados preliminares**) e um teto de páginas por seção. O
orçamento abaixo compara o exigido com o que o `artigo.tex` tem hoje
(estimativa de ~650 palavras/página no template SBC).

| Seção | Máx. | Hoje | Falta | Situação |
|---|---:|---:|---:|---|
| Título e resumo | 1 p | 0,4 p | — | Ajustar tempo verbal |
| Introdução | 2 p | 0,6 p | **+1,4 p** | ⚠ ponto a melhorar |
| Trabalhos correlatos | 3 p | 0,9 p | **+2,1 p** | ⚠ ponto a melhorar |
| Metodologia | 2 p | 0,9 p | +1,1 p | Reescrever no passado |
| Resultados parciais | 3 p | **0** | **+3,0 p** | ⚠ ponto a melhorar — seção nova |
| Discussão e conclusão | 1 p | **0** | +1,0 p | Seção nova |
| Referências | livre | — | — | — |

São ~8,6 páginas a escrever em 14 dias. É viável, mas só com as duas trilhas
rodando em paralelo (ver §3).

### Ajustes estruturais no `artigo.tex`

1. **Renomear seções** para bater com os nomes do enunciado:
   `Materiais e Métodos` → `Metodologia`; criar `Resultados Parciais` e
   `Discussão e Conclusão`.
2. **Remover a seção `Cronograma`.** Ela não consta na lista de seções
   exigidas e consome espaço de um teto apertado. Era artefato da fase de
   proposta.
3. **Mudar o tempo verbal da Metodologia.** O texto está inteiramente no
   futuro ("será construída", "Serão utilizadas", "Serão analisados"). Um
   relatório de andamento com resultados parciais descreve no passado o que já
   foi feito, e mantém no futuro apenas o que resta.
4. **Aplicar o título revisado** (decidido na discussão do grupo):
   > "Identificar e caracterizar perfis de municípios paulistas segundo
   > **indicadores integrados de** criminalidade, efetividade da gestão
   > municipal e vulnerabilidade socioeconômica"

   O título atual usa `relacionando-os a`, que descreve duas etapas
   (clusterizar por crime, relacionar ao resto depois) — o oposto do desenho
   de etapa única que as linhas 45–47 e 64 do tex descrevem.

### ⚠ Bloqueador administrativo — resolver hoje

`sbc-template.sty`, `sbc-template.bib`, `sbc.bst` e a pasta `Imagens/` **não
estão no repositório**. O `artigo.tex` não compila localmente. Confirmem onde
o projeto compila (provavelmente Overleaf) e, principalmente, **que o `.bib`
com as 10 referências já citadas existe lá**. Sem ele não há entrega, e
descobrir isso no dia 16 é o pior cenário possível.

---

## 2. Ponto de partida

Já pronto e verificado:

- Pipeline completo: `main.py` → `parse_ssp.py` / `parse_iegm.py` /
  `merge_bases.py` → `base_final.csv` (645 × 49) + `dicionario_base.csv`.
- Junção por `codigo_ibge` em todas as fontes; agregação conferida
  (645.725 linhas brutas = soma exata das contagens).
- Blocos de features definidos: 9 criminalidade + 2 socioeconômico + 8 gestão.

Falta: os dados de 2023–2025 (só há 2026 jan–jul em disco), todo o código de
modelagem, e 8,6 páginas de texto.

---

## 3. Estratégia: duas trilhas em paralelo

**A observação que decide o cronograma:** Introdução e Trabalhos Correlatos
somam 5 das 11 páginas e **não dependem de nenhum dado**. Elas podem começar
hoje, em paralelo com a modelagem.

Se a modelagem atrasar, 5 das 7 seções já estarão prontas. Se as duas trilhas
forem sequenciais, um problema no download da SSP compromete a entrega inteira.

```
Trilha A (dados e modelagem)   Fases 0 → 5      02/09 a 12/09
Trilha B (escrita conceitual)  Fase 6           02/09 a 10/09   ← COMEÇA HOJE
Convergência                   Fases 7 → 8      12/09 a 16/09
```

Sugestão de divisão entre os três: **duas pessoas na Trilha A** (uma nos dados
/ Fases 0–2, outra na modelagem / Fases 3–5) e **uma na Trilha B**. A Fase 7
junta todo mundo.

---

## FASE 0 — Completar as bases · 02–04/09 · **BLOQUEANTE**

Nada da Trilha A anda sem isto. Prioridade máxima.

### 0.1 Baixar manualmente — SSP-SP

Em <https://www.ssp.sp.gov.br/estatistica/consultas>, os exports **anuais**,
salvos em `data/raw/ssp/` com os nomes originais:

| Arquivo | Necessidade |
|---|---|
| `SPDadosCriminais_2023.xlsx` | obrigatório |
| `SPDadosCriminais_2024.xlsx` | obrigatório |
| `SPDadosCriminais_2025.xlsx` | obrigatório |
| `SPDadosCriminais_2022.xlsx` | **só para o teste da Fase 1** — não entra na janela |
| `VeiculosSubtraidos_2023..2025.xlsx` | opcional (bloco de textura) |
| `CelularesSubtraidos_2023..2025.xlsx` | opcional (bloco de textura) |

> São ~180 MB por ano. Reservem tempo de download e espaço em disco (~1 GB).

### 0.2 Verificar — IEGM/TCE-SP

Temos exercício 2024 (o ano central da janela). Confiram em
<https://www.tce.sp.gov.br/iegm> se há planilhas dos exercícios **2023 e
2025**. Se houver, baixem: permite usar a média dos três exercícios em vez de
um ponto único, alinhando o IEGM à mesma janela do crime. Se não houver, o
exercício 2024 sozinho é defensável — mas isso vira uma limitação a declarar.

### 0.3 Ajustar o código — SIDRA e configuração

- `src/config.py`: `ANOS_JANELA = [2023, 2024, 2025]` e
  `ANO_POPULACAO_REF = 2024`.
- `src/ibge_sidra.py`: baixar a população de **2024** (hoje o CSV em disco é
  de 2026). A tabela 6579 não publica 2022 nem 2023, então 2024 — o ponto
  médio da janela — é o denominador único.

### 0.4 Rodar

```bash
python main.py --forcar
```

**Entregáveis:** `base_final.csv` definitiva (janela 2023–2025, exposição =
3,000) e `relatorio_base.txt`. A zero-inflação do CVLI deve cair de 55% para
~23%; confiram no relatório.

---

## FASE 1 — Validar a janela temporal · 04–05/09

Justifica empiricamente o recorte, em vez de afirmá-lo. Vira contribuição
metodológica no artigo.

**Implementar:** `src/analise_temporal.py` — série mensal estadual, 2022 a
2025, por natureza, a partir de `ssp_painel.csv`.

**Decidir:** a aba `METODOLOGIA` da SSP diz que o R.D.O. foi substituído pelo
S.P.J. "entre 2022 e 2023". Se houver **degrau visível em 2023**, a migração
ainda estava em curso e a janela encolhe para `[2024, 2025]`. Se a série for
contínua, 2023–2025 está confirmado.

**Entregáveis:** `Figura 1` (série mensal 2022–2025) + parágrafo de
justificativa na Metodologia.

---

## FASE 2 — Exploratória e seleção de variáveis · 05–07/09

**Implementar:** `src/exploratoria.py`

- Descritivas das 9 taxas: média, mediana, desvio, máximo, **% de zeros**.
- Distribuições antes e depois de `log1p` (mostra por que a transformação é
  necessária).
- **Matriz de correlação de Spearman** — prometida na §3.2 do tex e ainda não
  feita. Spearman, não Pearson: as taxas não são normais.
- Poda: onde |ρ| > 0,85, fundir ou descartar. Registrar o que saiu e por quê.

**Entregáveis:** `Tabela 2` (descritivas + zero-inflação), `Figura 2` (matriz
de correlação), conjunto final de features documentado.

---

## FASE 3 — Pré-processamento · 07–08/09

**Implementar:** `src/preprocessamento.py`

1. Ler `dicionario_base.csv` para saber bloco e papel de cada coluna — nunca
   listar colunas na mão.
2. Filtrar: excluir `flag_sem_iegm` (a capital, que não tem IEGM).
3. `log1p` nas taxas e no PIB per capita; depois `RobustScaler`, **ajustado só
   no subconjunto efetivamente clusterizado**.
4. **Peso por bloco `1/√n`**, para que criminalidade (9), socioeconômico (2) e
   gestão (8) contribuam igualmente. Sem isso o IEGM leva ~40% do orçamento de
   distância só por ter mais colunas, carregando pouquíssima variância
   (`i_planejamento` tem 83% dos municípios no conceito `C`).
5. PCA sobre a matriz padronizada — necessária para o DBSCAN (Fase 4) e é a
   abordagem de González et al., já citada no tex.

**Entregáveis:** matriz `X` pronta + `Figura 3` (variância explicada acumulada).

---

## FASE 4 — Clusterização e comparação · 09–11/09

O núcleo do que o artigo promete na §3.3.

**Implementar:** `src/clusterizacao.py`

| Algoritmo | Seleção de parâmetro |
|---|---|
| K-means | cotovelo + silhueta + Calinski–Harabasz, para k = 2..10 |
| Hierárquico aglomerativo | dendrograma + as mesmas três métricas |
| DBSCAN | gráfico da distância ao k-ésimo vizinho, **sobre as componentes do PCA** |

> Expectativa realista: com 644 pontos em ~19 dimensões, o DBSCAN tende a
> rotular quase tudo como ruído. **"DBSCAN degenerou" é resultado comparativo
> legítimo**, não fracasso — desde que reportado com o gráfico de k-distância
> que mostra a ausência de um "joelho". É justamente o tipo de comparação
> sistemática que a §2 do tex aponta como lacuna da literatura.

**Entregáveis:** `Tabela 3` (comparação dos 3 algoritmos × silhueta,
Calinski–Harabasz, Davies–Bouldin), `Figura 4` (seleção de k).

---

## FASE 5 — Caracterização preliminar dos perfis · 11–12/09

**Implementar:** `src/perfis.py`

- Médias e medianas por variável em cada grupo.
- **Heatmap de médias padronizadas** (mais legível que radar quando há ~19
  variáveis; guardem o radar para 5–6 variáveis-resumo).
- Kruskal–Wallis entre grupos, reportando **tamanho de efeito (ε²)** e não
  p-valor: nas variáveis que construíram os clusters, o teste sempre rejeita.
  Use `papel = validacao_externa` do dicionário (`prop_via_publica`) como
  variável de validação genuinamente externa.
- Nomear os perfis encontrados (ex.: "polo urbano de alta criminalidade
  patrimonial", "interior de baixa incidência e gestão frágil").

**Cortável:** mapa coroplético. `geopandas` + malha municipal do IBGE é a peça
mais cara do projeto e a §3.4 pode ficar como trabalho futuro nesta entrega
parcial. **Não iniciem se a Fase 4 escorregar.**

**Entregáveis:** `Figura 5` (heatmap de perfis), `Tabela 4` (perfis × variáveis).

---

## FASE 6 — Escrita conceitual · 02–10/09 · **COMEÇA HOJE, EM PARALELO**

Zero dependência de dados. É a trilha que garante a entrega.

### 6.1 Introdução: 0,6 p → 2 p

Faltam ~950 palavras. O que acrescentar:

- Dimensionar o problema com números (taxas de homicídio em SP, dispersão
  entre municípios) — hoje a introdução é qualitativa demais.
- **Citar a literatura de desorganização social.** A linha 48 do tex invoca
  "literatura sobre desorganização social e vulnerabilidade urbana" **sem
  nenhuma citação**. Shaw & McKay e Sampson são as referências canônicas.
- Explicitar as perguntas de pesquisa e a estrutura do artigo.

### 6.2 Trabalhos Correlatos: 0,9 p → 3 p

Faltam ~1.400 palavras. Em ordem de custo-benefício:

1. **Promover `silva2025` e `soliani2024`.** Ambos já são citados (na
   Introdução e na Metodologia) mas **nunca discutidos na §2**. São ~2
   parágrafos de ganho imediato, sem leitura nova.
2. **Tabela comparativa** — o item de maior valor. Colunas sugeridas:
   `trabalho | recorte | fonte de dados | método | validação | integra gestão pública?`.
   Torna visual a lacuna que a §2 afirma em prosa, e ocupa meia página
   legitimamente.
3. **Buscar 2 trabalhos novos**, preenchendo os buracos que a tabela vai
   expor: clusterização de municípios brasileiros e algum estudo que use o
   IEGM como variável.

### 6.3 Título e resumo

Aplicar o título revisado (§1). Atualizar resumo e *abstract* para mencionar
que há resultados parciais — hoje ambos estão inteiramente no futuro.

**Entregáveis:** seções 1 e 2 do tex fechadas até 10/09.

---

## FASE 7 — Escrita dos resultados · 12–15/09 · **TODO O GRUPO**

### 7.1 Metodologia (2 p) — reescrever no passado

Incorporar as decisões que hoje só existem no código e no README:

- Janela 2023–2025 e sua justificativa empírica (Fase 1).
- Junção por `codigo_ibge`; município de **circunscrição** (local do fato), não
  o de registro — `NOME_MUNICIPIO` é ambíguo, 267 nomes com mais de um código.
- Taxa por 100 mil habitantes-ano com denominador de população 2024.
- **CVLI** agregando homicídio doloso + latrocínio + lesão seguida de morte.
- Naturezas excluídas e por quê (culposos de trânsito; porte/apreensão, que
  medem policiamento e não incidência).
- Exclusão da capital: São Paulo é fiscalizada pelo TCM-SP e não tem IEGM.
- Peso por bloco e transformações.

### 7.2 Resultados Parciais (3 p) — seção nova

Praticamente toda em figuras e tabelas, o que a torna a seção mais rápida de
escrever. Ordem sugerida:

| Elemento | Origem |
|---|---|
| Tabela 1 — composição da base (fontes, n, cobertura, ausentes) | Fase 0 |
| Figura 1 — série mensal 2022–2025 e validação da janela | Fase 1 |
| Tabela 2 — descritivas das taxas + zero-inflação | Fase 2 |
| Figura 2 — correlação de Spearman | Fase 2 |
| Figura 4 — seleção de k | Fase 4 |
| Tabela 3 — comparação dos 3 algoritmos | Fase 4 |
| Figura 5 — heatmap dos perfis | Fase 5 |

### 7.3 Discussão e Conclusão (1 p) — seção nova

- O que os perfis preliminares sugerem sobre crime × gestão × vulnerabilidade.
- **Limitações, declaradas de frente** (fortalece o texto, não enfraquece):
  anos de referência heterogêneos (crime 2023–25, IEGM exercício 2024, PIB
  2023, urbanização Censo 2022); capital fora da análise; problema dos números
  pequenos — 148 municípios (23%) abaixo de 5.000 hab., onde uma única
  ocorrência distorce a taxa; `taxa_trafico` mede também intensidade de
  policiamento.
- Próximos passos: mapas coropléticos, análise de estabilidade, encolhimento
  bayesiano das taxas.

---

## FASE 8 — Fechamento · 15–16/09

- [ ] Contagem de páginas por seção, dentro dos tetos
- [ ] Seção `Cronograma` removida
- [ ] Todas as citações resolvidas no `.bib` (hoje são 10)
- [ ] Figuras legíveis em escala de cinza e com legenda autoexplicativa
- [ ] Compilação limpa, sem `??` de referência quebrada
- [ ] PDF submetido — **não deixem para as 23h**

---

## 4. Riscos e plano de corte

| Risco | Mitigação |
|---|---|
| `.bib` / template não existem | **Verificar hoje** (§1). É o risco mais bobo e mais fatal. |
| Download da SSP falha ou demora | Trilha B garante 5 das 7 seções mesmo assim. |
| Degrau em 2023 (Fase 1) | Janela encolhe para `[2024, 2025]`. Nenhum código muda, só `config.py`. |
| Modelagem atrasa | Ver ordem de corte abaixo. |

**Ordem de corte, se 12/09 chegar com a Trilha A atrasada:**

1. Cortar o **mapa coroplético** (Fase 5) → vira trabalho futuro.
2. Cortar o **DBSCAN** → reportar K-means e hierárquico, e declarar o DBSCAN
   como próxima etapa.
3. Cortar a **caracterização de perfis** (Fase 5) → Resultados Parciais fecha
   na comparação de algoritmos (Fase 4), que já é substancial.

**O que nunca cortar:** Fases 0, 2 e 6. Sem base consolidada, sem análise
exploratória e sem as seções conceituais, não há entrega.

---

## 5. Calendário

| Dias | Trilha A | Trilha B |
|---|---|---|
| 02–04/09 | **Fase 0** — completar bases | **Fase 6** — Introdução |
| 04–05/09 | **Fase 1** — validar janela | Fase 6 — Trabalhos Correlatos |
| 05–07/09 | **Fase 2** — exploratória | Fase 6 — tabela comparativa |
| 07–08/09 | **Fase 3** — pré-processamento | Fase 6 — busca de 2 trabalhos |
| 09–11/09 | **Fase 4** — clusterização | Fase 6 — fechar seções 1 e 2 |
| 11–12/09 | **Fase 5** — perfis | revisão cruzada |
| 12–15/09 | **Fase 7** — escrita dos resultados (todo o grupo) | |
| 15–16/09 | **Fase 8** — fechamento e submissão | |

**Marcos de verificação:**

- **04/09** — `base_final.csv` com janela 2023–2025 gerada.
- **10/09** — Introdução e Trabalhos Correlatos fechados (5 das 11 páginas).
- **12/09** — todas as figuras e tabelas dos Resultados Parciais geradas.
- **15/09** — PDF compilando dentro dos tetos de página.
