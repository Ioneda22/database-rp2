"""
Leitura e agregação das bases de criminalidade da SSP-SP.

O QUE ESTES ARQUIVOS SÃO (verificado nos arquivos reais de 2023, 2024 e 2025):
  Os exports da SSP são MICRODADOS -- uma linha por boletim de ocorrência x
  pessoa x natureza x objeto --, e não uma tabela já agregada por município.
  Não existe coluna "quantidade": a contagem é o número de linhas do grupo.

  `SPDadosCriminais_<ano>.xlsx`  -> 1 aba de dicionário + 2 abas de dados
                                    (JAN-JUN_<ano>, JUL-DEZ_<ano>)
  `VeiculosSubtraidos_<ano>.xlsx`, `CelularesSubtraidos_<ano>.xlsx`
                                 -> METODOLOGIA + DICIONARIO DE DADOS + 1 aba
                                    de dados

OS NOMES DAS COLUNAS MUDAM DE ANO PARA ANO. Esta é a principal armadilha da
base, e por isso toda coluna é resolvida por uma LISTA DE APELIDOS
(`_indices`), nunca por um nome fixo:

  - `CD_IBGE` em 2023-2025; `COD IBGE` no export de 2026. A aba de dicionário
    documenta "COD IBGE" nos três anos, mas o cabeçalho real da aba de dados
    é `CD_IBGE`. Como as abas de dados são descobertas pelo conteúdo do
    cabeçalho, um nome errado aqui não dá erro: dá painel VAZIO.
  - `DESCR_TIPOLOCAL` só existe em 2025. Em 2023 e 2024 há apenas
    `DESCR_SUBTIPOLOCAL`. Usamos `DESCR_SUBTIPOLOCAL` nos TRÊS anos: uma
    definição consistente ao longo da janela vale mais do que casar com o
    TIPOLOCAL de 2025 -- misturar as duas criaria um degrau artificial entre
    2024 e 2025 em `prop_via_publica`, que é justamente a variável de
    validação externa do desenho. (As duas não são equivalentes: numa amostra
    de 4.000 linhas de 2025, TIPOLOCAL="Via Pública" em 2.333 e
    SUBTIPOLOCAL="Via Pública" em 2.118.)
  - Veículos e celulares: `ANO`/`MES` em 2023-2024, `ANO_REGISTRO_BO`/
    `MES_REGISTRO_BO` em 2025.

QUAL MUNICÍPIO: usamos `CD_IBGE`, que corresponde ao município de
CIRCUNSCRIÇÃO (local do fato) -- o correto para taxa de criminalidade. A aba
METODOLOGIA da própria SSP avisa que "cerca de 60% das ocorrências são
registradas fora de sua circunscrição", então registro != local do fato não é
detalhe. `agregar_criminais` VERIFICA essa correspondência em tempo de
execução e imprime o resultado.

POR QUE openpyxl EM STREAMING E NÃO pandas.read_excel: os arquivos têm 66 a
208 MB e até 623 mil linhas por aba. `read_excel` carrega a aba inteira em
memória; aqui percorremos linha a linha acumulando contadores, o que mantém o
uso de memória constante.

Saídas (camada intermediária, em data/processed/):
  ssp_painel.csv       codigo_ibge, ano, mes, natureza, ocorrencias
  ssp_textura.csv      codigo_ibge, ano, contagens de local/período
  ssp_complementar.csv codigo_ibge, ano, veículos e celulares subtraídos
  ssp_cobertura.csv    ano, n_meses

O painel é MENSAL de propósito, mesmo que a base final seja anual: mês é um
superconjunto barato (o `merge_bases.py` soma sobre ele sem saber que existe)
e é o que viabiliza a validação da janela temporal -- a série mensal estadual
que detecta o degrau da migração R.D.O. -> S.P.J. Sem isso, cada pergunta
sobre sazonalidade ou quebra de série custaria reprocessar 5 milhões de
linhas de novo.
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


# ---------------------------------------------------------------------------
# Resolução de colunas por apelido
# ---------------------------------------------------------------------------
#
# Cada campo lógico mapeia para a LISTA de grafias já vistas nos arquivos, em
# ordem de preferência. Acrescente aqui quando a SSP renomear algo -- é o
# único lugar que precisa mudar.

APELIDOS_CRIMINAIS = {
    "cod_ibge":  ["CD_IBGE", "COD IBGE"],
    "ano":       ["ANO_ESTATISTICA"],
    "mes":       ["MES_ESTATISTICA"],
    "natureza":  ["NATUREZA_APURADA"],
    # Ver a nota do cabeçalho: SUBTIPOLOCAL em todos os anos, de propósito.
    "local":     ["DESCR_SUBTIPOLOCAL"],
    "periodo":   ["DESC_PERIODO", "DESCR_PERIODO"],
    # Só para as verificações de integridade, não entram na agregação:
    "delegacia": ["NOME_DELEGACIA"],
    "num_bo":    ["NUM_BO"],
    "ano_bo":    ["ANO_BO"],
    "mun_reg":   ["NOME_MUNICIPIO", "CIDADE"],
    "mun_circ":  ["NOME_MUNICIPIO_CIRCUNSCRIÇÃO", "NOME_MUNICIPIO_CIRCUNCRIÇÃO"],
}
# `CIDADE` e `DESCR_PERIODO` são as grafias de 2022. Confirmadas contra a aba
# CAMPOS_DA_TABELA_SPDADOS daquele arquivo, que lista 29 campos na mesma ordem
# das 29 colunas da aba de dados: a posição 4 é documentada como
# "NOME_MUNICIPIO | Município de registro" e traz `CIDADE`; a posição 10 é
# "DESC_PERIODO | Período da ocorrência" e traz `DESCR_PERIODO`. Como em
# 2023-2025 não existe coluna `CIDADE`, a ordem dos apelidos resolve sozinha.

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
    Mapeia campo lógico -> posição na linha, tolerando acento/caixa/espaços e
    aceitando qualquer uma das grafias listadas em `apelidos`.

    Campos fora de `obrigatorias` que não forem encontrados viram None -- é
    assim que `DESCR_TIPOLOCAL` (ausente em 2023-2024) deixa de ser um crash e
    vira uma coluna opcional.
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
    Descobre quais abas são de dados olhando o CONTEÚDO do cabeçalho, e não o
    nome da aba -- os nomes mudam de ano para ano (JAN-JUN_2023, CELULAR_2025,
    VEICULOS_2024...) e as primeiras abas são metodologia/dicionário.

    Uma aba qualifica quando, para CADA campo em `marcadores`, pelo menos uma
    das grafias aceitas está presente.
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
    """1241911 -> '1.241.911'. Só o número: aplicar .replace(',', '.') na
    f-string inteira também trocaria as vírgulas do texto em volta."""
    return f"{n:,}".replace(",", ".")


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

# DESC_PERIODO tem taxa alta de "NULL" (~60% em 2023, ~83% em 2025), então
# `prop_noturno` é calculada apenas sobre os registros de período conhecido --
# e a base carrega `cobertura_periodo` junto, para julgar se é utilizável.
# "Em hora incerta" não é nem diurno nem noturno: fica fora dos dois.
PERIODOS_NOTURNOS = {"A NOITE", "DE MADRUGADA"}
PERIODOS_DIURNOS = {"PELA MANHA", "A TARDE"}


def agregar_criminais(
    diretorio: Path = SSP_DIR,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Percorre todos os SPDadosCriminais_*.xlsx e devolve (painel, textura,
    cobertura).

    O ano usado é ANO_ESTATISTICA (mês/ano de entrada na estatística oficial),
    não ANO_BO -- há boletins registrados num ano sobre fatos de anos
    anteriores, e a SSP contabiliza pela estatística.
    """
    arquivos = sorted(diretorio.glob(SSP_CRIMINAIS_GLOB))
    if not arquivos:
        raise FileNotFoundError(
            f"Nenhum arquivo '{SSP_CRIMINAIS_GLOB}' em {diretorio}.\n"
            "Baixe os exports anuais em "
            "https://www.ssp.sp.gov.br/estatistica/consultas"
        )

    contagem = Counter()                    # (cod, ano, natureza) -> n
    textura = defaultdict(Counter)          # (cod, ano) -> contadores
    meses = defaultdict(set)                # ano -> {meses observados}
    circunscricao = defaultdict(set)        # cod -> {nomes de circunscrição}
    por_nome = defaultdict(set)             # nome de REGISTRO -> {códigos}
    # Por ano, e não no agregado: o painel cobre anos fora da janela de
    # modelagem, e uma taxa global misturaria os dois. Os números que vão
    # para a Metodologia são os dos anos da janela.
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
                # mes = 0 quando MES_ESTATISTICA vem vazio. A ocorrência NÃO
                # é descartada: ela ainda conta no total anual, que é o que
                # alimenta as taxas. Quem faz série mensal é que filtra
                # `mes > 0` (ver notebook de validação temporal).
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

                # --- verificações de integridade ---
                linhas_ano[ano] += 1
                if i_mcirc is not None:
                    nome_circ = str(row[i_mcirc]).strip()
                    circunscricao[cod].add(nome_circ)
                    # .strip() nos DOIS lados: o campo `CIDADE` de 2022 vem
                    # preenchido com espaços à direita ('S.PAULO           '),
                    # e a comparação crua contaria isso como uma ocorrência
                    # registrada fora da circunscrição.
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

        # Cada linha é uma pessoa/natureza/objeto do boletim (ver METODOLOGIA
        # da SSP), então contar linhas só é contar ocorrências se as
        # repetições de (BO, natureza) forem desprezíveis. Medimos, não
        # supomos.
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

    # As duas direções da junção, que sustentam a decisão de casar por
    # `codigo_ibge` e nunca por nome:
    #
    #   código -> nome  deve ser 1:1. Um código com dois nomes pode ser só
    #   variação de grafia ("S.ANTONIO DA ALEGRIA" / "SANTO ANTONIO DA
    #   ALEGRIA"), que é inofensiva, ou dois municípios de fato, que
    #   invalidaria as taxas. O script lista os casos para julgamento humano
    #   em vez de decidir sozinho.
    #
    #   NOME_MUNICIPIO (registro) -> código  NÃO é 1:1, e é exatamente por
    #   isso que não se casa por nome. Cuidado com a leitura: a causa
    #   principal não é grafia ambígua, é que o município de REGISTRO não
    #   determina o município do FATO -- a mesma delegacia registra
    #   ocorrências de várias circunscrições. Casar por esse nome atribuiria
    #   o crime à cidade onde o BO foi feito. Este número vai para a
    #   Metodologia do artigo.
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


def agregar_complementares(diretorio: Path = SSP_DIR) -> pd.DataFrame:
    """Agrega VeiculosSubtraidos_* e CelularesSubtraidos_* por município/ano."""
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
                # Alguns exports trazem linhas totalmente vazias no fim.
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
                # 'Perda/Extravio' não é crime.
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
