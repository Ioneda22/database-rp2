"""
Construção da base final: uma linha por município do estado de São Paulo.

DESENHO DA PESQUISA (etapa única). O artigo clusteriza os municípios sobre a
base INTEGRADA -- criminalidade + vulnerabilidade socioeconômica + efetividade
da gestão entram juntas no espaço de features (ver artigo.tex, linhas 45-47 e
64). Esta base entrega os três blocos rotulados, e o `dicionario_base.csv`
diz a que bloco cada coluna pertence.

CHAVE DE JUNÇÃO: `codigo_ibge`, em todas as fontes. A SSP traz `COD IBGE` e o
IEGM traz `codigo_municipio` -- nenhum casamento por nome é necessário, e
tampouco desejável: `NOME_MUNICIPIO` da SSP é ambíguo (267 nomes com mais de
um código).

TAXAS. As ocorrências viram taxa por 100 mil habitantes-ano:

    taxa = ocorrencias_na_janela / (populacao_ref * exposicao_anos) * 100.000

`exposicao_anos` é lido de `ssp_cobertura.csv` como soma de (meses
observados / 12) por ano da janela. Isso é o que torna comparável uma janela
composta por anos completos e uma janela provisória com um ano parcial -- em
2026 só há 7 meses, logo exposicao_anos = 0,583 e não 1,0.

A BASE MANTÉM OS 645 MUNICÍPIOS. Exclusões (capital, municípios pequenos) são
decisão do script de modelagem, não da base: aqui elas viram apenas flags,
para que a análise de sensibilidade prometida na seção 3.3 do artigo possa ser
feita sem regerar nada.
"""
from __future__ import annotations

import pandas as pd

from config import (
    POPULACAO_CSV, PIB_PERCAPITA_CSV, URBANIZACAO_CSV,
    SSP_PAINEL_CSV, SSP_TEXTURA_CSV, SSP_COMPLEMENTAR_CSV, SSP_COBERTURA_CSV,
    BASE_FINAL_CSV, DICIONARIO_CSV, RELATORIO_TXT,
    ANOS_JANELA, ANO_POPULACAO_REF, POPULACAO_MINIMA, CODIGO_CAPITAL,
    TAXA_POR_HABITANTES, GRUPOS_NATUREZA, NATUREZAS_TIER2, COLUNAS_IEGM,
)
from parse_iegm import carregar_iegm
from parse_ssp import normaliza


def _limpa_nome(serie: pd.Series) -> pd.Series:
    """Os CSVs do SIDRA vêm com sufixo de UF: 'Adamantina - SP' -> 'Adamantina'."""
    return serie.astype(str).str.replace(r"\s*-\s*SP$", "", regex=True).str.strip()


def _codigo(serie: pd.Series) -> pd.Series:
    return serie.astype(str).str.strip().str.replace(r"\.0$", "", regex=True)


# ---------------------------------------------------------------------------

def carregar_ibge() -> pd.DataFrame:
    """Base mestre: os 645 municípios de SP, com população, PIB e urbanização."""
    pop = pd.read_csv(POPULACAO_CSV)
    pop["codigo_ibge"] = _codigo(pop["codigo_ibge"])
    base = pd.DataFrame({
        "codigo_ibge": pop["codigo_ibge"],
        "municipio": _limpa_nome(pop["municipio"]),
        "populacao": pd.to_numeric(pop["populacao"], errors="coerce"),
        "ano_populacao": pop.get("ano_populacao"),
    }).drop_duplicates(subset="codigo_ibge").reset_index(drop=True)

    # PIB per capita é RECALCULADO aqui, e não lido pronto do CSV.
    # Motivo: ibge_sidra.py divide o PIB pela estimativa populacional mais
    # próxima <= ano do PIB; como a tabela 6579 não publica 2022 nem 2023, ele
    # cai em 2021 -- o CSV em disco traz PIB de 2023 sobre população de 2021,
    # o que infla o per capita de municípios em crescimento. Usamos a
    # população de referência da base, que é bem mais próxima do ano do PIB.
    pib = pd.read_csv(PIB_PERCAPITA_CSV)
    pib["codigo_ibge"] = _codigo(pib["codigo_ibge"])
    base = base.merge(
        pib[["codigo_ibge", "pib_total_mil_reais", "ano_pib"]],
        on="codigo_ibge", how="left",
    )
    base["pib_percapita"] = (
        pd.to_numeric(base["pib_total_mil_reais"], errors="coerce") * 1000
    ) / base["populacao"]

    urb = pd.read_csv(URBANIZACAO_CSV)
    urb["codigo_ibge"] = _codigo(urb["codigo_ibge"])
    base = base.merge(urb[["codigo_ibge", "taxa_urbanizacao"]],
                      on="codigo_ibge", how="left")
    return base


