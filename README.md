# RP2 — Construção da base de dados

Pipeline que integra SSP-SP, IEGM/TCE-SP e SIDRA/IBGE em uma única base com
**uma linha por município** do estado de São Paulo.

> **Estado do projeto, o que falta e o changelog:** [ANDAMENTO.md](ANDAMENTO.md).
> Este README explica como rodar; o [PLANEJAMENTO.md](PLANEJAMENTO.md) é o
> plano e o cronograma.

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

> ⚠ **Os nomes das colunas mudam de ano para ano.** A SSP renomeou campos
> entre os exports, e a aba de dicionário de dados às vezes documenta o nome
> *antigo*. Casos já conhecidos: o código do município é `CD_IBGE` em
> 2023–2025 mas `COD IBGE` em 2026 (embora o dicionário diga "COD IBGE" nos
> três anos); `DESCR_TIPOLOCAL` só existe em 2025; veículos e celulares usam
> `ANO`/`MES` em 2023–2024 e `ANO_REGISTRO_BO`/`MES_REGISTRO_BO` em 2025.
>
> Por isso toda coluna é resolvida por uma **lista de apelidos**, em
> `APELIDOS_*` no topo de `src/parse_ssp.py`. Se um ano novo quebrar, é o
> único lugar a mexer. Preste atenção ao aviso `nenhuma aba de dados
> reconhecida`: um nome de coluna errado não gera erro, gera **painel
> vazio**.

## 2. Baixar manualmente: IEGM/TCE-SP

Em <https://www.tce.sp.gov.br/iegm>, baixe as planilhas de resultados e
jogue todas em `data/raw/ieg-m/`. **O nome do arquivo não importa** — o
pipeline lê todos os `.xls` da pasta e se orienta pela coluna `exercicio_ref`
de dentro de cada planilha. Isso não é preciosismo: em disco,
`ieg_m_2025.xls` é o exercício **2022**.

Quanto mais exercícios, melhor. Estão em uso os exercícios 2022, 2023 e 2024
(apurados em 2023, 2024 e 2025 — a mesma janela do crime), e as colunas
`*_ord` da base são a **média** deles. Um exercício isolado é um ponto único
com 4–5 níveis muito concentrados (`i_planejamento` tem 83% dos municípios em
`C`); a média dos três devolve variância ao bloco de gestão — de 4 níveis
distintos para 10 nessa mesma coluna. As colunas `*_conceito` guardam a letra
do exercício mais recente, como rótulo legível, e por isso **não
correspondem** ao valor de `*_ord`.

## 3. Rodar

```bash
python main.py            # roda o que faltar
python main.py --forcar   # reprocessa os .xlsx da SSP do zero
```

Saídas em `data/processed/`:

| Arquivo | O que é |
|---|---|
| `ssp_painel.csv` | município × ano × **mês** × natureza → contagem |
| `ssp_textura.csv` | município × ano → local/período das ocorrências |
| `ssp_complementar.csv` | município × ano → veículos e celulares subtraídos |
| `ssp_cobertura.csv` | ano → nº de meses observados |
| **`base_final.csv`** | **uma linha por município — a base da análise** |
| `dicionario_base.csv` | coluna → bloco, tipo, papel na modelagem |
| `relatorio_base.txt` | ausentes, zero-inflação, balanço de features |
| `tabela2_descritivas.csv` | gerado pelo notebook da Fase 2 |

**O painel é mensal, a base é anual.** Mês é um superconjunto barato — o
`merge_bases.py` soma sobre ele sem precisar saber que existe — e é o que
permite a série mensal da Fase 1 sem reprocessar 4,8 milhões de linhas a cada
pergunta sobre sazonalidade. Ocorrências sem `MES_ESTATISTICA` recebem
`mes = 0` e continuam contando no total anual; quem faz série mensal filtra
`mes > 0`.

**O painel cobre 2022, a base não.** 2022 entra como série de controle para a
validação da janela e é descartado pelo filtro `ANOS_JANELA` do
`merge_bases.py`. Conferido: incluir 2022 no painel não altera uma linha
sequer de `base_final.csv`.

A camada intermediária existe porque agregar os microdados custa minutos e
centenas de MB de leitura. Ela também é o que viabiliza a **análise de
estabilidade** da seção 3.3: reclusterizar em 2023–2024 vs. 2024–2025 e
comparar as partições por Adjusted Rand Index, sem reprocessar nada.

## Recorte temporal

Configurado em `src/config.py` (`ANOS_JANELA`). `None` = usa tudo que houver.

