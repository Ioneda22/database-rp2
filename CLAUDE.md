# RP2 — instruções para o Claude Code

Este arquivo fica na raiz do repositório `database-rp2`. O Claude Code lê ele
sozinho ao abrir o projeto. As tarefas desta entrega estão em `tarefas/`, uma
por arquivo, e devem ser feitas **uma de cada vez, na ordem**.

## 1. O projeto

Trabalho de Resolução de Problemas II (Sistemas de Informação, EACH-USP).
Três alunos do 6º semestre: Bruno, Guilherme e Higor.

Agrupamos os 645 municípios paulistas em perfis a partir de três blocos de
indicadores: criminalidade (SSP-SP), efetividade da gestão municipal
(IEGM/TCE-SP) e condição socioeconômica (IBGE). O artigo está no Overleaf
(template SBC), **não neste repositório**.

As três perguntas do artigo:

1. Os três blocos trazem informação complementar ou repetida? **(respondida)**
2. Qual algoritmo (K-means, hierárquico de Ward ou DBSCAN) dá o melhor
   equilíbrio entre qualidade estatística e interpretabilidade? **(esta entrega)**
3. Que perfis aparecem e como se relacionam com a literatura? **(esta entrega)**

Entrega atual: relatório parcial + vídeo, prazo **21/10/2026, 23:59**.

## 2. O que já existe (não refazer)

| Arquivo | O que é |
|---|---|
| `main.py`, `src/parse_*.py`, `src/merge_bases.py`, `src/ibge_sidra.py` | Constroem a base. **Não mexer.** Os dados brutos não estão no repositório. |
| `data/processed/base_final.csv` | 645 municípios × 54 colunas. **Não alterar.** |
| `data/processed/dicionario_base.csv` | Bloco e papel de cada coluna. As features são as linhas com `papel == "feature"` (22). |
| `data/processed/ssp_painel.csv` | Ocorrências por município × ano × mês × natureza (2022–2025). |
| `data/processed/ssp_cobertura.csv` | Meses observados por ano (todos têm 12). |
| `data/processed/matriz_modelagem.csv` | 644 × 22, já transformada, padronizada e ponderada, + `codigo_ibge` e `municipio`. Insumo da clusterização. |
| `notebooks/01` a `03b` | Fases 1 a 3 (janela, exploratória, pré-processamento). **Não mudar os resultados.** |
| `src/config.py` | Constantes e caminhos. Número novo vai para cá, não fica solto no notebook. |
| `src/figuras.py` | Uma função por figura do artigo. |
| `src/estilo.py` | `aplicar_estilo()` e `salvar(fig, nome)`. |

## 3. Decisões já tomadas (não mudar sem a gente pedir)

- **Capital fora da modelagem** (`flag_sem_iegm`): 644 municípios.
- **22 features**: 9 de criminalidade, 6 socioeconômicas e 7 de gestão. A
  lista sai sempre do dicionário, ordenada por bloco
  (`ORDEM_BLOCOS = ["criminalidade", "socioeconomico", "gestao"]`) e por nome.
- **`log1p`** nas 9 taxas criminais e em `pib_percapita` e
  `renda_domiciliar_mediana`.
- **`StandardScaler`** ajustado só nos municípios que vão ser agrupados.
- **Peso `1/√n` por bloco** (n = número de colunas do bloco), para cada bloco
  valer um terço da distância.
- **Janela 2023–2025**, população de 2024, taxa por 100 mil habitantes por ano.
- **`prop_via_publica` é a variável de validação externa.** Nunca entra como
  feature.
- `flag_pop_pequena` marca os 149 municípios com menos de 5.000 habitantes.
  Eles ficam na modelagem; só saem no teste de estabilidade.
- **Reprodutibilidade**: `random_state=42` em tudo que sorteia; K-means com
  `n_init=50`.
- **A escolha final do modelo é do grupo.** O código calcula a tabela e aponta
  o que a regra de decisão sugere, mas quem preenche `ALGORITMO_ESCOLHIDO` e
  `K_ESCOLHIDO` no `config.py` somos nós.

## 4. Padrão de código

- Python 3, pandas, numpy, scikit-learn, scipy, matplotlib e seaborn. Os
  mapas usam geopandas. **Não adicionar biblioteca** fora do
  `requirements.txt` sem perguntar.
- **Regra das duas frases**: qualquer célula de notebook tem que poder ser
  explicada em duas frases por qualquer um de nós. O que não couber nisso vira
  função em `src/` (com docstring) ou vai para um apêndice.
- Funções de cálculo novas ficam em `src/` (ex.: `src/preprocessamento.py`,
  `src/clusterizacao.py`). O notebook prepara os dados, chama a função e mostra
  o resultado.
- Toda figura do artigo é uma função em `src/figuras.py`. Ela recebe os dados
  prontos e devolve a `Figure`, com uma docstring dizendo **o que a figura
  mostra e para que serve**. Quem salva é `salvar(fig, nome)`. Nada de
  `ax.text` posicionado à mão dentro de notebook.
- Cores: `C0`/`C1` para duas séries, `Blues` para valores em ordem, `RdBu`
  para valores com sinal (acima ou abaixo da média). As figuras precisam ser
  legíveis impressas em preto e branco.
- `from __future__ import annotations` e *type hints* simples nas funções
  novas, como no resto de `src/`.
