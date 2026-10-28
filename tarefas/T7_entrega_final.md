# T7 — Entrega final: sensibilidade, taxas suavizadas, capital e relatório de resultados

**Para:** Claude Code, no repositório `database-rp2` · **Entrega final:** novembro de 2026

Este arquivo é o plano completo da entrega final. Ele tem quatro tarefas de
análise (T7a a T7d), uma de documentação (T7e) e, no fim, o **relatório de
resultados** que o grupo vai levar para atualizar o artigo. Siga as tarefas
na ordem e pare entre uma e outra para mostrar o resumo ao grupo.

---

## 0. Antes de começar

1. `git pull` e leia o `CLAUDE.md` inteiro. **Todas as regras dele valem
   aqui**: comentários no padrão do grupo, regra das duas frases, cálculo em
   `src/`, figura em `src/figuras.py`, número novo em `src/config.py`,
   `assert` nas conferências, nenhuma biblioteca fora do `requirements.txt`.
2. Leia o `ANDAMENTO.md` (seção 3.4 tem os números atuais) e os notebooks 03,
   05 e 07, que são o modelo de estilo.
3. **Não mude nada que já existe**: `base_final.csv`, `matriz_modelagem.csv`,
   `perfis.csv`, os notebooks 01 a 07 e os resultados deles. Tudo o que esta
   entrega produz é **novo** (notebooks 08 a 10, tabelas e figuras novas).
   Se perceber que algo existente precisaria mudar, pare e avise.
4. O modelo de referência continua sendo o do `config.py`
   (`ALGORITMO_ESCOLHIDO = "kmeans"`, `K_ESCOLHIDO = 4`) e a partição de
   referência é a do `data/processed/perfis.csv`. Todas as comparações desta
   entrega são contra ela.
5. Para comparar duas partições, use o ARI (índice de Rand ajustado), como no
   notebook 05. Quando precisar alinhar os números dos grupos (para tabelas
   cruzadas), renumere com `renumerar_por_socioeconomico`, como no notebook 05.

### Critério de leitura do ARI (definido antes de rodar)

Use as mesmas faixas nas tarefas T7a e T7b e escreva-as na primeira célula
de Markdown dos notebooks 08 e 09, **antes** das células que calculam:

| ARI | Leitura |
|---|---|
| ≥ 0,80 | os perfis se mantêm |
| 0,65 a 0,80 | os perfis mudam em parte; descrever quais |
| < 0,65 | os perfis dependem da mudança testada |

Coloque essas faixas no `config.py` como `FAIXAS_ARI`. **Se o grupo ainda
não confirmou essas faixas, pergunte antes de rodar.** Não troque as faixas
depois de ver o resultado.

---

## T7a — Notebook 08: sensibilidade a três variáveis

**Por que.** A Discussão do artigo aponta três variáveis com problemas
conhecidos: `taxa_trafico` (mede também a atuação da polícia),
`pib_percapita` (inflado por polos industriais) e `i_planejamento_ord` (70%
dos municípios com o mesmo valor). A pergunta é se os perfis mudam quando
cada uma sai.

**O que implementar** — `notebooks/08_sensibilidade.ipynb`:

1. Para cada uma das três variáveis, **separadamente**: tirar a coluna da
   lista de features, refazer a matriz com `montar_matriz` (o peso do bloco é
   recalculado sozinho), agrupar com o modelo do `config.py` e calcular o ARI
   contra o `perfis.csv`.
2. Uma quarta linha com **as três retiradas ao mesmo tempo**.
3. Para cada linha, uma tabela cruzada (perfil original × perfil novo,
   renumerado pelo critério socioeconômico) e o número de municípios que
   mudaram de perfil.
4. `assert` de que, em cada matriz refeita, cada bloco continua com um terço
   da variância (mesma função `orcamento` do notebook 03; pode virar função em
   `src/preprocessamento.py`).
