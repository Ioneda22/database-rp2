# RP2 — Construção da base de dados

Pipeline que integra SSP-SP, IEGM/TCE-SP e SIDRA/IBGE em uma única base com
**uma linha por município** do estado de São Paulo.

## Desenho da pesquisa (etapa única)

Os três blocos — criminalidade, vulnerabilidade socioeconômica e efetividade
da gestão municipal — entram **juntos** no espaço de features da clusterização,
conforme `artigo.tex` (linhas 45–47 e 64). Não é "clusterizar por crime e
depois relacionar ao resto": a contribuição reivindicada no artigo é
justamente a integração simultânea das três fontes.

Consequência: **a capital fica fora da modelagem**. São Paulo é fiscalizada
pelo TCM-SP, não pelo TCE-SP, e por isso não tem nota IEGM — a base traz os
645 municípios com `flag_sem_iegm`, e o script de modelagem filtra os 644.

## Por que parte disso é manual

| Fonte | Tem API/link estático? |
|---|---|
| SIDRA/IBGE | **Sim** — API REST pública (`apisidra.ibge.gov.br`). 100% automático. |
| SSP-SP | Não — painel interativo, export sob demanda. |
| IEGM/TCE-SP | Não — mesma lógica. |

## 0. Instalação

```bash
python -m venv .venv && .venv\Scripts\activate    # Windows
pip install -r requirements.txt
```

## 1. Baixar manualmente: SSP-SP

Em <https://www.ssp.sp.gov.br/estatistica/consultas>, baixe os exports
**anuais** e salve em `data/raw/ssp/` mantendo os nomes originais:

```
data/raw/ssp/SPDadosCriminais_<ano>.xlsx     (obrigatório)
data/raw/ssp/VeiculosSubtraidos_<ano>.xlsx   (opcional — bloco de textura)
data/raw/ssp/CelularesSubtraidos_<ano>.xlsx  (opcional — bloco de textura)
```

O pipeline descobre sozinho quais anos existem. **Baixe 2023, 2024 e 2025** —
ver "Recorte temporal" abaixo.

## 2. Baixar manualmente: IEGM/TCE-SP

Em <https://www.tce.sp.gov.br/iegm>, baixe a planilha de resultados do
exercício mais recente e salve em `data/raw/ieg-m/ieg-m.xls`.

## 3. Rodar

```bash
python main.py            # roda o que faltar
python main.py --forcar   # reprocessa os .xlsx da SSP do zero
```

Saídas em `data/processed/`:

| Arquivo | O que é |
|---|---|
| `ssp_painel.csv` | município × ano × natureza → contagem (camada intermediária) |
| `ssp_textura.csv` | município × ano → local/período das ocorrências |
| `ssp_complementar.csv` | município × ano → veículos e celulares subtraídos |
| `ssp_cobertura.csv` | ano → nº de meses observados |
| **`base_final.csv`** | **uma linha por município — a base da análise** |
| `dicionario_base.csv` | coluna → bloco, tipo, papel na modelagem |
| `relatorio_base.txt` | ausentes, zero-inflação, balanço de features |

A camada intermediária existe porque agregar os microdados custa minutos e
centenas de MB de leitura. Ela também é o que viabiliza a **análise de
estabilidade** da seção 3.3: reclusterizar em 2023–2024 vs. 2024–2025 e
comparar as partições por Adjusted Rand Index, sem reprocessar nada.

## Recorte temporal

Configurado em `src/config.py` (`ANOS_JANELA`). `None` = usa tudo que houver.

**Recomendação: `[2023, 2024, 2025]`** — três anos civis completos. Motivos:

- **Pós-migração de sistema.** A aba `METODOLOGIA` dos arquivos da SSP diz que
  o R.D.O. foi substituído pelo S.P.J. "entre 2022 e 2023". Janelas que cruzam
  2022 misturam dois regimes de registro.
- **Pós-pandemia.** 2020–21 tiveram colapso de mobilidade: furto e roubo
  despencaram, homicídio quase não. Isso contamina a média com um choque
  exógeno.
- **Corta a zero-inflação pela metade.** Municípios sem nenhum CVLI, por
  estimativa Poisson sobre a população real: 1 ano → 46%; 2 anos → 31%;
  3 anos → 23%; 5 anos → 14%.
- **O IEGM cai no meio.** Exercício 2024 é o ano central da janela.

**Antes de fechar:** baixem 2022 também e plotem o total mensal estadual de
2022 a 2025. Se houver degrau visível em 2023, a migração ainda estava em
curso e a janela deve encolher para `[2024, 2025]`.

