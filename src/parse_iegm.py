"""
Lê as planilhas do IEGM (TCE-SP) e monta uma linha por município.

Sobre esses arquivos:
- São .xls antigo, então usamos xlrd (openpyxl não abre).
- As notas vêm como letra (A, B+, B, C+, C). Convertemos para 1 a 5.
- Só têm 644 municípios: a capital não entra, porque é fiscalizada pelo
  TCM-SP e não pelo TCE-SP.
- O nome do arquivo não diz o ano. O que vale é a coluna exercicio_ref.

Nas colunas *_ord usamos a média dos exercícios disponíveis (2022, 2023 e
2024). Um exercício sozinho tem poucos valores diferentes; com a média a
coluna ganha mais variação. As colunas *_conceito guardam a letra do
exercício mais recente, só para leitura.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import xlrd

from config import IEGM_DIR, IEGM_GLOB, ESCALA_ORDINAL_IEGM, COLUNAS_IEGM


def _ler_planilha(caminho: Path) -> pd.DataFrame:
    """Lê uma planilha (um exercício) e devolve um município por linha."""
    livro = xlrd.open_workbook(str(caminho))
    aba = livro.sheet_by_index(0)
    cabecalho = [str(c).strip().lower() for c in aba.row_values(0)]
    linhas = [aba.row_values(i) for i in range(1, aba.nrows)]
    df = pd.DataFrame(linhas, columns=cabecalho)

    faltando = [c for c in ["codigo_municipio", "nome", "exercicio_ref"]
                + list(COLUNAS_IEGM) if c not in df.columns]
    if faltando:
        raise ValueError(
            f"Colunas ausentes em {caminho.name}: {faltando}\n"
            f"Colunas encontradas: {cabecalho}\n"
            "Se o TCE-SP mudou o layout, ajuste COLUNAS_IEGM em config.py."
        )

    # O xlrd lê os números como float: 3500105.0 vira "3500105".
    saida = pd.DataFrame({
        "codigo_ibge": df["codigo_municipio"].astype(float).astype(int)
                                             .astype(str),
        "municipio_iegm": df["nome"].astype(str).str.strip(),
        "exercicio_ref": df["exercicio_ref"].astype(float).astype(int),
    })
    if "ano_apuracao" in df.columns:
        saida["ano_apuracao"] = df["ano_apuracao"].astype(float).astype(int)

    nao_mapeados = set()
    for origem, destino in COLUNAS_IEGM.items():
        conceito = df[origem].astype(str).str.strip().str.upper()
        saida[f"{destino}_conceito"] = conceito
        saida[f"{destino}_ord"] = conceito.map(ESCALA_ORDINAL_IEGM)
        nao_mapeados |= set(conceito.unique()) - set(ESCALA_ORDINAL_IEGM)

    if nao_mapeados:
        print(f"[aviso] {caminho.name}: conceitos fora de "
              f"ESCALA_ORDINAL_IEGM: {sorted(nao_mapeados)}. "
              "Ajuste o dicionário em config.py.")
    return saida


def carregar_iegm(diretorio: Path = IEGM_DIR) -> pd.DataFrame:
    """
    Junta todos os exercícios do IEGM em uma linha por município.

    *_ord      -> média dos exercícios encontrados
    *_conceito -> letra do exercício mais recente
    """
    arquivos = sorted(Path(diretorio).glob(IEGM_GLOB))
    if not arquivos:
        raise FileNotFoundError(
            f"Nenhum arquivo '{IEGM_GLOB}' em {diretorio}. Baixe as planilhas "
            "de resultados do IEGM em https://www.tce.sp.gov.br/iegm."
        )

    exercicios = [_ler_planilha(a) for a in arquivos]
    longo = pd.concat(exercicios, ignore_index=True)

    dup = longo.duplicated(subset=["codigo_ibge", "exercicio_ref"]).sum()
    if dup:
        raise ValueError(
            f"{dup} par(es) (município, exercício) repetido(s) em "
            f"{diretorio}. Há planilhas duplicadas do mesmo exercício -- "
            "remova as cópias e rode de novo."
        )

    anos = sorted(longo["exercicio_ref"].unique())
    print(f"IEGM: {len(arquivos)} planilha(s), exercício(s) {anos}, "
          f"{longo['codigo_ibge'].nunique()} municípios.")

    cols_ord = [f"{d}_ord" for d in COLUNAS_IEGM.values()]
    cols_conc = [f"{d}_conceito" for d in COLUNAS_IEGM.values()]

    medias = (longo.groupby("codigo_ibge", as_index=False)[cols_ord]
              .mean().round(4))

    recente = longo["exercicio_ref"] == max(anos)
    rotulos = longo.loc[recente, ["codigo_ibge", "municipio_iegm"] + cols_conc]

    saida = rotulos.merge(medias, on="codigo_ibge", how="outer")

    # Guarda o intervalo de anos como texto, ex.: "2022-2024".
    def intervalo(serie: pd.Series) -> str:
        v = sorted(serie.dropna().astype(int).unique())
        return str(v[0]) if len(v) == 1 else f"{v[0]}-{v[-1]}"

    saida["iegm_exercicio_ref"] = intervalo(longo["exercicio_ref"])
    if "ano_apuracao" in longo.columns:
        saida["iegm_ano_apuracao"] = intervalo(longo["ano_apuracao"])

    return saida.reset_index(drop=True)


if __name__ == "__main__":
    df = carregar_iegm()
    print(df.head())
    print(f"\n{len(df)} municípios consolidados do IEGM.")
    print(f"Exercícios: {df['iegm_exercicio_ref'].iloc[0]} | "
          f"apuração: {df['iegm_ano_apuracao'].iloc[0]}")
    for col in [c for c in df.columns if c.endswith("_ord")]:
        s = df[col]
        print(f"  {col:20s} média={s.mean():.2f}  níveis distintos="
              f"{s.nunique()}")