5. Saída: `data/processed/tabela_sensibilidade.csv` com as colunas
   `variavel_retirada`, `bloco`, `n_colunas_no_bloco`, `ari`, `leitura`
   (faixa do ARI) e `municipios_que_mudaram`.
6. Markdown escrito **depois** de rodar: uma frase por linha da tabela, no
   registro do artigo, pronta para entrar no texto.

**Critérios de aceite**

- [ ] 4 linhas na tabela; o `assert` do um terço passa em todas.
- [ ] As tabelas cruzadas aparecem no notebook.
- [ ] Nenhum número no Markdown que não esteja na saída da célula acima.

---

## T7b — Notebook 09: taxas suavizadas dos municípios pequenos

**Por que.** O teste mais exigente da estabilidade foi retirar os 149
municípios com menos de 5.000 habitantes (ARI de 0,480 no modelo escolhido).
Nesses municípios, um caso a mais muda muito a taxa. O artigo cita Assunção
et al. (1998), que propõem suavizar as taxas por um método bayesiano
empírico: a taxa de um município pequeno é puxada para perto da média do
estado, na medida da incerteza dela. A pergunta é se os perfis se mantêm com
as taxas suavizadas e se a divisão fica mais estável.

**O que implementar**

1. Em `src/preprocessamento.py`, a função
   `suavizar_taxas(base, painel, cobertura, anos) -> pd.DataFrame`, que
   devolve uma cópia da base com as 9 taxas criminais suavizadas pelo
   **estimador bayesiano empírico global** (Marshall, 1991; é o estimador
   usado por Assunção et al., 1998). Para cada natureza criminal, com `y_i` =
   ocorrências do município na janela e `n_i` = população × exposição
   (pessoas-ano):

   ```
   r_i = y_i / n_i                       (taxa bruta)
   m   = soma(y) / soma(n)               (taxa do estado)
   s²  = soma(n_i * (r_i - m)²) / soma(n) - m / média(n)
   s²  = max(s², 0)
   C_i = s² / (s² + m / n_i)             (quanto confiar na taxa do município)
   r_suavizada_i = m + C_i * (r_i - m)
   ```

   Depois, multiplicar por 100 mil, como as taxas da base. Reaproveite
   `agregar_janela` e `exposicao_da_janela`, como faz `taxas_da_janela`.
   Docstring com a referência e uma frase explicando o `C_i`.
   **Antes de implementar, confira as fórmulas em uma fonte confiável** (o
   artigo de Assunção et al., 1998, ou a documentação do estimador de Marshall).
   Se encontrar diferença, use a da fonte e registre isso no relatório.
2. `notebooks/09_taxas_suavizadas.ipynb`:
   - Conferências: com taxas suavizadas, município grande quase não muda
     (`C_i` perto de 1); mostrar a mediana de `C_i` nos 149 pequenos e nos
     495 demais, para cada natureza.
   - Figura de apoio `figura_taxas_suavizadas`: taxa bruta × suavizada de
     CVLI, com os pequenos destacados (função nova em `src/figuras.py`).
   - Refazer a matriz com as taxas suavizadas (mesmo `montar_matriz`), agrupar
     com o modelo do `config.py` e calcular:
     - ARI contra o `perfis.csv` nos 644, nos 149 pequenos e nos 495 demais;
     - tabela cruzada perfil original × perfil com taxas suavizadas;
     - o teste "sem os municípios pequenos" (`ari_sem_pequenos`) **refeito
       sobre a base suavizada**, para comparar com o 0,480 original;
     - silhueta da partição suavizada, para comparar com 0,101.
   - Saídas: `data/processed/tabela_taxas_suavizadas.csv` (uma linha por
     medida acima, com o valor original e o novo lado a lado) e
     `data/processed/perfis_suavizados.csv` (código, município, perfil
     original, perfil suavizado).
   - Markdown depois de rodar, com a leitura pelas faixas do ARI.

**Critérios de aceite**

