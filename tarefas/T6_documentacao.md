# T6 — Atualizar README e ANDAMENTO

**Responsável:** Bruno · **Prazo:** domingo 18/10 · **Tempo estimado:** 30 min

## O que fazer

- `README.md`:
  - seção 3.2: lista dos notebooks com 04 a 07 (e 08, se existir), no mesmo
    formato da lista atual;
  - seção 4.1: as saídas novas em `data/processed/` (`metricas_clusterizacao.csv`,
    `dbscan_grade.csv`, `tabela_comparacao_algoritmos.csv`, `perfis.csv`,
    `tabela_perfis.csv`, `tabela_exemplos_perfis.csv`, `tabela_kruskal.csv`
    e, se existir, `tabela_sensibilidade.csv`), na mesma tabela de 3 colunas;
  - seção 4.2: as figuras novas;
  - seção 5: `src/preprocessamento.py`, `src/clusterizacao.py`, `src/malha.py`
    e a malha em `data/raw/ibge/`.
- `ANDAMENTO.md`:
  - atualizar data, entrega e a tabela "Onde estamos" (Fases 4 e 5
    concluídas);
  - trocar a seção 1 ("O escopo desta entrega mudou") por um resumo do escopo
    de 21/10;
  - seção "Números verificados": acrescentar os números finais da
    clusterização, **copiados das saídas dos notebooks**, nunca digitados de
    memória.
- Conferir se `requirements.txt` cobre tudo o que os notebooks novos importam.

## Prompt para colar no Claude Code

> Leia o `CLAUDE.md` e `tarefas/T6_documentacao.md`. Atualize README e
> ANDAMENTO conforme a tarefa. Todo número que entrar no ANDAMENTO tem que vir
> de um CSV ou da saída de um notebook; me diga de onde veio cada um.