- **Primeira célula de código** de todo notebook novo igual à dos notebooks
  existentes: o truque do `RAIZ` para achar `src/`, `aplicar_estilo()`,
  `print("Python:", sys.executable)` e leitura dos CSVs com
  `dtype={"codigo_ibge": str}`.
- Use `assert` para conferências que, se falharem, invalidam o resultado
  (como no notebook 01).

## 5. Como escrever comentários e textos (importante)

Quem lê o código somos nós: alunos de SI que sabem Python e pandas, mas **não
têm formação em estatística ou aprendizado de máquina**. Precisamos entender
cada linha e explicar tudo no vídeo. Os notebooks atuais são o modelo: leia o
`03_preprocessamento.ipynb` antes de escrever qualquer coisa.

### Comentários no código (`#`)

- Português com acentos, primeira pessoa do plural ("usamos", "tiramos",
  "para a gente conferir").
- Explicam **o porquê**, não repetem o que a linha faz.
- Frases curtas e vocabulário simples. Quando um termo técnico aparecer pela
  primeira vez, explicar em linguagem comum na mesma frase.
- Quando usar algo de pandas ou numpy que não é óbvio, explicar em uma linha
  (como o notebook 02 faz com `~` e o 01 com `nunique()`).
- Sem jargão sem explicação ("ortogonal", "variedade", "espaço latente",
  "heterocedástico"), sem fórmula longa em comentário e sem anglicismo quando
  existe palavra em português ("semente", não "seed", exceto no nome do
  parâmetro `random_state`).

Exemplo do nosso padrão:

```python
# n_init=50: o K-means começa sorteando os centros, e sorteios diferentes
# podem dar grupos diferentes. Rodamos 50 vezes e ficamos com a melhor.
km = KMeans(n_clusters=k, n_init=N_INIT, random_state=RANDOM_STATE)
```

Exemplo do que **não** queremos:

```python
# Inicializa o KMeans com 50 inicializações para mitigar mínimos locais
# da função objetivo (inércia intra-cluster) e garantir convergência.
```

### Células de Markdown

- Mesmo registro do artigo: impessoal e formal ("Este notebook compara...",
  "de modo a", "de maneira que"), como nos notebooks 01 a 03.
- A primeira célula diz **o que o notebook faz**, **quais figuras e tabelas
  do artigo saem dele** e, quando houver, **qual critério foi definido antes de
  rodar**.
- Siglas por extenso na primeira vez (ARI: índice de Rand ajustado).
- Títulos no formato `## 1. Título` e `## 2. Figura 4 - seleção de k`.
- **Nunca** escrever conclusão sobre um resultado antes de a célula que o
  produz ter rodado. Todo número citado em Markdown tem que ser conferido com a
  saída da célula logo acima. Se um número mudar, o texto muda junto.
- Não inventar referência bibliográfica. Se um texto precisar de citação,
  deixar `[CITAÇÃO?]` e avisar a gente.

### Docstrings

Uma ou duas frases: o que a função recebe, o que devolve e para que serve no
projeto. Nas funções de figura, "Mostra ... Serve para ...", como em
`plot_variancia_pca`.

## 6. Nomes de saída

| Tipo | Onde | Nome |
|---|---|---|
| Figuras do artigo | `figuras/` | `figura4_selecao_k`, `figura5_perfis`, `figura6_mapa_perfis` |
| Figuras de apoio | `figuras/` | `figura_<assunto>` (ex.: `figura_dendrograma`) |
| Tabelas | `data/processed/` | `tabela_<assunto>.csv` (sem número: a numeração das tabelas no artigo vai mudar) |
| Resultados intermediários | `data/processed/` | nome descritivo (ex.: `metricas_clusterizacao.csv`, `perfis.csv`) |

## 7. Como rodar e conferir

- Os dados processados estão versionados, então **não é preciso rodar o
  `main.py`**.
- Para executar um notebook e salvar as saídas nele:
  `jupyter nbconvert --to notebook --execute --inplace notebooks/<nome>.ipynb`
- A máquina é Windows e tem mais de um Python. O que tem as bibliotecas é
  `C:\Python314\python.exe`. Se der `ModuleNotFoundError`, verifique o
  interpretador antes de instalar qualquer coisa.
- Ao terminar cada tarefa: rodar o notebook do início ao fim, conferir os
  critérios de aceite da tarefa e mostrar para a gente um resumo do que mudou
  e os números principais.

## 8. Ao terminar cada tarefa

- Adicionar uma entrada no topo do changelog do `ANDAMENTO.md`, no mesmo
  formato das anteriores (`### [dd/mm/aaaa] Título`, depois **Adicionado**,
  **Alterado** e **Números** quando houver).
- Mensagem de commit em português, no imperativo e curta, como as que já
  existem (ex.: "Adiciona notebook 04 de clusterização"). **Não fazer push**:
  quem faz push somos nós, depois de revisar.

## 9. O que não fazer

- Não alterar `base_final.csv`, `dicionario_base.csv`, `matriz_modelagem.csv`
  nem os resultados dos notebooks 01 a 03b.
- Não escolher o modelo final por conta própria.
- Não editar textos do artigo (ele não está aqui).
- Não versionar nada em `data/raw/` (o `.gitignore` já bloqueia).
- Não "melhorar" decisões da seção 3 sem perguntar, mesmo que pareçam
  discutíveis. Se achar um problema, avisar.
