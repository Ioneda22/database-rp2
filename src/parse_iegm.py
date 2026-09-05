"""
Leitura e limpeza da base do IEGM (TCE-SP).

O QUE ESTE ARQUIVO É (verificado no arquivo real `data/raw/ieg-m/ieg-m.xls`):

  - Formato OLE2 legado (BIFF, assinatura D0CF11E0), NÃO xlsx. `openpyxl` não
    lê; é preciso `xlrd` (usamos a API do xlrd diretamente para não depender
    da versão do pandas).
  - Aba única, 644 municípios, exercício 2024 / apuração 2025.
  - Colunas:
        exercicio_ref | ano_apuracao | codigo_municipio | nome | iegm
        iplanejamento | ifiscal | ieduc | isaude | iamb | icidade | igov

DUAS COISAS QUE QUEBRAM QUEM ASSUME O CONTRÁRIO:

  1. TODAS as notas -- a geral e as 7 dimensões -- vêm como CONCEITO em letra
     (A, B+, B, C+, C), nunca como número. Aplicar `pd.to_numeric` nelas
     transforma a base inteira em NaN. Convertemos as 8 pela escala ordinal
     de config.ESCALA_ORDINAL_IEGM.
  2. Há 644 municípios, não 645: falta a CAPITAL (código 3550308). São Paulo
     é fiscalizada pelo TCM-SP, não pelo TCE-SP, e por isso nunca aparece no
     IEGM. Como o desenho da pesquisa usa o IEGM como variável de
     clusterização, a capital fica necessariamente fora da base de modelagem
     -- a base final marca isso em `flag_sem_iegm`.

CAVEAT PARA A MODELAGEM: os conceitos têm 4-5 níveis e são muito
concentrados. Em 2024, `iplanejamento` tem 533 dos 644 municípios (83%) no
conceito 'C', e nenhum município tirou 'A' no IEGM geral. Padronizadas, essas
colunas carregam pouca informação mas consomem orçamento de distância no
K-means -- veja a nota sobre peso por bloco no relatório da base.
"""
from __future__ import annotations

import pandas as pd
import xlrd

from config import IEGM_RAW_PATH, ESCALA_ORDINAL_IEGM, COLUNAS_IEGM


def carregar_iegm(caminho=IEGM_RAW_PATH) -> pd.DataFrame:
    if not caminho.exists():
        raise FileNotFoundError(
            f"Não encontrei {caminho}. Baixe a planilha de resultados do IEGM "
            "em https://www.tce.sp.gov.br/iegm e salve nesse caminho."
        )

    livro = xlrd.open_workbook(str(caminho))
    aba = livro.sheet_by_index(0)
    cabecalho = [str(c).strip().lower() for c in aba.row_values(0)]
    linhas = [aba.row_values(i) for i in range(1, aba.nrows)]
    df = pd.DataFrame(linhas, columns=cabecalho)

    faltando = [c for c in ["codigo_municipio", "nome"] + list(COLUNAS_IEGM)
                if c not in df.columns]
    if faltando:
        raise ValueError(
            f"Colunas ausentes na planilha do IEGM: {faltando}\n"
            f"Colunas encontradas: {cabecalho}\n"
            "Se o TCE-SP mudou o layout, ajuste COLUNAS_IEGM em config.py."
        )

    # xlrd devolve todo número como float: 3500105.0 -> "3500105"
    saida = pd.DataFrame({
        "codigo_ibge": df["codigo_municipio"].astype(float).astype(int).astype(str),
        "municipio_iegm": df["nome"].astype(str).str.strip(),
    })
    for exercicio in ("exercicio_ref", "ano_apuracao"):
        if exercicio in df.columns:
            saida[f"iegm_{exercicio}"] = df[exercicio].astype(float).astype(int)

    nao_mapeados = set()
    for origem, destino in COLUNAS_IEGM.items():
        conceito = df[origem].astype(str).str.strip().str.upper()
        saida[f"{destino}_conceito"] = conceito
        saida[f"{destino}_ord"] = conceito.map(ESCALA_ORDINAL_IEGM)
        nao_mapeados |= set(conceito.unique()) - set(ESCALA_ORDINAL_IEGM)

    if nao_mapeados:
        print(f"[aviso] conceitos do IEGM fora de ESCALA_ORDINAL_IEGM: "
              f"{sorted(nao_mapeados)}. Ajuste o dicionário em config.py.")

    return saida


if __name__ == "__main__":
    df = carregar_iegm()
    print(df.head())
    print(f"\n{len(df)} municípios carregados do IEGM.")
    for col in [c for c in df.columns if c.endswith("_conceito")]:
        print(f"  {col:24s} {df[col].value_counts().to_dict()}")
