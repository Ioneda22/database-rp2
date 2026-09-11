"""
Lê os arquivos da SSP-SP e agrega as ocorrências por município, ano e mês.

Sobre os arquivos:
- Cada linha é uma pessoa, natureza ou objeto de um boletim, não um boletim
  inteiro. Não existe coluna de quantidade: a contagem é o número de linhas.
- SPDadosCriminais_<ano>.xlsx tem 1 aba de dicionário e 2 abas de dados
  (JAN-JUN e JUL-DEZ). Veículos e celulares têm 1 aba de dados.
- Os nomes das colunas mudam de um ano para o outro. Por exemplo, o código
  do município é CD_IBGE em 2023-2025 e COD IBGE em 2026. Por isso cada
  campo tem uma lista de nomes possíveis (APELIDOS_*). Se a SSP mudar um
  nome, basta acrescentar na lista.
- Usamos o município de circunscrição (onde o fato aconteceu), que é o
  CD_IBGE, e não o município onde o BO foi registrado.

Lemos os .xlsx linha a linha com openpyxl porque os arquivos têm até
200 MB. Carregar tudo com pandas.read_excel gasta memória demais.

Saídas em data/processed/:
  ssp_painel.csv       codigo_ibge, ano, mes, natureza, ocorrencias
  ssp_textura.csv      codigo_ibge, ano, contagens de local e período
  ssp_complementar.csv codigo_ibge, ano, veículos e celulares
  ssp_cobertura.csv    ano, quantos meses tem

O painel é mensal para permitir a série mensal do notebook 01. A base final
soma os meses de cada ano.
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
    """Deixa o texto em maiúsculas, sem acento e sem espaços repetidos."""
    txt = str(txt).strip().upper()
    txt = unicodedata.normalize("NFKD", txt).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", txt)


# ---------------------------------------------------------------------------
# Nomes possíveis de cada coluna
# ---------------------------------------------------------------------------
#
# Para cada campo, a lista de nomes que já apareceram nos arquivos, em ordem
# de preferência. Quando a SSP renomear uma coluna, é só acrescentar aqui.

APELIDOS_CRIMINAIS = {
    "cod_ibge":  ["CD_IBGE", "COD IBGE"],
    "ano":       ["ANO_ESTATISTICA"],
    "mes":       ["MES_ESTATISTICA"],
    "natureza":  ["NATUREZA_APURADA"],
    # DESCR_TIPOLOCAL só existe em 2025. Usamos SUBTIPOLOCAL em todos os anos
    # para a definição de "via pública" ser a mesma na janela inteira.
    "local":     ["DESCR_SUBTIPOLOCAL"],
    "periodo":   ["DESC_PERIODO", "DESCR_PERIODO"],
    # Estes só servem para as conferências; não entram na agregação.
    "delegacia": ["NOME_DELEGACIA"],
    "num_bo":    ["NUM_BO"],
    "ano_bo":    ["ANO_BO"],
    "mun_reg":   ["NOME_MUNICIPIO", "CIDADE"],
    "mun_circ":  ["NOME_MUNICIPIO_CIRCUNSCRIÇÃO", "NOME_MUNICIPIO_CIRCUNCRIÇÃO"],
}
# CIDADE e DESCR_PERIODO são os nomes usados no arquivo de 2022. Conferimos
# pela aba de dicionário desse arquivo, que lista os campos na mesma ordem
# das colunas.

APELIDOS_VEICULOS = {
    "cod_ibge": ["CD_IBGE", "COD IBGE"],
    "ano":      ["ANO_REGISTRO_BO", "ANO"],
    "desfecho": ["DESCR_OCORRENCIA_VEICULO"],
    "tipo":     ["DESCR_TIPO_VEICULO"],
}

APELIDOS_CELULARES = {
    "cod_ibge": ["CD_IBGE", "COD IBGE"],
    "ano":      ["ANO_REGISTRO_BO", "ANO"],
    "rubrica":  ["RUBRICA"],
}


def _indices(cabecalho: list, apelidos: dict[str, list[str]],
             obrigatorias: list[str]) -> dict[str, int | None]:
    """
    Descobre em qual posição da linha está cada campo, aceitando qualquer
    um dos nomes da lista. Campos opcionais que não existirem viram None.
    """
    posicoes = {}
    for i, c in enumerate(cabecalho):
        if c is not None:
            posicoes.setdefault(normaliza(c), i)

    idx: dict[str, int | None] = {}
    faltando = []
    for campo, nomes in apelidos.items():
        achado = next((posicoes[normaliza(n)] for n in nomes
                       if normaliza(n) in posicoes), None)
        idx[campo] = achado
        if achado is None and campo in obrigatorias:
            faltando.append(f"{campo} (esperava uma de {nomes})")

    if faltando:
        raise ValueError(
            f"Não encontrei as colunas {faltando} nesta aba.\n"
            f"Colunas presentes: {[c for c in cabecalho if c is not None]}"
        )
    return idx


def _abas_de_dados(wb, apelidos: dict[str, list[str]],
                   marcadores: list[str]) -> list[str]:
    """
    Descobre quais abas têm dados olhando o cabeçalho, e não o nome da aba
    (o nome muda de ano para ano). Uma aba serve se tiver todos os campos
    de `marcadores`.
    """
    abas = []
    for nome in wb.sheetnames:
        ws = wb[nome]
        try:
            cabecalho = next(ws.iter_rows(max_row=1, values_only=True))
        except StopIteration:
            continue
        presentes = {normaliza(c) for c in cabecalho if c is not None}
        if all(any(normaliza(n) in presentes for n in apelidos[campo])
               for campo in marcadores):
            abas.append(nome)
    return abas


def _mil(n: int) -> str:
    """Formata 1241911 como '1.241.911'."""
    return f"{n:,}".replace(",", ".")


def _cod_ibge(valor) -> str | None:
    """Devolve o código IBGE como texto de 7 dígitos, ou None se inválido."""
    if valor is None:
        return None
    txt = str(valor).strip()
    if txt in ("", "NULL"):
        return None
    if txt.endswith(".0"):
        txt = txt[:-2]
    return txt if txt.isdigit() and len(txt) == 7 else None


# ---------------------------------------------------------------------------
# 1. Arquivo principal: SPDadosCriminais
# ---------------------------------------------------------------------------

# O período fica vazio na maior parte das linhas. Por isso prop_noturno é
# calculada só sobre as linhas com período preenchido, e a base guarda a
# cobertura para avisar. "Em hora incerta" não entra em nenhum dos dois.
PERIODOS_NOTURNOS = {"A NOITE", "DE MADRUGADA"}
PERIODOS_DIURNOS = {"PELA MANHA", "A TARDE"}


def agregar_criminais(
    diretorio: Path = SSP_DIR,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Lê todos os SPDadosCriminais_*.xlsx e devolve (painel, textura,
    cobertura).

    O ano é o ANO_ESTATISTICA (quando a ocorrência entrou na estatística),
    e não o ANO_BO, porque é assim que a SSP conta.
    """
    arquivos = sorted(diretorio.glob(SSP_CRIMINAIS_GLOB))
    if not arquivos:
        raise FileNotFoundError(
            f"Nenhum arquivo '{SSP_CRIMINAIS_GLOB}' em {diretorio}.\n"
            "Baixe os exports anuais em "
            "https://www.ssp.sp.gov.br/estatistica/consultas"
        )

    contagem = Counter()                    # (cod, ano, mes, natureza) -> n
    textura = defaultdict(Counter)          # (cod, ano) -> contadores
    meses = defaultdict(set)                # ano -> meses que apareceram
    circunscricao = defaultdict(set)        # cod -> nomes de circunscrição
    por_nome = defaultdict(set)             # nome de registro -> códigos
    # Contados por ano, porque o painel tem anos fora da janela (2022).
    fora_circunscricao = Counter()          # ano -> linhas registro != fato
    linhas_ano = Counter()                  # ano -> linhas válidas
    descartadas = 0
    total_linhas = 0

    for arq in arquivos:
        print(f"  lendo {arq.name} ...", flush=True)
        wb = load_workbook(arq, read_only=True, data_only=True)
        abas = _abas_de_dados(wb, APELIDOS_CRIMINAIS, ["cod_ibge", "natureza"])
        if not abas:
            print(f"    [aviso] nenhuma aba de dados reconhecida em "
                  f"{arq.name}; pulando.")
            wb.close()
            continue

        chaves_bo = set()   # hashes de (delegacia, ano_bo, num_bo, natureza)
        linhas_arq = 0

        for aba in abas:
            ws = wb[aba]
            it = ws.iter_rows(values_only=True)
            idx = _indices(list(next(it)), APELIDOS_CRIMINAIS,
                           obrigatorias=["cod_ibge", "ano", "mes", "natureza"])
            i_cod, i_ano, i_mes = idx["cod_ibge"], idx["ano"], idx["mes"]
            i_nat, i_loc, i_per = idx["natureza"], idx["local"], idx["periodo"]
            i_del, i_nbo, i_abo = idx["delegacia"], idx["num_bo"], idx["ano_bo"]
            i_mreg, i_mcirc = idx["mun_reg"], idx["mun_circ"]

            n_aba = 0
            for row in it:
                cod = _cod_ibge(row[i_cod])
                if cod is None or row[i_ano] is None:
                    descartadas += 1
                    continue
                ano = int(row[i_ano])
                chave = (cod, ano)
                natureza = normaliza(row[i_nat])
                # Se o mês estiver vazio, fica 0. A linha continua contando
                # no total do ano; só a série mensal filtra mes > 0.
                mes = int(row[i_mes]) if row[i_mes] is not None else 0
                contagem[(cod, ano, mes, natureza)] += 1

                t = textura[chave]
                t["n_ocorrencias"] += 1
                if i_loc is not None and normaliza(row[i_loc]) == "VIA PUBLICA":
                    t["n_via_publica"] += 1
                if i_per is not None:
                    periodo = normaliza(row[i_per])
                    if periodo in PERIODOS_NOTURNOS:
                        t["n_periodo_conhecido"] += 1
                        t["n_noturno"] += 1
                    elif periodo in PERIODOS_DIURNOS:
                        t["n_periodo_conhecido"] += 1

                if mes:
                    meses[ano].add(mes)

                # --- conferências ---
                linhas_ano[ano] += 1
                if i_mcirc is not None:
                    nome_circ = str(row[i_mcirc]).strip()
                    circunscricao[cod].add(nome_circ)
                    # strip() dos dois lados: em 2022 o campo CIDADE vem com
                    # espaços no fim e a comparação daria diferente à toa.
                    if i_mreg is not None:
                        if str(row[i_mreg]).strip() != nome_circ:
                            fora_circunscricao[ano] += 1
                if i_mreg is not None:
                    por_nome[str(row[i_mreg]).strip()].add(cod)
                if None not in (i_del, i_nbo, i_abo):
                    chaves_bo.add(hash((row[i_del], row[i_abo],
                                        row[i_nbo], natureza)))
                n_aba += 1

            linhas_arq += n_aba
            print(f"    aba {aba!r}: {_mil(n_aba)} linhas")
        wb.close()

        # Como cada linha é uma pessoa/natureza/objeto, contar linhas só dá
        # certo se quase não houver repetição de (BO, natureza). Aqui a gente
        # mede isso em vez de supor.
        if chaves_bo:
            dup = linhas_arq - len(chaves_bo)
            print(f"    {_mil(linhas_arq)} linhas / {_mil(len(chaves_bo))} "
                  "chaves (delegacia, ano_bo, num_bo, natureza) distintas "
                  f"-> {_mil(dup)} repetição(ões) = {dup / linhas_arq:.2%}")
        total_linhas += linhas_arq

    print(f"\n  Total lido: {_mil(total_linhas)} linhas.")
    if descartadas:
        print(f"  [aviso] {descartadas} linha(s) descartada(s) por "
              "CD_IBGE/ano ausente.")

    # Conferência da chave de junção:
    # - cada código deve ter um nome só. Se tiver dois, pode ser só grafia
    #   diferente (ex.: "S.ANTONIO" e "SANTO ANTONIO"); o script lista para
    #   a gente conferir.
    # - o nome do município de registro aponta para vários códigos, porque o
    #   BO pode ser feito numa cidade e o fato ter ocorrido em outra. É por
    #   isso que não juntamos por nome.
    varios_nomes = {c: n for c, n in circunscricao.items() if len(n) > 1}
    print(f"  CD_IBGE -> município de circunscrição: {len(circunscricao)} "
          f"códigos, {len(varios_nomes)} com mais de uma grafia")
    for c, nomes in sorted(varios_nomes.items())[:10]:
        print(f"    {c}: {sorted(nomes)}  <- conferir se é o mesmo município")

    varios_cods = {n: c for n, c in por_nome.items() if len(c) > 1}
    if por_nome:
        print(f"  NOME_MUNICIPIO (delegacia de registro) -> código: "
              f"{len(por_nome)} nomes, {len(varios_cods)} apontam para mais "
              "de um código -- casar por esse nome atribuiria a ocorrência à "
              "cidade do BO, não à do fato.")
    if fora_circunscricao:
        print("  Registro != circunscrição, por ano (a SSP avisa que ~60% "
              "dos BOs são feitos fora da circunscrição):")
        for ano in sorted(linhas_ano):
            n_fora, n_tot = fora_circunscricao[ano], linhas_ano[ano]
            print(f"    {ano}: {_mil(n_fora):>9s} de {_mil(n_tot):>11s} "
                  f"({n_fora / n_tot:.2%})")

    painel = pd.DataFrame(
        [(c, a, m, n, q) for (c, a, m, n), q in sorted(contagem.items())],
        columns=["codigo_ibge", "ano", "mes", "natureza", "ocorrencias"],
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
        [{"ano": a, "n_meses": len(m),
          "meses": ",".join(str(x) for x in sorted(m))}
         for a, m in sorted(meses.items())]
    )
    return painel, tex, cob