def definir_janela(cobertura: pd.DataFrame) -> tuple[list[int], float]:
    """Devolve (anos da janela, exposição em anos-equivalentes)."""
    disponiveis = sorted(cobertura["ano"].astype(int).tolist())
    anos = sorted(ANOS_JANELA) if ANOS_JANELA else disponiveis

    ausentes = [a for a in anos if a not in disponiveis]
    if ausentes:
        raise SystemExit(
            f"ANOS_JANELA pede {ausentes}, mas só há dados da SSP para "
            f"{disponiveis}.\nBaixe os arquivos SPDadosCriminais_<ano>.xlsx "
            "faltantes em data/raw/ssp/ e rode parse_ssp.py de novo."
        )

    meses = cobertura.set_index(cobertura["ano"].astype(int))["n_meses"]
    exposicao = sum(meses[a] / 12.0 for a in anos)
    return anos, exposicao


def agregar_janela(painel: pd.DataFrame, anos: list[int]) -> pd.DataFrame:
    """Soma as ocorrências da janela e as reduz aos grupos do Bloco B."""
    dados = painel[painel["ano"].astype(int).isin(anos)]

    # GRUPOS_NATUREZA é escrito com acento em config.py; o painel guarda a
    # natureza já normalizada. Normalizamos os dois lados para casar.
    mapa = {}
    for grupo, naturezas in GRUPOS_NATUREZA.items():
        for nat in naturezas:
            mapa[normaliza(nat)] = grupo

    nao_mapeadas = sorted(set(dados["natureza"]) - set(mapa))
    if nao_mapeadas:
        print(f"[info] naturezas fora do Bloco B (preservadas no painel, "
              f"ausentes na base final): {nao_mapeadas}")
    faltando = sorted(set(mapa) - set(dados["natureza"]))
    if faltando:
        print(f"[aviso] naturezas de GRUPOS_NATUREZA que NÃO aparecem no "
              f"painel: {faltando}. Confira a grafia em config.py.")

    dados = dados.assign(grupo=dados["natureza"].map(mapa)).dropna(subset=["grupo"])
    largo = (
        dados.groupby(["codigo_ibge", "grupo"])["ocorrencias"].sum()
        .unstack(fill_value=0).reset_index()
    )
    largo.columns.name = None
    # Um grupo pode não ter nenhuma ocorrência em todo o estado na janela.
    for grupo in GRUPOS_NATUREZA:
        if grupo not in largo.columns:
            largo[grupo] = 0
    return largo


