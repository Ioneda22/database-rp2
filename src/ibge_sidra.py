"""
Aquisição de dados do SIDRA/IBGE para os municípios de São Paulo.

Esta é a ÚNICA das 3 fontes com uma API real e estável (apisidra.ibge.gov.br),
então este script roda sozinho, sem passos manuais.

Tabelas usadas (verificadas em sidra.ibge.gov.br/tabela/<codigo>):
  - 6579: População residente estimada (Estimativas de População, anual).
          Usada duas vezes: uma vez com period="last" (para o dataset
          principal) e outra vez pro ano específico do PIB, pra calcular o
          PIB per capita corretamente (ver abaixo).
  - 5938: PIB dos Municípios -- usamos a variável de PIB total (a preços
          correntes). Essa tabela NÃO tem uma variável de "PIB per capita";
          calculamos isso por fora, dividindo o PIB total pela população do
          MESMO ANO de referência do PIB (que fica ~2 anos atrás da
          estimativa populacional mais recente). A tabela 6784 tem uma
          variável de per capita pronta, mas só existe até nível de UF, não
          desce a município -- não dá pra usar aqui.
  - 9923: População residente por situação do domicílio, CENSO 2022 -- usada
          para calcular a taxa de urbanização (pop. urbana / pop. total).

          ATENÇÃO: NÃO use a tabela 202 para isso. Ela é do Censo antigo e
          seus períodos publicados param em 2010 (verificado na API:
          [1970, 1980, 1991, 2000, 2010]). Pedir period="last" nela devolve
          silenciosamente o Censo 2010 -- 15 anos defasado -- para uma das
          duas únicas features do bloco socioeconômico. A tabela do Censo
          2022 que desce a município (N6) é a 9923, com a classificação 1
          (Situação do domicílio: 6795=Total, 1=Urbana, 2=Rural).

          Como só existe ano de Censo, trate a urbanização como variável
          "quase-estática" no dataset.

ANOS DE REFERÊNCIA (verificados na API dos períodos):
  6579 -> [..., 2020, 2021, 2024, 2025, 2026]: SEM 2022 e SEM 2023, que são
          anos de Censo/recalibração. Por isso a janela 2023-2025 usa a
          população de 2024 (config.ANO_POPULACAO_REF) como denominador
          único, e não a de cada ano.
  5938 -> último período publicado: 2023.
  9923 -> período único: 2022.
"""
from __future__ import annotations

import sys
import pandas as pd
import requests
import sidrapy

from config import (
    UF_CODE_SP, POPULACAO_CSV, PIB_PERCAPITA_CSV, URBANIZACAO_CSV,
    TABELA_POPULACAO, TABELA_PIB, TABELA_URBANIZACAO,
    ANO_CENSO_URBANIZACAO, ANO_POPULACAO_REF,
)


def _print_debug(label: str, df: pd.DataFrame) -> None:
    print(f"\n[debug] {label}: {df.shape[0]} linhas, colunas = {list(df.columns)}")


def _descobrir_variavel(tabela: str, precisa_conter: list[str], nao_pode_conter: list[str] | None = None) -> tuple[str, str]:
    """
    Descobre dinamicamente o código de uma variável de uma tabela, consultando
    a API de metadados do IBGE, filtrando pelo nome.

    `precisa_conter`: todos esses trechos (case-insensitive) devem aparecer no
    nome da variável. `nao_pode_conter`: nenhum desses trechos pode aparecer
    (útil pra excluir variantes tipo "Participação de ... no ...").
    """
    url = f"https://servicodados.ibge.gov.br/api/v3/agregados/{tabela}/metadados"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    variaveis = resp.json().get("variaveis", [])

    nao_pode_conter = nao_pode_conter or []

    def bate(nome: str) -> bool:
        nome_lower = nome.lower()
        return (
            all(t.lower() in nome_lower for t in precisa_conter)
            and not any(t.lower() in nome_lower for t in nao_pode_conter)
        )

    candidatas = [v for v in variaveis if bate(v.get("nome", ""))]
    if not candidatas:
        disponiveis = [(v.get("id"), v.get("nome")) for v in variaveis]
        raise SystemExit(
            f"Não encontrei nenhuma variável com {precisa_conter!r} (excluindo "
            f"{nao_pode_conter!r}) nos metadados da tabela {tabela}. "
            f"Variáveis disponíveis: {disponiveis}\n"
            f"Ajuste manualmente o filtro em _descobrir_variavel()."
        )
    if len(candidatas) > 1:
        print(f"[aviso] mais de uma variável bateu com o filtro {precisa_conter!r}: "
              f"{[(v['id'], v['nome']) for v in candidatas]}. Usando a primeira.")

    var_id, var_nome = candidatas[0]["id"], candidatas[0]["nome"]
    print(f"[debug] variável identificada em '{tabela}': {var_id} ({var_nome})")
    return str(var_id), var_nome


