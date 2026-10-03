# T4b — Notebook 07: validação externa e mapa

**Responsável:** Guilherme · **Prazo:** parte 1 no sábado 03/10; parte 2 na sexta 09/10 · **Tempo estimado:** 2h com revisão

## Por que

- **Validação externa.** Testar se os perfis diferem em roubo, quando o roubo
  foi usado para formar os perfis, é circular: o teste sempre "passa". Por
  isso reservamos a `prop_via_publica` (proporção de ocorrências em via
  pública), que **não entrou na modelagem**. Se os perfis diferem nela, eles
  capturam algo real sobre os municípios. É o mesmo cuidado do estudo de São
  Carlos citado no artigo (Kruskal–Wallis com tamanho de efeito ε²).
- **Mapa.** Mostra se os perfis têm uma geografia (Grande São Paulo, litoral,
  Vale do Ribeira, oeste). O artigo promete mapas coropléticos na seção 3.3.

A **parte 1** (malha e mapa de teste) não depende da escolha do modelo e pode
ser feita antes da aula de 07/10. A **parte 2** depende do `perfis.csv`.

## O que implementar

### Parte 1 — malha municipal

`src/malha.py` com `carregar_malha_sp() -> geopandas.GeoDataFrame`:

- Baixa uma vez e guarda em `data/raw/ibge/malha_sp_municipios.geojson` (fica
  fora do Git, como os outros dados brutos). Nas próximas vezes, lê do disco.
- Fonte principal: API de malhas do IBGE,
  `https://servicodados.ibge.gov.br/api/v3/malhas/estados/35?formato=application/vnd.geo+json&intrarregiao=municipio&qualidade=intermediaria`.
  O código do município costuma vir na propriedade `codarea`. **Conferir na
  resposta real** antes de usar.
- Se a API não responder, alternativa: a malha municipal 2022 do IBGE para SP
  em shapefile (`SP_Municipios_2022.zip`, no geoftp do IBGE, coluna
  `CD_MUN`). Conferir o endereço antes de usar.
- Devolve um `GeoDataFrame` com a coluna `codigo_ibge` como texto de 7
  dígitos. `assert` de que os 645 códigos da `base_final.csv` estão na malha.

Função nova em `src/figuras.py` (seção `# Fase 5 - perfis`):

- `plot_mapa_categorias(gdf, coluna, rotulos, titulo) -> Figure` —
  **Figura 6** quando usada com os perfis. Cores em ordem, tiradas de `Blues`
  (do perfil 1, mais claro, ao último, mais escuro), porque os perfis vão sair
  ordenados por condição socioeconômica na T3 e uma escala em ordem continua
  legível impressa em cinza. Municípios sem perfil (a capital) em cinza-claro
  com hachura, com a legenda "sem perfil (sem IEGM)". Borda dos municípios
  fina e cinza; sem eixos.

Teste da parte 1, no notebook (seção 0): desenhar o mapa com
`taxa_urbanizacao` dividida em 4 faixas, só para conferir a junção. Não salvar
essa figura.

Se o `geopandas` não instalar no Python da máquina, **parar e avisar**. O mapa
é o primeiro item cortável da entrega.

### Parte 2 — `notebooks/07_validacao_externa_mapa.ipynb`

- **Abertura.** Objetivo, saídas (Figura 6, `tabela_kruskal.csv`) e o
  critério, definido antes: a validação externa é feita só com
  `prop_via_publica`; o teste nas features é descritivo e circular.
- **`## 1. Validação externa`.** Kruskal–Wallis (`scipy.stats.kruskal`) da
  `prop_via_publica` entre os perfis. Reportar H, p-valor e
  `ε² = H / (n − 1)`. Markdown curto explicando, em linguagem comum: o teste
  pergunta se a variável muda de um perfil para outro; com 644 municípios,
  quase qualquer diferença tem p-valor pequeno, por isso o que importa é o
  tamanho do efeito ε² (de 0 a 1). Para a leitura, usar as faixas: abaixo de
  0,04 fraco; 0,04 a 0,16 moderado; 0,16 a 0,36 relativamente forte; 0,36 a
  0,64 forte. Boxplot de apoio (`figura_via_publica_perfis`), feito por uma
  função em `figuras.py`.
- **`## 2. Quais variáveis mais separam os perfis`.** O mesmo ε² para as 22
  features, ordenado. Markdown **destacando** que isto é descritivo: as
  features formaram os perfis, então o efeito é grande por construção. Serve
  para ajudar a dar nome aos perfis, não como validação.
- **`## 3. Figura 6 - mapa dos perfis`.** Juntar `perfis.csv` com a malha;
  `assert` de que os 644 municípios encontraram polígono. Salvar
  `figura6_mapa_perfis`.
- **`## 4. Leitura do mapa`.** Markdown escrito depois de rodar: onde cada
  perfil se concentra, citando regiões e 2 ou 3 municípios.

Salvar `data/processed/tabela_kruskal.csv` com `variavel`, `tipo`
(`validacao_externa` ou `feature`), `H`, `p_valor`, `epsilon2`.

## Critérios de aceite

- [ ] Malha carregando do disco na segunda execução, sem baixar de novo.
- [ ] `assert` dos 645 códigos e dos 644 perfis passando.
- [ ] `figura6_mapa_perfis.png` legível em preto e branco.
- [ ] `tabela_kruskal.csv` com 23 linhas (1 externa + 22 features).
- [ ] Entrada no changelog do `ANDAMENTO.md`.

## Prompts para colar no Claude Code

Parte 1:

> Leia o `CLAUDE.md` e `tarefas/T4b_validacao_externa_e_mapa.md`. Faça só a
> parte 1: `src/malha.py`, a função de mapa em `figuras.py` e a seção 0 do
> notebook 07 com o mapa de teste. Confira na resposta real da API qual
> propriedade tem o código do município. Me mostre o mapa de teste.

Parte 2 (depois de `perfis.csv` existir):

> Agora faça a parte 2 de `tarefas/T4b_validacao_externa_e_mapa.md`. Rode o
> notebook 07 e me mostre o ε² da validação externa, a tabela ordenada e a
> Figura 6.