**Em uso: `[2023, 2024, 2025]`** — três anos civis completos (cada arquivo
traz `JAN-JUN` + `JUL-DEZ`, logo `exposicao_anos = 3,000` exatos). Motivos:

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
Censo/recalibração): os períodos vão de 2021 direto para 2024 — verificado na
API. Por isso a janela 2023–2025 usa **a população de 2024 como referência
única** (`ANO_POPULACAO_REF`), o ponto médio da janela. Documentem a escolha.

### Armadilha da urbanização: tabela 202 ≠ Censo 2022

`taxa_urbanizacao` vem da tabela **9923** (Censo 2022), não da 202. A 202 é do
Censo antigo e seus períodos publicados param em **2010**; pedir
`period="last"` nela devolve o Censo 2010 **sem erro nenhum** — 15 anos de
defasagem numa das duas únicas features do bloco socioeconômico.

## Notas para a modelagem

O `dicionario_base.csv` diz o bloco e o papel de cada coluna. Leiam ele em vez
de listar colunas na mão — é o que permite:

1. **Pesar os blocos.** São 19 features: 9 de criminalidade, 2 de
   socioeconômico e 8 de gestão. Sem peso, cada bloco influencia a distância
   na proporção do nº de colunas que a fonte por acaso tem — o IEGM levaria
   ~40% do orçamento. Sugestão: peso `1/sqrt(n)` por bloco (0,333 / 0,707 /
   0,354, calculados no `relatorio_base.txt`).
2. **Transformar.** `log1p` nas taxas e no PIB per capita (fortemente
   assimétricos), depois `RobustScaler` — **ajustado só no subconjunto
   efetivamente clusterizado**, e não na base inteira.
3. **Segurar variáveis de validação externa.** `papel = validacao_externa`
   marca `prop_via_publica`, propositalmente fora das features, para que os
   testes da seção 3.4 não sejam circulares. Nas variáveis que *entraram* na
   clusterização, reportem **tamanho de efeito** (ε², η²) em vez de p-valor.
4. **Números pequenos.** A mediana populacional de SP é 13.399 hab. e **149
   municípios (23,1%)** têm menos de 5.000. O efeito aparece cru na base: o
   máximo de `taxa_cvli` é Balbinos (3.963 hab.) e o de `taxa_estupro_total`
   é Guarani d'Oeste (1.999 hab.) — não são os municípios mais violentos de
   SP, são os menores denominadores. A base marca `flag_pop_pequena`; rodem a
   clusterização com e sem esses municípios e comparem por Adjusted Rand
   Index.
5. **Ausentes.** Só 44 municípios (6,8%) têm `taxa_recuperacao_veiculo` e
   `prop_veiculo_motocicleta` nulos — são os que não tiveram nenhum veículo
   subtraído em três anos, então o `NaN` é a resposta correta, não uma falha
   de coleta. As 8 colunas do IEGM faltam só na capital (`flag_sem_iegm`).
   Nenhuma outra coluna tem ausente.

## 4. Análise, em notebooks

```
notebooks/01_validacao_temporal.ipynb   Fase 1 — Figura 1
notebooks/02_exploratoria.ipynb         Fase 2 — Tabela 2 e Figura 2
notebooks/03_preprocessamento.ipynb     Fase 3 — Figura 3 + matriz_modelagem.csv
```

Todos rodam sobre `data/processed/`; nenhum reprocessa microdado. As figuras
saem em `figuras/`, prontas para subir no Overleaf.

> ⚠ **Cuidado com o kernel.** Há mais de um Python instalado na máquina e nem
> todos têm as dependências. Se o notebook der `ModuleNotFoundError` no
> primeiro import, use *Select Kernel* no canto superior direito e escolha o
> interpretador onde você rodou o `pip install -r requirements.txt`. A
> primeira célula imprime `sys.executable` justamente para você conferir qual
> está ativo.

**Conclusão da Fase 1:** a janela 2023–2025 foi **confirmada**. A série
mensal não tem degrau em jan/2023; das dez naturezas, cinco sobem e cinco
descem na virada 2022→2023, com magnitude mediana (~6%) igual à das viradas
seguintes. As duas únicas naturezas que destoam são `cvli` e `estupro_total`
— justamente as menos sensíveis ao sistema de registro, o oposto do que a
hipótese de artefato de migração previria.

**Conclusão da Fase 2:** nenhum par de features passa de |ρ| > 0,85 (máximo
0,76, `roubo_outros × roubo_veiculo`), então **as 19 features seguem inteiras**
— não há poda. E `log1p` deve ser mantido: a assimetria negativa que ele
parece introduzir é zero-inflação reaparecendo, não excesso de correção
(retirando os zeros, toda assimetria pós-`log1p` cai para a faixa −0,5 a
+0,7).