### Denominador das taxas

```
taxa = ocorrências_na_janela / (populacao_ref × exposicao_anos) × 100.000
```

`exposicao_anos` sai de `ssp_cobertura.csv` (meses observados ÷ 12, somados),
o que anualiza corretamente janelas com ano parcial.

A tabela 6579 do SIDRA **não publica estimativa para 2022 nem 2023** (anos de
Censo/recalibração): os períodos vão de 2021 direto para 2024. Por isso a
janela 2023–2025 usa **a população de 2024 como referência única** — o ponto
médio da janela. Documentem essa escolha.

## Notas para a modelagem

O `dicionario_base.csv` diz o bloco e o papel de cada coluna. Leiam ele em vez
de listar colunas na mão — é o que permite:

1. **Pesar os blocos.** Sem peso, cada bloco influencia a distância na
   proporção do nº de colunas que a fonte por acaso tem: 8 colunas do IEGM
   levariam ~40% do orçamento com quase nenhuma variância (`i_planejamento`
   tem 83% dos municípios no conceito `C`). Sugestão: peso `1/sqrt(n)` por
   bloco.
2. **Transformar.** `log1p` nas taxas e no PIB per capita (fortemente
   assimétricos), depois `RobustScaler` — **ajustado só no subconjunto
   efetivamente clusterizado**, e não na base inteira.
3. **Segurar variáveis de validação externa.** `papel = validacao_externa`
   marca colunas propositalmente fora das features (`taxa_urbanizacao`,
   `prop_via_publica`), para que os testes da seção 3.4 não sejam circulares.
   Nas variáveis que *entraram* na clusterização, reportem **tamanho de
   efeito** (ε², η²) em vez de p-valor.
4. **Números pequenos.** A mediana populacional de SP é ~13.500 hab. e 148
   municípios (23%) têm menos de 5.000 — em Borá (935 hab.), um único
   homicídio em 3 anos vira 35,7/100 mil/ano, 7× a média estadual. A base
   marca `flag_pop_pequena`; rodem a clusterização com e sem esses municípios
   e comparem por Adjusted Rand Index.

## Estrutura

```
rp2_inicial/
├── main.py                    # orquestra as 4 etapas
├── requirements.txt
├── src/
│   ├── config.py              # caminhos, janela temporal, agrupamento de naturezas
│   ├── ibge_sidra.py          # SIDRA — automático
│   ├── parse_ssp.py           # microdados da SSP -> painel (streaming)
│   ├── parse_iegm.py          # .xls legado do IEGM -> conceitos + ordinais
│   └── merge_bases.py         # une tudo por codigo_ibge -> base final
└── data/
    ├── raw/{ssp,ieg-m,ibge}/
    └── processed/
```

## Decisões de dados que valem registro no relatório

- **Junção por `codigo_ibge`**, nunca por nome. A SSP traz `COD IBGE` e o IEGM
  traz `codigo_municipio`. O `NOME_MUNICIPIO` da SSP é ambíguo — 267 nomes
  aparecem com mais de um código.
- **Município = circunscrição** (local do fato), não o de registro. Foi
  verificado que `COD IBGE` acompanha `NOME_MUNICIPIO_CIRCUNSCRICAO` 1:1.
- **Ano = `ANO_ESTATISTICA`**, não `ANO_BO`: a SSP contabiliza pela entrada na
  estatística oficial, e há boletins de 2026 sobre fatos de 2024/2025.
- **CVLI** agrega homicídio doloso + latrocínio + lesão seguida de morte —
  indicador padrão da literatura brasileira, e reduz a zero-inflação.
- **Fora do bloco de criminalidade:** culposos de trânsito (segurança viária,
  não criminalidade) e porte/apreensão de entorpecentes e de arma (medem
  policiamento, não incidência). `taxa_trafico` sofre da mesma crítica e foi
  mantida por medir presença de organização criminosa — registrem o caveat.
- **Veículos e celulares viram razão, não contagem.** Esses BOs já estão em
  `SPDadosCriminais`; somá-los seria dupla contagem. Deles extraímos taxa de
  recuperação de veículo, participação de motos e participação de celulares.
- **`PIB per capita` é recalculado** no `merge_bases.py`. O
  `ibge_pib_percapita.csv` gerado pelo `ibge_sidra.py` divide o PIB de 2023
  pela população de **2021** (consequência do buraco de 2022–23 na tabela
  6579), o que infla o per capita de municípios em crescimento.
