"""
Leitura e agregação das bases de criminalidade da SSP-SP.

O QUE ESTES ARQUIVOS SÃO (verificado nos arquivos reais):
  Os exports da SSP são MICRODADOS -- uma linha por boletim de ocorrência x
  natureza apurada --, e não uma tabela já agregada por município. Não existe
  coluna "quantidade": a contagem é o número de linhas do grupo. Conferido em
  SPDadosCriminais_2026: 638.300 BOs distintos em 645.725 linhas, com apenas
  2 duplicatas exatas de (BO, natureza).

  `SPDadosCriminais_<ano>.xlsx`  -> 1 aba de dicionário + N abas de dados
                                    (ex.: JAN-JUN_2026, JUL-DEZ_2026)
  `VeiculosSubtraidos_<ano>.xlsx`, `CelularesSubtraidos_<ano>.xlsx`
                                 -> METODOLOGIA + DICIONARIO DE DADOS + 1 aba
                                    de dados

QUAL MUNICÍPIO: usamos a coluna `COD IBGE`, que corresponde ao município de
CIRCUNSCRIÇÃO (local do fato) -- o correto para taxa de criminalidade. Foi
verificado: `NOME_MUNICIPIO_CIRCUNSCRICAO` mapeia 1:1 com `COD IBGE`, enquanto
`NOME_MUNICIPIO` (delegacia de registro) é ambíguo -- 267 nomes aparecem com
mais de um código. Registro != circunscrição em 0,5% das linhas.

POR QUE openpyxl EM STREAMING E NÃO pandas.read_excel: os arquivos têm 34 a
112 MB e até 555 mil linhas por aba. `read_excel` carrega a aba inteira em
memória; aqui percorremos linha a linha acumulando contadores, o que mantém o
uso de memória constante.

Saídas (camada intermediária, em data/processed/):
  ssp_painel.csv       codigo_ibge, ano, natureza, ocorrencias
  ssp_textura.csv      codigo_ibge, ano, contagens de local/período
  ssp_complementar.csv codigo_ibge, ano, veículos e celulares subtraídos
  ssp_cobertura.csv    ano, n_meses  (essencial: 2026 só tem 7 meses)
"""
from __future__ import annotations

import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook

from config import (
    SSP_DIR, SSP_CRIMINAIS_GLOB, SSP_VEICULOS_GLOB, SSP_CELULARES_GLOB,
    SSP_PAINEL_CSV, SSP_TEXTURA_CSV, SSP_COMPLEMENTAR_CSV, SSP_COBERTURA_CSV,
)


def normaliza(txt) -> str:
    """Maiúsculo, sem acento, espaços colapsados -- para comparar rótulos."""
    txt = str(txt).strip().upper()
    txt = unicodedata.normalize("NFKD", txt).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", txt)


def _abas_de_dados(wb, colunas_exigidas: list[str]) -> list[str]:
    """
    Descobre quais abas são de dados olhando o CONTEÚDO do cabeçalho, e não o
    nome da aba -- os nomes mudam de ano para ano (JAN-JUN_2026, JAN-DEZ_2025,
    CELULAR_2026...) e a primeira aba costuma ser o dicionário de campos.
    """
    exigidas = {normaliza(c) for c in colunas_exigidas}
    abas = []
    for nome in wb.sheetnames:
        ws = wb[nome]
        try:
            cabecalho = next(ws.iter_rows(max_row=1, values_only=True))
        except StopIteration:
            continue
        presentes = {normaliza(c) for c in cabecalho if c is not None}
        if exigidas <= presentes:
            abas.append(nome)
    return abas


def _indices(cabecalho: list, colunas: list[str]) -> dict[str, int]:
    """Mapeia nome de coluna -> posição, tolerando acento/caixa/espaços."""
    posicoes = {}
    for i, c in enumerate(cabecalho):
        if c is not None:
            posicoes.setdefault(normaliza(c), i)
    faltando = [c for c in colunas if normaliza(c) not in posicoes]
    if faltando:
        raise ValueError(
            f"Não encontrei as colunas {faltando} nesta aba.\n"
            f"Colunas presentes: {[c for c in cabecalho if c is not None]}"
        )
    return {c: posicoes[normaliza(c)] for c in colunas}


def _cod_ibge(valor) -> str | None:
    """Normaliza o código IBGE para string de 7 dígitos, ou None se inválido."""
    if valor is None:
        return None
    txt = str(valor).strip()
    if txt in ("", "NULL"):
        return None
    if txt.endswith(".0"):
        txt = txt[:-2]
    return txt if txt.isdigit() and len(txt) == 7 else None


# ---------------------------------------------------------------------------
# 1. Base principal: SPDadosCriminais
# ---------------------------------------------------------------------------

# DESC_PERIODO tem 57,6% de "NULL" no arquivo de 2026, então `prop_noturno`
# é calculada apenas sobre os registros de período conhecido -- e a base
# carrega a cobertura junto, para vocês julgarem se a variável é utilizável.
PERIODOS_NOTURNOS = {"A NOITE", "DE MADRUGADA"}
PERIODOS_DIURNOS = {"PELA MANHA", "A TARDE"}