def _descobrir_classificacao(tabela: str, contem: str) -> tuple[str, str]:
    """
    Descobre o código de uma classificação (ex.: "Situação do domicílio") de
    uma tabela, consultando a API de metadados do IBGE.
    """
    url = f"https://servicodados.ibge.gov.br/api/v3/agregados/{tabela}/metadados"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    classificacoes = resp.json().get("classificacoes", [])

    contem_lower = contem.lower()
    candidatas = [c for c in classificacoes if contem_lower in c.get("nome", "").lower()]
    if not candidatas:
        disponiveis = [(c.get("id"), c.get("nome")) for c in classificacoes]
        raise SystemExit(
            f"Não encontrei nenhuma classificação com {contem!r} nos metadados "
            f"da tabela {tabela}. Classificações disponíveis: {disponiveis}"
        )
    if len(candidatas) > 1:
        print(f"[aviso] mais de uma classificação bateu com {contem!r}: "
              f"{[(c['id'], c['nome']) for c in candidatas]}. Usando a primeira.")

    class_id, class_nome = candidatas[0]["id"], candidatas[0]["nome"]
    print(f"[debug] classificação identificada em '{tabela}': {class_id} ({class_nome})")
    return str(class_id), class_nome


def _periodos_disponiveis(tabela: str) -> list[str]:
    """Lista os períodos (anos) que a tabela realmente tem publicados no SIDRA."""
    url = f"https://servicodados.ibge.gov.br/api/v3/agregados/{tabela}/periodos"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return [str(p["id"]) for p in resp.json()]


def _filtrar_sp(df: pd.DataFrame, col_codigo: str = "D1C") -> pd.DataFrame:
    """Mantém apenas municípios cujo código IBGE começa com 35 (SP)."""
    return df[df[col_codigo].astype(str).str.startswith(UF_CODE_SP)].copy()


def get_populacao(periodo: str = "last") -> pd.DataFrame:
    """
    População residente estimada por município de SP.

    Não use period="last" para o denominador das taxas: hoje isso traria 2026.
    O denominador da janela 2023-2025 é a população de config.ANO_POPULACAO_REF
    (2024, o ponto médio da janela), e quem passa esse período é o main().
    """
    print(f"Baixando população (tabela {TABELA_POPULACAO}, "
          f"período={periodo})...")
    df = sidrapy.get_table(
        table_code=TABELA_POPULACAO,
        territorial_level="6",
        ibge_territorial_code="all",
        period=periodo,
    )
    # A primeira linha do retorno do sidrapy já vem como cabeçalho (pandas=True
    # por padrão na versão atual da lib devolve DataFrame com nomes D1C, D1N, V...)
    _print_debug("população (bruto)", df)
    df = _filtrar_sp(df)
    df = df.rename(columns={
        "D1C": "codigo_ibge",
        "D1N": "municipio",
        "V": "populacao",
        "D2N": "ano_populacao",
    })
    cols = [c for c in ["codigo_ibge", "municipio", "populacao", "ano_populacao"] if c in df.columns]
    df = df[cols]
    df["populacao"] = pd.to_numeric(df["populacao"], errors="coerce")
    return df.reset_index(drop=True)


def get_pib_total(periodo: str = "last") -> pd.DataFrame:
    """PIB total (a preços correntes, R$ 1.000) por município de SP, tabela 5938."""
    print(f"Baixando PIB total (tabela 5938, período={periodo})...")

    # A tabela 5938 tem ~40 variáveis (PIB total, VAB por setor, impostos,
    # participações percentuais...). Pedimos só a de PIB total em R$ correntes
    # -- filtrando explicitamente para não pegar as variantes "Participação
    # do PIB ... na UF/mesorregião/etc", que também contêm o mesmo texto base.
    variavel, _ = _descobrir_variavel(
        TABELA_PIB,
        precisa_conter=["produto interno bruto", "preços correntes"],
        nao_pode_conter=["participação"],
    )

    df = sidrapy.get_table(
        table_code=TABELA_PIB,
        territorial_level="6",
        ibge_territorial_code="all",
        variable=variavel,
        period=periodo,
    )
    _print_debug("PIB total (bruto)", df)

    df = _filtrar_sp(df)
    df = df.rename(columns={
        "D1C": "codigo_ibge",
        "D1N": "municipio",
        "V": "pib_total_mil_reais",
        "D2N": "ano_pib",
    })
    cols = [c for c in ["codigo_ibge", "municipio", "pib_total_mil_reais", "ano_pib"] if c in df.columns]
    df = df[cols]
    df["pib_total_mil_reais"] = pd.to_numeric(df["pib_total_mil_reais"], errors="coerce")
    return df.reset_index(drop=True)


