"""
Configurações e constantes compartilhadas por todo o pipeline.

Ajuste os valores aqui em vez de espalhar "números mágicos" pelos outros
scripts.
"""
from pathlib import Path

# --- Caminhos -----------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_RAW = BASE_DIR / "data" / "raw"
DATA_PROCESSED = BASE_DIR / "data" / "processed"

SSP_DIR = DATA_RAW / "ssp"
IEGM_DIR = DATA_RAW / "ieg-m"
IBGE_DIR = DATA_RAW / "ibge"

# Os arquivos da SSP vêm um por ano. O pipeline descobre sozinho quais anos
# existem em disco -- basta jogar novos arquivos nessas pastas.
SSP_CRIMINAIS_GLOB = "SPDadosCriminais_*.xlsx"
SSP_VEICULOS_GLOB = "VeiculosSubtraidos_*.xlsx"
SSP_CELULARES_GLOB = "CelularesSubtraidos_*.xlsx"

IEGM_RAW_PATH = IEGM_DIR / "ieg-m.xls"

# Gerados pelo ibge_sidra.py
POPULACAO_CSV = IBGE_DIR / "ibge_populacao.csv"
PIB_PERCAPITA_CSV = IBGE_DIR / "ibge_pib_percapita.csv"
URBANIZACAO_CSV = IBGE_DIR / "ibge_urbanizacao.csv"

# --- Saídas -------------------------------------------------------------
# Camada intermediária (município x ano): cara de gerar, barata de reusar.
SSP_PAINEL_CSV = DATA_PROCESSED / "ssp_painel.csv"
SSP_TEXTURA_CSV = DATA_PROCESSED / "ssp_textura.csv"
SSP_COMPLEMENTAR_CSV = DATA_PROCESSED / "ssp_complementar.csv"
SSP_COBERTURA_CSV = DATA_PROCESSED / "ssp_cobertura.csv"

# Camada final (uma linha por município)
BASE_FINAL_CSV = DATA_PROCESSED / "base_final.csv"
DICIONARIO_CSV = DATA_PROCESSED / "dicionario_base.csv"
RELATORIO_TXT = DATA_PROCESSED / "relatorio_base.txt"

# --- Parâmetros do domínio ----------------------------------------------
UF_CODE_SP = "35"
TAXA_POR_HABITANTES = 100_000
CODIGO_CAPITAL = "3550308"   # São Paulo: fiscalizada pelo TCM-SP, fora do IEGM

# Janela temporal da análise.
#   None  -> usa todos os anos encontrados em data/raw/ssp/
#   lista -> ex.: [2023, 2024, 2025]
#
# A recomendação metodológica é [2023, 2024, 2025]: três anos civis completos,
# posteriores à migração R.D.O. -> S.P.J. (concluída entre 2022 e 2023, ver a
# aba METODOLOGIA dos arquivos da SSP) e posteriores ao choque de mobilidade
# da pandemia. Enquanto só houver 2026 em disco, deixe None.
ANOS_JANELA = None

# Ano de referência da população usada como denominador das taxas.
#   None -> usa o ano disponível no CSV do IBGE que estiver em data/raw/ibge/
# ATENÇÃO: a tabela 6579 do SIDRA não publica estimativa para 2022 nem 2023
# (anos de Censo/recalibração). Para a janela 2023-2025, use 2024 -- o ponto
# médio da janela -- como referência única, e documente a escolha.
ANO_POPULACAO_REF = None

# Limiar de população para sinalizar municípios sujeitos ao problema dos
# números pequenos (uma única ocorrência vira uma taxa altíssima). Não exclui
# ninguém da base: gera apenas a coluna `flag_pop_pequena`, para a análise de
# sensibilidade. Mediana populacional de SP = ~13.500 hab.
POPULACAO_MINIMA = 5_000

# --- IEGM ---------------------------------------------------------------
# O IEGM divulga TODAS as notas (geral e as 7 dimensões) como conceito em
# letra, nunca como número. Esta é a escala ordinal usada na clusterização.
ESCALA_ORDINAL_IEGM = {"C": 1, "C+": 2, "B": 3, "B+": 4, "A": 5}

# nome na planilha -> nome na base final
COLUNAS_IEGM = {
    "iegm": "iegm",
    "iplanejamento": "i_planejamento",
    "ifiscal": "i_fiscal",
    "ieduc": "i_educ",
    "isaude": "i_saude",
    "iamb": "i_amb",
    "icidade": "i_cidade",
    "igov": "i_gov_ti",
}

# --- Agrupamento das naturezas criminais --------------------------------
# Bloco B: as variáveis de criminalidade que entram na clusterização.
# A comparação é feita sobre o texto normalizado (sem acento, maiúsculo).
GRUPOS_NATUREZA = {
    # CVLI (Crimes Violentos Letais Intencionais): indicador padrão da
    # literatura brasileira de segurança pública. Agregar as três naturezas
    # letais reduz a zero-inflação sem inventar nada.
    "cvli": ["HOMICÍDIO DOLOSO", "LATROCÍNIO", "LESÃO CORPORAL SEGUIDA DE MORTE"],
    "tentativa_homicidio": ["TENTATIVA DE HOMICÍDIO"],
    "lesao_dolosa": ["LESÃO CORPORAL DOLOSA"],
    "roubo_outros": ["ROUBO - OUTROS"],
    "roubo_veiculo": ["ROUBO DE VEÍCULO"],
    "roubo_carga": ["ROUBO DE CARGA"],
    "furto_outros": ["FURTO - OUTROS"],
    "furto_veiculo": ["FURTO DE VEÍCULO"],
    "estupro_total": ["ESTUPRO", "ESTUPRO DE VULNERÁVEL"],
    "trafico": ["TRÁFICO DE ENTORPECENTES"],
}

# Naturezas deliberadamente FORA do Bloco B (mas preservadas no painel
# intermediário, caso vocês mudem de ideia):
#   - culposos de trânsito: fenômeno de segurança viária, dirigido por
#     densidade rodoviária, não por padrão de criminalidade;
#   - porte/apreensão de entorpecentes e porte de arma: medem atividade
#     policial (oferta de policiamento), não incidência criminal.
# `trafico` sofre da mesma crítica e foi mantido por medir presença de
# organização criminosa -- registre o caveat no artigo.

# Variáveis de criminalidade consideradas de segunda linha (alta concentração
# em poucos municípios). O script de modelagem decide se entram.
NATUREZAS_TIER2 = ["roubo_carga"]
