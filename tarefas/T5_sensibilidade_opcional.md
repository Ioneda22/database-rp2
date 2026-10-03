# T5 (opcional) — Notebook 08: sensibilidade a três variáveis

**Responsável:** Guilherme · **Prazo:** fim de semana 10–12/10 · **Tempo estimado:** 45 min

Só fazer se T1 a T4 estiverem prontas. Se não der tempo, vira próximo passo
na Discussão.

## Por que

A Discussão do artigo aponta três variáveis com problemas conhecidos:
`taxa_trafico` (mede também a atuação da polícia), `pib_percapita` (fica
inflado em cidades com polo industrial) e `i_planejamento_ord` (70% dos
municípios com o mesmo valor). A pergunta é: se uma delas sair, os perfis
mudam muito?

## O que implementar

`notebooks/08_sensibilidade.ipynb`:

- Para cada uma das três variáveis, separadamente: tirar a coluna da lista de
  features, refazer `montar_matriz` (o peso do bloco é recalculado sozinho,
  porque o bloco ficou com uma coluna a menos), agrupar com
  `ALGORITMO_ESCOLHIDO` e `K_ESCOLHIDO` e calcular o ARI contra o
  `perfis.csv`.
- Tabela `data/processed/tabela_sensibilidade.csv` com `variavel_retirada`,
  `bloco`, `n_colunas_no_bloco`, `ari`.
- Markdown escrito depois de rodar, em uma frase por variável, pronta para
  virar uma frase no artigo. Usar o mesmo critério da T3 para ler o ARI.

## Critérios de aceite

- [ ] 3 linhas na tabela, com o peso recalculado (conferir com um `assert` que
      o bloco afetado continua somando um terço da variância).
- [ ] Entrada no changelog do `ANDAMENTO.md`.

## Prompt para colar no Claude Code

> Leia o `CLAUDE.md` e `tarefas/T5_sensibilidade_opcional.md`. Implemente, rode
> o notebook 08 e me mostre a tabela.