**Conclusão da Fase 3:** o escalonamento é `StandardScaler`, e **não**
`RobustScaler` como o plano previa. O peso `1/√n` por bloco é deduzido supondo
que cada coluna padronizada valha uma unidade de variância — o que só o
`StandardScaler` garante. Com ele os blocos ficam em 33,3% cada; com
`RobustScaler` ficavam em 37/33/30 e a segunda componente principal era
**uma variável só** (`i_planejamento_ord`, carga 0,88, porque seu IQR de 0,333
fazia o escalonador multiplicá-la por três). São necessárias **9 componentes
para 80% da variância**: não há estrutura de baixa dimensão, o que reforça que
os três blocos são complementares.

## Estrutura

```
rp2_inicial/
├── main.py                    # orquestra as 4 etapas
├── requirements.txt
├── src/
│   ├── config.py              # caminhos, janela temporal, agrupamento de naturezas
│   ├── ibge_sidra.py          # SIDRA — automático
│   ├── parse_ssp.py           # microdados da SSP -> painel mensal (streaming)
│   ├── parse_iegm.py          # .xls legado do IEGM -> conceitos + ordinais
│   ├── merge_bases.py         # une tudo por codigo_ibge -> base final
│   └── estilo.py              # paleta validada e rcParams das figuras
├── notebooks/                 # análise (Fases 1 e 2)
├── figuras/                   # saída das figuras do artigo
└── data/
    ├── raw/{ssp,ieg-m,ibge}/
    └── processed/
```

## Decisões de dados que valem registro no relatório

- **Junção por `codigo_ibge`**, nunca por nome. A SSP traz `CD_IBGE` e o IEGM
  traz `codigo_municipio`. Medido na janela 2023–2025: dos 674 valores
  distintos de `NOME_MUNICIPIO`, **492 apontam para mais de um código IBGE**.
  Cuidado com a leitura desse número: a causa principal não é grafia ambígua,
  é que o município de **registro** não determina o do **fato** — a mesma
  delegacia registra ocorrências de várias circunscrições. Casar por nome
  atribuiria o crime à cidade onde o BO foi feito. O `parse_ssp.py` refaz
  essa medição a cada execução; leiam o log em vez de confiar no número aqui.
- **Município = circunscrição** (local do fato), não o de registro. Medido na
  janela: registro ≠ circunscrição em **12.219 de 3.594.857 linhas (0,34%)** —
  0,37% em 2023, 0,34% em 2024, 0,31% em 2025.

  > **Não confundam esse 0,34% com os "cerca de 60%" da aba `METODOLOGIA` da
  > SSP.** Os dois medem coisas diferentes: a SSP fala de **delegacia** de
  > circunscrição, e um BO registrado noutra delegacia do *mesmo* município
  > entra naqueles 60% sem mudar de município. Nossa medida é municipal, que é
  > a unidade da análise. Os 60% justificam por que não se deve usar a
  > delegacia; o 0,34% é o tamanho real do erro que estaríamos cometendo na
  > unidade que importa.

  O `CD_IBGE` acompanha o município de circunscrição: 645 códigos, e o único
  código com duas grafias é 3547908 (`S.ANTONIO DA ALEGRIA` / `SANTO ANTONIO
  DA ALEGRIA`) — mesmo município, abreviação diferente. Outro motivo para não
  casar por nome.
- **Ano = `ANO_ESTATISTICA`**, não `ANO_BO`: a SSP contabiliza pela entrada na
  estatística oficial, e há boletins registrados num ano sobre fatos de anos
  anteriores.
- **Contar linhas é contar ocorrências**, mas isso foi *medido*, não suposto.
  A `METODOLOGIA` da SSP avisa que cada linha é uma pessoa/natureza/objeto do
  boletim, então um BO com três vítimas viraria três linhas. O `parse_ssp.py`
  compara o total de linhas com o de chaves `(delegacia, ano_bo, num_bo,
  natureza)` distintas: a repetição é de **0,01%** em 2023 e 2024 e 0,00% em
  2025 — desprezível.
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
- **IEGM = média de três exercícios** (2022, 2023 e 2024), e não um ponto
  único. Ver a seção 2 acima.
- **Anos de referência são heterogêneos** — crime 2023–2025, IEGM exercícios
  2022–2024, PIB 2023, população 2024, urbanização Censo 2022. Cada fonte
  publica no seu calendário; isto é uma limitação a **declarar** na Discussão,
  e o `relatorio_base.txt` já traz o quadro pronto para copiar.