def montar_base_final() -> tuple[pd.DataFrame, pd.DataFrame, list[int], float]:
    base = carregar_ibge()

    painel = pd.read_csv(SSP_PAINEL_CSV, dtype={"codigo_ibge": str})
    textura = pd.read_csv(SSP_TEXTURA_CSV, dtype={"codigo_ibge": str})
    comp = pd.read_csv(SSP_COMPLEMENTAR_CSV, dtype={"codigo_ibge": str})
    cobertura = pd.read_csv(SSP_COBERTURA_CSV)

    anos, exposicao = definir_janela(cobertura)
    print(f"Janela: {anos} | exposição = {exposicao:.3f} ano(s)-equivalente(s)")

    # --- população de referência (denominador) ---
    if ANO_POPULACAO_REF is not None:
        ano_pop = ANO_POPULACAO_REF
        if str(base["ano_populacao"].iloc[0]) != str(ano_pop):
            print(f"[aviso] ANO_POPULACAO_REF={ano_pop}, mas o CSV em disco é de "
                  f"{base['ano_populacao'].iloc[0]}. Rode ibge_sidra.py para o "
                  "ano correto ou deixe ANO_POPULACAO_REF=None.")
    ano_pop = base["ano_populacao"].iloc[0]

    # --- Bloco B: taxas de criminalidade ---
    contagens = agregar_janela(painel, anos)
    base = base.merge(contagens, on="codigo_ibge", how="left")
    pessoas_ano = base["populacao"] * exposicao
    for grupo in GRUPOS_NATUREZA:
        base[grupo] = base[grupo].fillna(0)
        base[f"taxa_{grupo}"] = base[grupo] / pessoas_ano * TAXA_POR_HABITANTES
    base["total_ocorrencias_janela"] = base[list(GRUPOS_NATUREZA)].sum(axis=1)
    base = base.drop(columns=list(GRUPOS_NATUREZA))

    # --- Bloco C: textura (proporções, não volumes) ---
    tex = (textura[textura["ano"].astype(int).isin(anos)]
           .groupby("codigo_ibge")[["n_ocorrencias", "n_via_publica",
                                    "n_periodo_conhecido", "n_noturno"]].sum()
           .reset_index())
    base = base.merge(tex, on="codigo_ibge", how="left")
    base["prop_via_publica"] = base["n_via_publica"] / base["n_ocorrencias"]
    base["prop_noturno"] = base["n_noturno"] / base["n_periodo_conhecido"]
    base["cobertura_periodo"] = base["n_periodo_conhecido"] / base["n_ocorrencias"]

    campos_comp = ["veic_furtado", "veic_roubado", "veic_localizado",
                   "veic_subtraido", "veic_moto", "cel_furto", "cel_roubo"]
    cmp_janela = (comp[comp["ano"].astype(int).isin(anos)]
                  .groupby("codigo_ibge")[campos_comp].sum().reset_index())
    base = base.merge(cmp_janela, on="codigo_ibge", how="left")
    for c in campos_comp:
        base[c] = base[c].fillna(0)
    # Efetividade institucional: quantos dos veículos subtraídos voltam.
    base["taxa_recuperacao_veiculo"] = (
        base["veic_localizado"] / base["veic_subtraido"].replace(0, pd.NA)
    )
    base["prop_veiculo_motocicleta"] = (
        base["veic_moto"] / base["veic_subtraido"].replace(0, pd.NA)
    )
    base["prop_celular_em_furto_roubo"] = (
        (base["cel_furto"] + base["cel_roubo"]) /
        base["n_ocorrencias"].replace(0, pd.NA)
    )
    base = base.drop(columns=campos_comp + ["n_via_publica", "n_noturno",
                                            "n_periodo_conhecido"])

    # --- Bloco E: IEGM ---
    iegm = carregar_iegm()
    base = base.merge(iegm.drop(columns=["municipio_iegm"]),
                      on="codigo_ibge", how="left")

    # --- Bloco F: flags de qualidade ---
    base["flag_sem_iegm"] = base["iegm_ord"].isna()
    base["flag_pop_pequena"] = base["populacao"] < POPULACAO_MINIMA
    base["flag_capital"] = base["codigo_ibge"] == CODIGO_CAPITAL
    base["janela_anos"] = "-".join(str(a) for a in (anos[0], anos[-1]))
    base["exposicao_anos"] = round(exposicao, 4)
    base["ano_populacao_ref"] = ano_pop

    base = base.drop(columns=["pib_total_mil_reais"])
    return base, montar_dicionario(base), anos, exposicao


# ---------------------------------------------------------------------------