# ---------------------------------------------------------------------------
# 2. Arquivos de veículos e celulares
# ---------------------------------------------------------------------------
#
# Os BOs desses arquivos já estão contados no SPDadosCriminais (como furto,
# roubo etc.). Somar de novo seria contar duas vezes. Daqui tiramos só o que
# é informação nova, em forma de proporção:
#   - veículos localizados / subtraídos
#   - participação de motos entre os veículos subtraídos
#   - participação de celulares nas ocorrências

MOTOS = {"MOTOCICLO", "MOTONETA", "CICLOMOTO"}


def agregar_complementares(diretorio: Path = SSP_DIR) -> pd.DataFrame:
    """Agrega VeiculosSubtraidos_* e CelularesSubtraidos_* por município e ano."""
    acc = defaultdict(Counter)   # (cod, ano) -> contadores

    # --- veículos ---
    for arq in sorted(diretorio.glob(SSP_VEICULOS_GLOB)):
        print(f"  lendo {arq.name} ...", flush=True)
        wb = load_workbook(arq, read_only=True, data_only=True)
        for aba in _abas_de_dados(wb, APELIDOS_VEICULOS,
                                  ["cod_ibge", "desfecho"]):
            ws = wb[aba]
            it = ws.iter_rows(values_only=True)
            idx = _indices(list(next(it)), APELIDOS_VEICULOS,
                           obrigatorias=["cod_ibge", "ano", "desfecho", "tipo"])
            vazias = 0
            for row in it:
                cod = _cod_ibge(row[idx["cod_ibge"]])
                ano = row[idx["ano"]]
                desfecho = row[idx["desfecho"]]
                # Alguns arquivos têm linhas vazias no final.
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
                    # "Localizado / Entregue" é veículo recuperado, não crime.
                    acc[chave]["veic_localizado"] += 1
                if d in ("FURTADO", "ROUBADO"):
                    acc[chave]["veic_subtraido"] += 1
                    if normaliza(row[idx["tipo"]]) in MOTOS:
                        acc[chave]["veic_moto"] += 1
            if vazias:
                print(f"    aba {aba!r}: {vazias} linha(s) vazia(s) "
                      "descartada(s)")
        wb.close()

    # --- celulares ---
    for arq in sorted(diretorio.glob(SSP_CELULARES_GLOB)):
        print(f"  lendo {arq.name} ...", flush=True)
        wb = load_workbook(arq, read_only=True, data_only=True)
        for aba in _abas_de_dados(wb, APELIDOS_CELULARES,
                                  ["cod_ibge", "rubrica"]):
            ws = wb[aba]
            it = ws.iter_rows(values_only=True)
            idx = _indices(list(next(it)), APELIDOS_CELULARES,
                           obrigatorias=["cod_ibge", "ano", "rubrica"])
            for row in it:
                cod = _cod_ibge(row[idx["cod_ibge"]])
                ano = row[idx["ano"]]
                if cod is None or ano is None:
                    continue
                rubrica = normaliza(row[idx["rubrica"]])
                # "Perda/Extravio" não é crime.
                if rubrica.startswith("FURTO"):
                    acc[(cod, int(ano))]["cel_furto"] += 1
                elif rubrica.startswith("ROUBO"):
                    acc[(cod, int(ano))]["cel_roubo"] += 1
        wb.close()

    campos = ["veic_furtado", "veic_roubado", "veic_localizado",
              "veic_subtraido", "veic_moto", "cel_furto", "cel_roubo"]
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