- [ ] `assert` de que as taxas suavizadas dos municípios com mais de 100 mil
      habitantes diferem menos de 5% das brutas (se falhar, investigar antes
      de seguir e registrar no relatório).
- [ ] Tabela com valores original e novo lado a lado.
- [ ] Nenhuma biblioteca nova (só numpy e pandas).

---

## T7c — Notebook 10: posição da capital nos perfis

**Por que.** A capital ficou fora da modelagem porque não tem IEGM. O artigo
lista isso como limitação e promete identificar de qual perfil ela mais se
aproxima.

**O que implementar** — `notebooks/10_capital.ipynb`:

1. Transformar os dados da capital **com a mesma escala dos 644**: aplicar o
   `log1p` e padronizar com a média e o desvio dos 644 (não refazer a
   padronização com a capital dentro). Usar só os blocos de criminalidade e
   socioeconômico, com os mesmos pesos da matriz original.
2. Calcular a distância da capital ao centro de cada um dos 4 perfis nesses
   15 colunas e apontar o perfil mais próximo.
3. **Teste de confiança do método:** aplicar a mesma regra (centro mais
   próximo, sem o bloco de gestão) aos 644 municípios e medir em quantos ela
   devolve o perfil original. Se acertar pouco, o resultado da capital vale
   pouco, e isso precisa ser dito.
4. Mostrar, para cada uma das 15 variáveis, o valor da capital em desvios em
   relação à média dos 644, ao lado da média de cada perfil. **Avisar quando
   a capital estiver fora da faixa dos 644** (por exemplo, a taxa de roubo da
   capital, cerca de 953 por 100 mil hab./ano, passa do máximo dos 644, que é
   752). Nesses casos o resultado é uma extrapolação.
5. Opcional: colocar o perfil apontado no mapa, como uma figura de apoio
   `figura_mapa_perfis_com_capital` (sem mudar a Figura 6).
6. Saída: `data/processed/tabela_capital.csv` com as distâncias aos 4 perfis
   e a taxa de acerto do teste do passo 3.

**Critérios de aceite**

- [ ] `assert` de que a escala usada é a dos 644 (média e desvio iguais aos
      da `montar_matriz` original).
- [ ] O Markdown diz o perfil mais próximo, a distância ao segundo mais
      próximo e a taxa de acerto do passo 3.

---

## T7d — Sugestões de nomes para os perfis

**Não decidir.** Os nomes são escolha do grupo. Para cada perfil, propor
**três opções** de nome curto (até quatro palavras), cada uma apoiada em
números da Figura 5 e da `tabela_perfis.csv`. Evitar nomes que sugiram causa
("violento", "mal administrado") ou julgamento; preferir nomes descritivos
("rural de maior privação", "urbano de gestão acima da média"). Colocar só no
relatório de resultados; não mudar figuras nem notebooks.

---

## T7e — README e ANDAMENTO

- `README.md`: notebooks 08 a 10 na seção 3.2; saídas novas nas seções 4.1 e
  4.2; função nova em `src/` na seção 5.
- `ANDAMENTO.md`: entrada no topo do changelog para cada tarefa
  (`### [dd/mm/aaaa] T7x — título`, com **Adicionado**, **Alterado** e
  **Números**) e a seção 3.4 com os números novos.
- Um commit por tarefa, mensagem curta em português no imperativo.
  **Não fazer push.**

---

## T7f — Relatório de resultados (obrigatório)

Ao terminar, criar o arquivo **`RESULTADOS_ENTREGA_FINAL.md` na raiz do
repositório**. É esse arquivo que o grupo vai entregar para atualizar o
artigo e o Documento de Domínio, então ele precisa ser **completo e
autossuficiente**: quem lê não terá acesso aos notebooks.

Regras do relatório:

- Todo número copiado da saída de uma célula ou de um CSV, com 3 casas
  decimais para ARI, silhueta e ε², e indicando de onde veio
  (`notebook 08, seção 2` ou `tabela_sensibilidade.csv`).