def montar_dicionario(base: pd.DataFrame) -> pd.DataFrame:
    """
    Dicionário legível por máquina: a que bloco cada coluna pertence e qual é
    o seu papel na modelagem.

    O script de clusterização deve ler ESTE arquivo em vez de listar colunas
    na mão -- é o que permite pesar os blocos explicitamente. Sem peso, os
    três blocos entram no K-means com influência proporcional ao número de
    colunas que cada fonte por acaso tem (o IEGM levaria ~40% do orçamento de
    distância com quase nenhuma variância). Sugestão: peso 1/sqrt(n) por
    bloco, para que criminalidade, socioeconômico e gestão contribuam igual.
    """
    linhas = []

    def add(col, bloco, tipo, papel, desc):
        if col in base.columns:
            linhas.append({"coluna": col, "bloco": bloco, "tipo": tipo,
                           "papel": papel, "descricao": desc})

    add("codigo_ibge", "identificacao", "str", "chave", "Código IBGE de 7 dígitos")
    add("municipio", "identificacao", "str", "rotulo", "Nome oficial IBGE")
    add("populacao", "identificacao", "int", "contexto", "População residente (denominador)")
    add("ano_populacao", "identificacao", "int", "metadado", "Ano da estimativa populacional")

    rotulos = {
        "cvli": "Crimes violentos letais intencionais (homicídio doloso + latrocínio + lesão seguida de morte)",
        "tentativa_homicidio": "Tentativa de homicídio",
        "lesao_dolosa": "Lesão corporal dolosa",
        "roubo_outros": "Roubo (exceto veículo e carga)",
        "roubo_veiculo": "Roubo de veículo",
        "roubo_carga": "Roubo de carga",
        "furto_outros": "Furto (exceto veículo e carga)",
        "furto_veiculo": "Furto de veículo",
        "estupro_total": "Estupro + estupro de vulnerável",
        "trafico": "Tráfico de entorpecentes (mede também intensidade de policiamento)",
    }
    for grupo, desc in rotulos.items():
        papel = "feature_tier2" if grupo in NATUREZAS_TIER2 else "feature"
        add(f"taxa_{grupo}", "criminalidade", "float", papel,
            f"{desc} -- por 100 mil hab./ano")

    add("prop_via_publica", "textura", "float", "validacao_externa",
        "Proporção de ocorrências em via pública (sugerida como validação externa)")
    add("prop_noturno", "textura", "float", "feature_tier2",
        "Proporção de ocorrências noturnas entre as de período conhecido")
    add("cobertura_periodo", "textura", "float", "qualidade",
        "Fração de ocorrências com DESC_PERIODO preenchido (~42% em 2026)")
    add("taxa_recuperacao_veiculo", "textura", "float", "feature_tier2",
        "Veículos localizados / veículos subtraídos -- efetividade institucional")
    add("prop_veiculo_motocicleta", "textura", "float", "feature_tier2",
        "Participação de motos entre os veículos subtraídos")
    add("prop_celular_em_furto_roubo", "textura", "float", "feature_tier2",
        "Ocorrências com celular subtraído / total de ocorrências")

    add("pib_percapita", "socioeconomico", "float", "feature",
        "PIB per capita em R$ (recalculado com a população de referência)")
    # A seção 3.1 do artigo nomeia taxa de urbanização como um dos três
    # indicadores do IBGE de interesse -- entra como feature do bloco.
    add("taxa_urbanizacao", "socioeconomico", "float", "feature",
        "% da população em domicílio urbano (Censo 2022)")
    # `populacao` fica DELIBERADAMENTE fora das features: é a única variável
    # de tamanho num conjunto em que todo o resto já está normalizado por
    # habitante, e entraria dominando os grupos ("cidade grande x pequena").
    # Se quiserem tamanho como eixo explícito, acrescentem log(populacao) e
    # documentem -- por isso ela fica marcada como 'contexto', e não removida.
    add("ano_pib", "socioeconomico", "int", "metadado", "Ano de referência do PIB")

    for destino in COLUNAS_IEGM.values():
        add(f"{destino}_ord", "gestao", "ordinal_1_5", "feature",
            f"IEGM {destino}: conceito convertido em ordinal (C=1 ... A=5)")
        add(f"{destino}_conceito", "gestao", "str", "rotulo",
            f"IEGM {destino}: conceito original em letra")
    add("iegm_exercicio_ref", "gestao", "int", "metadado", "Exercício avaliado pelo IEGM")
    add("iegm_ano_apuracao", "gestao", "int", "metadado", "Ano de apuração do IEGM")

    add("total_ocorrencias_janela", "qualidade", "int", "qualidade",
        "Soma bruta das ocorrências do Bloco B -- detecta subnotificação")
    add("n_ocorrencias", "qualidade", "int", "qualidade",
        "Total de ocorrências de qualquer natureza no município/janela")
    add("flag_sem_iegm", "qualidade", "bool", "flag",
        "Sem nota IEGM (apenas a capital: fiscalizada pelo TCM-SP)")
    add("flag_pop_pequena", "qualidade", "bool", "flag",
        f"População < {POPULACAO_MINIMA} -- sujeito ao problema dos números pequenos")
    add("flag_capital", "qualidade", "bool", "flag", "É o município de São Paulo")
    add("janela_anos", "qualidade", "str", "metadado", "Janela temporal da SSP")
    add("exposicao_anos", "qualidade", "float", "metadado",
        "Anos-equivalentes de exposição (meses observados / 12, somados)")
    add("ano_populacao_ref", "qualidade", "int", "metadado",
        "Ano da população usada como denominador")

    dic = pd.DataFrame(linhas)
    orfas = [c for c in base.columns if c not in set(dic["coluna"])]
    if orfas:
        print(f"[aviso] colunas sem entrada no dicionário: {orfas}")
    return dic