COLS_CRIMINAIS = [
    "COD IBGE", "ANO_ESTATISTICA", "MES_ESTATISTICA",
    "NATUREZA_APURADA", "DESCR_TIPOLOCAL", "DESC_PERIODO",
]


def agregar_criminais(diretorio: Path = SSP_DIR) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Percorre todos os SPDadosCriminais_*.xlsx e devolve (painel, textura,
    cobertura).

    O ano usado é ANO_ESTATISTICA (mês/ano de entrada na estatística oficial),
    não ANO_BO -- alguns boletins de 2026 referem-se a fatos de 2024/2025, e a
    SSP contabiliza pela estatística.
    """
    arquivos = sorted(diretorio.glob(SSP_CRIMINAIS_GLOB))
    if not arquivos:
        raise FileNotFoundError(
            f"Nenhum arquivo '{SSP_CRIMINAIS_GLOB}' em {diretorio}.\n"
            "Baixe os exports anuais em https://www.ssp.sp.gov.br/estatistica/consultas"
        )

    contagem = Counter()                    # (cod, ano, natureza) -> n
    textura = defaultdict(Counter)          # (cod, ano) -> contadores
    meses = defaultdict(set)                # ano -> {meses observados}
    descartadas = 0

    for arq in arquivos:
        print(f"  lendo {arq.name} ...", flush=True)
        wb = load_workbook(arq, read_only=True, data_only=True)
        abas = _abas_de_dados(wb, ["COD IBGE", "NATUREZA_APURADA"])
        if not abas:
            print(f"    [aviso] nenhuma aba de dados reconhecida em {arq.name}; pulando.")
            wb.close()
            continue

        for aba in abas:
            ws = wb[aba]
            it = ws.iter_rows(values_only=True)
            idx = _indices(list(next(it)), COLS_CRIMINAIS)
            i_cod = idx["COD IBGE"]
            i_ano, i_mes = idx["ANO_ESTATISTICA"], idx["MES_ESTATISTICA"]
            i_nat, i_loc, i_per = (idx["NATUREZA_APURADA"], idx["DESCR_TIPOLOCAL"],
                                   idx["DESC_PERIODO"])
            n_aba = 0
            for row in it:
                cod = _cod_ibge(row[i_cod])
                if cod is None or row[i_ano] is None:
                    descartadas += 1
                    continue
                ano = int(row[i_ano])
                chave = (cod, ano)
                contagem[(cod, ano, normaliza(row[i_nat]))] += 1

                t = textura[chave]
                t["n_ocorrencias"] += 1
                if normaliza(row[i_loc]) == "VIA PUBLICA":
                    t["n_via_publica"] += 1
                periodo = normaliza(row[i_per])
                if periodo in PERIODOS_NOTURNOS:
                    t["n_periodo_conhecido"] += 1
                    t["n_noturno"] += 1
                elif periodo in PERIODOS_DIURNOS:
                    t["n_periodo_conhecido"] += 1

                if row[i_mes] is not None:
                    meses[ano].add(int(row[i_mes]))
                n_aba += 1
            print(f"    aba {aba!r}: {n_aba:,} linhas".replace(",", "."))
        wb.close()

    if descartadas:
        print(f"  [aviso] {descartadas} linha(s) descartada(s) por COD IBGE/ano ausente.")

    painel = pd.DataFrame(
        [(c, a, n, q) for (c, a, n), q in sorted(contagem.items())],
        columns=["codigo_ibge", "ano", "natureza", "ocorrencias"],
    )
    tex = pd.DataFrame(
        [
            {"codigo_ibge": c, "ano": a,
             "n_ocorrencias": v["n_ocorrencias"],
             "n_via_publica": v["n_via_publica"],
             "n_periodo_conhecido": v["n_periodo_conhecido"],
             "n_noturno": v["n_noturno"]}
            for (c, a), v in sorted(textura.items())
        ]
    )
    cob = pd.DataFrame(
        [{"ano": a, "n_meses": len(m), "meses": ",".join(str(x) for x in sorted(m))}
         for a, m in sorted(meses.items())]
    )
    return painel, tex, cob


# ---------------------------------------------------------------------------
# 2. Bases complementares: veículos e celulares
# ---------------------------------------------------------------------------
#
# ATENÇÃO conceitual: os BOs destes dois arquivos JÁ ESTÃO contabilizados em
# SPDadosCriminais como FURTO - OUTROS / ROUBO - OUTROS / FURTO DE VEÍCULO
# etc. Somar as contagens daqui como se fossem crimes adicionais seria dupla
# contagem. Por isso extraímos apenas o que é informação NOVA -- composição e
# desfecho -- que vira razão (proporção) na base final:
#   - taxa de recuperação de veículos  -> efetividade institucional
#   - participação de motocicletas     -> perfil da frota subtraída
#   - participação de celulares        -> crime patrimonial urbano de rua

MOTOS = {"MOTOCICLO", "MOTONETA", "CICLOMOTO"}

COLS_VEICULOS = ["COD IBGE", "ANO_REGISTRO_BO", "DESCR_OCORRENCIA_VEICULO",
                 "DESCR_TIPO_VEICULO"]
COLS_CELULARES = ["COD IBGE", "ANO_REGISTRO_BO", "RUBRICA"]


def agregar_complementares(diretorio: Path = SSP_DIR) -> pd.DataFrame:
    """Agrega VeiculosSubtraidos_* e CelularesSubtraidos_* por município/ano."""
    acc = defaultdict(Counter)   # (cod, ano) -> contadores

    # --- veículos ---
    for arq in sorted(diretorio.glob(SSP_VEICULOS_GLOB)):
        print(f"  lendo {arq.name} ...", flush=True)
        wb = load_workbook(arq, read_only=True, data_only=True)
        for aba in _abas_de_dados(wb, ["COD IBGE", "DESCR_OCORRENCIA_VEICULO"]):
            ws = wb[aba]
            it = ws.iter_rows(values_only=True)
            idx = _indices(list(next(it)), COLS_VEICULOS)
            vazias = 0
            for row in it:
                cod = _cod_ibge(row[idx["COD IBGE"]])
                ano = row[idx["ANO_REGISTRO_BO"]]
                desfecho = row[idx["DESCR_OCORRENCIA_VEICULO"]]
                # O arquivo de 2026 traz 3.696 linhas totalmente vazias no fim.
                if cod is None or ano is None or desfecho is None:
                    vazias += 1
                    continue
                chave = (cod, int(ano))
                d = normaliza(desfecho)
                if d == "FURTADO":
                    acc[chave]["veic_furtado"] += 1
                elif d == "ROUBADO":
                    acc[chave]["veic_roubado"] += 1
                elif d.startswith("LOCALIZADO"):
                    # "Localizado / Entregue" é RECUPERAÇÃO, não crime.
                    acc[chave]["veic_localizado"] += 1
                if d in ("FURTADO", "ROUBADO"):
                    acc[chave]["veic_subtraido"] += 1
                    if normaliza(row[idx["DESCR_TIPO_VEICULO"]]) in MOTOS:
                        acc[chave]["veic_moto"] += 1
            if vazias:
                print(f"    aba {aba!r}: {vazias} linha(s) vazia(s) descartada(s)")
        wb.close()

    # --- celulares ---
    for arq in sorted(diretorio.glob(SSP_CELULARES_GLOB)):
        print(f"  lendo {arq.name} ...", flush=True)
        wb = load_workbook(arq, read_only=True, data_only=True)
        for aba in _abas_de_dados(wb, ["COD IBGE", "RUBRICA"]):
            ws = wb[aba]
            it = ws.iter_rows(values_only=True)
            idx = _indices(list(next(it)), COLS_CELULARES)
            for row in it:
                cod = _cod_ibge(row[idx["COD IBGE"]])
                ano = row[idx["ANO_REGISTRO_BO"]]
                if cod is None or ano is None:
                    continue
                rubrica = normaliza(row[idx["RUBRICA"]])
                # 'Perda/Extravio' (28 mil linhas em 2026) não é crime.
                if rubrica.startswith("FURTO"):
                    acc[(cod, int(ano))]["cel_furto"] += 1
                elif rubrica.startswith("ROUBO"):
                    acc[(cod, int(ano))]["cel_roubo"] += 1
        wb.close()

    campos = ["veic_furtado", "veic_roubado", "veic_localizado", "veic_subtraido",
              "veic_moto", "cel_furto", "cel_roubo"]
    return pd.DataFrame(
        [dict({"codigo_ibge": c, "ano": a}, **{k: v[k] for k in campos})
         for (c, a), v in sorted(acc.items())]
    )


def main() -> None:
    print("Agregando SPDadosCriminais (microdados -> painel município x ano)...")
    painel, textura, cobertura = agregar_criminais()
    painel.to_csv(SSP_PAINEL_CSV, index=False, encoding="utf-8")
    textura.to_csv(SSP_TEXTURA_CSV, index=False, encoding="utf-8")
    cobertura.to_csv(SSP_COBERTURA_CSV, index=False, encoding="utf-8")
    print(f"-> {SSP_PAINEL_CSV.name}: {len(painel)} linhas "
          f"({painel['codigo_ibge'].nunique()} municípios, "
          f"{painel['natureza'].nunique()} naturezas)")
    print(f"-> {SSP_COBERTURA_CSV.name}:")
    for _, r in cobertura.iterrows():
        aviso = "  <-- ANO INCOMPLETO" if r["n_meses"] < 12 else ""
        print(f"     {r['ano']}: {r['n_meses']} meses{aviso}")

    print("\nAgregando veículos e celulares subtraídos...")
    comp = agregar_complementares()
    comp.to_csv(SSP_COMPLEMENTAR_CSV, index=False, encoding="utf-8")
    print(f"-> {SSP_COMPLEMENTAR_CSV.name}: {len(comp)} linhas")


if __name__ == "__main__":
    main()