- Nada de interpretação além do que os números mostram. Nenhuma afirmação
  causal.
- Nenhuma referência bibliográfica inventada. Se uma frase precisar de
  citação, escrever `[CITAÇÃO?]` e dizer qual é a afirmação.
- Se alguma tarefa não foi feita ou foi feita de outro jeito, dizer isso
  explicitamente na seção da tarefa.

Estrutura obrigatória:

```markdown
# Resultados da entrega final

Data: dd/mm/aaaa · Commit: <hash curto do último commit>

## 1. Resumo
Cinco a oito linhas: o que foi feito e o principal resultado de cada tarefa,
com o número.

## 2. Critério de leitura do ARI
As faixas usadas e se o grupo as confirmou antes de rodar.

## 3. T7a — Sensibilidade
- O que foi feito (2 a 4 linhas).
- Tabela completa de tabela_sensibilidade.csv (em Markdown).
- As tabelas cruzadas (perfil original × novo) de cada linha.
- Uma frase por variável, no registro do artigo.
- Desvios do plano, se houver.

## 4. T7b — Taxas suavizadas
- Fórmula usada e a fonte conferida (com o link ou a referência completa).
- Mediana de C_i nos pequenos e nos demais, por natureza.
- Tabela original × suavizado (ARI 644 / 149 / 495, ARI sem pequenos,
  silhueta).
- Tabela cruzada perfil original × suavizado.
- Quantos e quais municípios mudaram de perfil (lista, se forem até 30).
- Frases prontas para o artigo.
- Desvios do plano, se houver.

## 5. T7c — Capital
- Perfil mais próximo, distâncias aos 4 perfis.
- Taxa de acerto do método nos 644.
- Tabela das 15 variáveis: capital em desvios × média de cada perfil,
  marcando as que estão fora da faixa dos 644.
- Frases prontas para o artigo, com a ressalva de extrapolação.

## 6. T7d — Sugestões de nomes
Tabela: perfil · três opções · números que apoiam cada uma.

## 7. Figuras e tabelas geradas
Lista de arquivos novos em figuras/ e data/processed/, com uma linha
dizendo o que cada um mostra e se serve para o artigo ou só de apoio.

## 8. O que muda no artigo
Para cada seção do artigo (Método 3.3, Resultados, Discussão: limitações e
trabalhos futuros, Resumo/Abstract), dizer o que deve ser acrescentado ou
alterado e por quê. Apontar quais limitações deixam de ser limitação e quais
trabalhos futuros saem da lista.

## 9. Pendências e avisos
Tudo o que ficou em aberto, falhou ou precisa de decisão do grupo.
```

---

## Prompts para colar no Claude Code

Use um prompt por vez, na ordem, e revise o resultado antes do próximo.

> **1.** Leia o `CLAUDE.md` e o `tarefas/T7_entrega_final.md` inteiro. Antes
> de escrever código, me mostre o critério de leitura do ARI da seção 0 e
> pergunte se o grupo confirma. Depois faça a T7a, rode o notebook 08 do
> início ao fim e me mostre a tabela e um resumo do que mudou.

> **2.** Faça a T7b do `tarefas/T7_entrega_final.md`. Antes de implementar
> `suavizar_taxas`, confira as fórmulas na fonte e me diga o que encontrou.
> Rode o notebook 09 e me mostre a tabela original × suavizado.

> **3.** Faça a T7c do `tarefas/T7_entrega_final.md`, rode o notebook 10 e me
> mostre o perfil mais próximo da capital e a taxa de acerto do método.

> **4.** Faça a T7d e a T7e do `tarefas/T7_entrega_final.md`.

> **5.** Faça a T7f: escreva o `RESULTADOS_ENTREGA_FINAL.md` seguindo
> exatamente a estrutura do plano, conferindo cada número com a saída das
> células e os CSVs. No fim, liste qualquer número que você não conseguiu
> conferir.