def get_pib_percapita() -> pd.DataFrame:
    """
    PIB per capita por município de SP.

    IMPORTANTE: nenhuma tabela municipal do SIDRA traz "PIB per capita"
    pronto -- a 5938 (PIB dos Municípios) só tem PIB total/VAB/impostos, e a
    6784 (que tem per capita) só existe até o nível de Unidade da Federação,
    não desce a município (dá erro "Parâmetro N6 incompatível com a tabela").

    Por isso calculamos por fora: PIB total (tabela 5938) dividido pela
    população residente (tabela 6579) **do mesmo ano de referência do PIB**.
    O PIB municipal do IBGE tem defasagem de ~2 anos em relação à estimativa
    populacional mais recente, então usar periodo="last" em população daria
    um ano diferente do PIB e o cálculo ficaria incorreto.
    """
    pib_total = get_pib_total()

    anos_pib = pib_total["ano_pib"].dropna().unique() if "ano_pib" in pib_total.columns else []
    if len(anos_pib) != 1:
        raise SystemExit(
            f"Esperava um único ano de referência no PIB total, mas veio "
            f"{list(anos_pib)}. Ajuste get_pib_percapita() para tratar múltiplos anos."
        )
    ano_pib = str(anos_pib[0])
    print(f"[debug] ano de referência do PIB: {ano_pib} -- buscando população desse mesmo ano")

    # Nem todo ano existe como período publicado na tabela 6579 (anos de
    # Censo, por exemplo, saem por tabelas separadas). Checamos os períodos
    # realmente disponíveis e, se o ano do PIB não estiver lá, usamos o ano
    # disponível mais próximo (o mais recente <= ano do PIB) em vez de travar.
    periodos_pop = _periodos_disponiveis(TABELA_POPULACAO)
    if ano_pib in periodos_pop:
        periodo_pop = ano_pib
    else:
        anteriores = [p for p in periodos_pop if p.isdigit() and int(p) <= int(ano_pib)]
        if not anteriores:
            raise SystemExit(
                f"Ano do PIB ({ano_pib}) não está nos períodos da tabela 6579 "
                f"({periodos_pop}) e não achei nenhum período anterior pra usar "
                f"como aproximação. Ajuste manualmente get_pib_percapita()."
            )
        periodo_pop = max(anteriores, key=int)
        print(f"[aviso] população não publicada para {ano_pib} na tabela 6579 "
              f"(provavelmente ano de Censo/transição). Usando o período "
              f"disponível mais próximo: {periodo_pop}.")

    populacao_ano_pib = get_populacao(periodo=periodo_pop)

    df = pib_total.merge(
        populacao_ano_pib[["codigo_ibge", "populacao"]],
        on="codigo_ibge",
        how="left",
    )
    faltando = df["populacao"].isna().sum()
    if faltando:
        print(f"[aviso] {faltando} município(s) sem população para {ano_pib}; "
              f"pib_percapita vai ficar NaN pra eles.")

    df["pib_percapita"] = (df["pib_total_mil_reais"] * 1000) / df["populacao"]
    cols = ["codigo_ibge", "municipio", "pib_percapita", "pib_total_mil_reais", "populacao", "ano_pib"]
    return df[[c for c in cols if c in df.columns]].reset_index(drop=True)