def relatorio(base: pd.DataFrame, dic: pd.DataFrame, anos, exposicao) -> str:
    L = []
    L.append("=" * 68)
    L.append("BASE FINAL -- perfis de municípios paulistas")
    L.append("=" * 68)
    L.append(f"Municípios: {len(base)}   Colunas: {len(base.columns)}")
    L.append(f"Janela SSP: {anos}  ({exposicao:.3f} ano(s)-equivalente(s) de exposição)")
    L.append(f"População de referência: {base['ano_populacao'].iloc[0]}")
    L.append(f"PIB de referência: {base['ano_pib'].dropna().iloc[0]:.0f}")
    if exposicao < 0.999 * len(anos):
        L.append("\n  *** ATENÇÃO: a janela contém ano(s) INCOMPLETO(S). As taxas já")
        L.append("      estão anualizadas pela exposição, mas herdam viés sazonal.")
        L.append("      Trate esta base como PROVISÓRIA até baixar anos completos.")

    L.append("\n--- Municípios aptos à modelagem ---")
    aptos = base[~base["flag_sem_iegm"]]
    L.append(f"Com todos os blocos (crime + socioeconômico + gestão): {len(aptos)}")
    L.append(f"Sem IEGM (fora da modelagem): {int(base['flag_sem_iegm'].sum())} "
             f"-> {', '.join(base.loc[base['flag_sem_iegm'], 'municipio'])}")
    L.append(f"Com população < {POPULACAO_MINIMA:,}: "
             f"{int(base['flag_pop_pequena'].sum())} "
             f"({base['flag_pop_pequena'].mean():.1%}) -- mantidos na base, "
             "usar em análise de sensibilidade")

    L.append("\n--- Valores ausentes ---")
    ausentes = base.isna().sum()
    ausentes = ausentes[ausentes > 0]
    if len(ausentes):
        for col, n in ausentes.items():
            L.append(f"  {col:34s} {n:4d} ({n / len(base):.1%})")
    else:
        L.append("  nenhum")

    L.append("\n--- Bloco B: taxas por 100 mil hab./ano ---")
    L.append(f"  {'variável':30s} {'média':>9s} {'mediana':>9s} {'máx':>10s} {'zeros':>7s}")
    for col in [c for c in base.columns if c.startswith("taxa_")
                and c != "taxa_urbanizacao" and c != "taxa_recuperacao_veiculo"]:
        s = base[col]
        zeros = int((s == 0).sum())
        L.append(f"  {col:30s} {s.mean():9.1f} {s.median():9.1f} "
                 f"{s.max():10.1f} {zeros:5d} ({zeros / len(base):.0%})")
    L.append("\n  Zeros elevados = zero-inflação. Ela cai ao ampliar a janela:")
    L.append("  estimativa Poisson para CVLI -- 1 ano: 46% | 2 anos: 31% | "
             "3 anos: 23% | 5 anos: 14%.")

    L.append("\n--- Espaço de features (etapa única) ---")
    feats = dic[dic["papel"] == "feature"]
    for bloco, grupo in feats.groupby("bloco"):
        L.append(f"  {bloco:18s} {len(grupo):2d} features -> peso sugerido "
                 f"1/sqrt({len(grupo)}) = {1 / len(grupo) ** 0.5:.3f}")
    L.append("  Sem peso por bloco, cada bloco influencia a distância na")
    L.append("  proporção do nº de colunas que a fonte por acaso tem.")
    L.append("\n  Transformações a aplicar NO SCRIPT DE MODELAGEM (não aqui):")
    L.append("    log1p nas taxas e no PIB per capita (fortemente assimétricos),")
    L.append("    depois RobustScaler, ajustado só no subconjunto clusterizado.")
    return "\n".join(L)


def main() -> None:
    base, dic, anos, exposicao = montar_base_final()
    base.to_csv(BASE_FINAL_CSV, index=False, encoding="utf-8")
    dic.to_csv(DICIONARIO_CSV, index=False, encoding="utf-8")
    texto = relatorio(base, dic, anos, exposicao)
    RELATORIO_TXT.write_text(texto, encoding="utf-8")
    print(f"\n-> {BASE_FINAL_CSV}")
    print(f"-> {DICIONARIO_CSV}")
    print(f"-> {RELATORIO_TXT}\n")
    print(texto)


if __name__ == "__main__":
    main()