def get_urbanizacao(periodo: str = ANO_CENSO_URBANIZACAO) -> pd.DataFrame:
    """
    Taxa de urbanização (%) por município de SP, a partir do Censo 2022
    (tabela 9923: população residente por situação do domicílio).

    NÃO troque para a tabela 202: ela é do Censo antigo e seus períodos param
    em 2010, então `period="last"` devolveria o Censo 2010 sem avisar. Ver a
    nota no topo do módulo.

    Só existe para ano de Censo -- é uma variável quase-estática no dataset.
    """
    print(f"Baixando situação do domicílio (tabela {TABELA_URBANIZACAO}, "
          f"Censo {periodo}) para calcular urbanização...")

    disponiveis = _periodos_disponiveis(TABELA_URBANIZACAO)
    if periodo not in disponiveis:
        raise SystemExit(
            f"A tabela {TABELA_URBANIZACAO} não publica o período {periodo}. "
            f"Períodos disponíveis: {disponiveis}. Ajuste "
            "ANO_CENSO_URBANIZACAO em config.py."
        )

    # Sem passar `classification=.../all`, o SIDRA devolve só a categoria
    # "Total" agregada -- nunca a quebra Urbana/Rural que precisamos pra
    # calcular a taxa. Descobrimos o código da classificação dinamicamente
    # e pedimos explicitamente todas as categorias dela.
    class_id, _ = _descobrir_classificacao(TABELA_URBANIZACAO,
                                           "situação do domicílio")
    # A 9923 tem duas variáveis (93 = população em pessoas, 1000093 = % do
    # total). Pedimos a de contagem e calculamos a taxa por fora, para não
    # depender do denominador que o IBGE escolheu para o percentual.
    variavel, _ = _descobrir_variavel(
        TABELA_URBANIZACAO,
        precisa_conter=["população residente"],
        nao_pode_conter=["percentual"],
    )

    df = sidrapy.get_table(
        table_code=TABELA_URBANIZACAO,
        territorial_level="6",
        ibge_territorial_code="all",
        variable=variavel,
        classification=f"{class_id}/all",
        period=periodo,
    )
    _print_debug("situação do domicílio (bruto)", df)

    # Filtra pra SP ANTES de qualquer outra coisa: isso também descarta uma
    # linha "fantasma" que o sidrapy às vezes deixa no topo do DataFrame, com
    # os próprios rótulos das dimensões como se fossem dado (ex.: D4N =
    # "Situação do domicílio" em vez de "Urbana"/"Rural"/"Total") -- essa
    # linha nunca começa com o código "35", então some no filtro.
    df = _filtrar_sp(df)
    df["V"] = pd.to_numeric(df["V"], errors="coerce")

    # Coluna de classificação (situação do domicílio: Urbana / Rural / Total).
    # Procuramos pelo conteúdo (não pela posição da dimensão), que muda
    # conforme a tabela tem mais classificações (aqui, também sexo).
    col_categoria = None
    candidatas_cat = [c for c in df.columns if c.startswith("D") and c.endswith("N") and c != "D1N"]
    for candidate in candidatas_cat:
        valores = set(str(v).strip().lower() for v in df[candidate].dropna().unique())
        if "urbana" in valores and "total" in valores:
            col_categoria = candidate
            break
    if col_categoria is None:
        detalhes = {c: sorted(df[c].dropna().unique().tolist())[:10] for c in candidatas_cat}
        raise SystemExit(
            "Não identifiquei a coluna de situação do domicílio (nenhuma "
            f"coluna com valores 'Urbana'/'Total'). Colunas e valores: {detalhes}"
        )

    pivot = df.pivot_table(
        index=["D1C", "D1N"], columns=col_categoria, values="V", aggfunc="sum"
    ).reset_index()
    pivot = pivot.rename(columns={"D1C": "codigo_ibge", "D1N": "municipio"})

    col_urbana = next((c for c in pivot.columns if "urbana" in str(c).lower()), None)
    col_total = next((c for c in pivot.columns if "total" in str(c).lower()), None)
    if col_urbana is None or col_total is None:
        raise SystemExit(
            "Não encontrei colunas 'Urbana' e/ou 'Total' após o pivot. "
            f"Colunas: {list(pivot.columns)}."
        )

    pivot["taxa_urbanizacao"] = (pivot[col_urbana] / pivot[col_total]) * 100
    return pivot[["codigo_ibge", "municipio", "taxa_urbanizacao"]].reset_index(drop=True)


def main() -> None:
    # O denominador das taxas é a população de ANO_POPULACAO_REF (2024), e
    # não a mais recente publicada -- period="last" traria 2026.
    periodo_pop = ("last" if ANO_POPULACAO_REF is None
                   else str(ANO_POPULACAO_REF))
    populacao = get_populacao(periodo=periodo_pop)
    populacao.to_csv(POPULACAO_CSV, index=False)
    print(f"-> salvo em {POPULACAO_CSV} ({len(populacao)} municípios)")

    pib = get_pib_percapita()
    pib.to_csv(PIB_PERCAPITA_CSV, index=False)
    print(f"-> salvo em {PIB_PERCAPITA_CSV} ({len(pib)} municípios)")

    urban = get_urbanizacao()
    urban.to_csv(URBANIZACAO_CSV, index=False)
    print(f"-> salvo em {URBANIZACAO_CSV} ({len(urban)} municípios)")


if __name__ == "__main__":
    sys.path.insert(0, str(__file__).replace("ibge_sidra.py", ""))
    main()
