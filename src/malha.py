"""
Malha municipal do IBGE (o desenho do contorno de cada município), usada nos
mapas dos perfis.

Baixamos uma vez e guardamos em data/raw/ibge/, como os outros dados brutos.
Nas próximas vezes, lemos do disco.
"""
from __future__ import annotations

import io

import geopandas as gpd
import requests

from config import IBGE_DIR, UF_CODE_SP

MALHA_SP_GEOJSON = IBGE_DIR / "malha_sp_municipios.geojson"

# Fonte principal: API de malhas do IBGE. Conferido em 07/10/2026: devolve os
# 645 municípios, e o código de 7 dígitos vem na propriedade "codarea".
URL_API_MALHAS = (
    f"https://servicodados.ibge.gov.br/api/v3/malhas/estados/{UF_CODE_SP}"
    "?formato=application/vnd.geo+json&intrarregiao=municipio"
    "&qualidade=intermediaria"
)
# Alternativa, se a API não responder: a malha municipal de 2022 em
# shapefile. Conferido em 07/10/2026: 645 municípios, código na coluna CD_MUN.
URL_SHAPEFILE_2022 = (
    "https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/"
    "malhas_municipais/municipio_2022/UFs/SP/SP_Municipios_2022.zip"
)


def _baixar_da_api() -> gpd.GeoDataFrame:
    resposta = requests.get(URL_API_MALHAS, timeout=120)
    resposta.raise_for_status()
    gdf = gpd.read_file(io.BytesIO(resposta.content))
    return gdf.rename(columns={"codarea": "codigo_ibge"})


def _baixar_shapefile() -> gpd.GeoDataFrame:
    resposta = requests.get(URL_SHAPEFILE_2022, timeout=300)
    resposta.raise_for_status()
    # O shapefile vem dentro de um .zip. O geopandas lê o .zip direto, sem
    # precisar descompactar.
    caminho_zip = IBGE_DIR / "SP_Municipios_2022.zip"
    IBGE_DIR.mkdir(parents=True, exist_ok=True)
    caminho_zip.write_bytes(resposta.content)
    gdf = gpd.read_file(caminho_zip)
    return gdf.rename(columns={"CD_MUN": "codigo_ibge"})


def carregar_malha_sp() -> gpd.GeoDataFrame:
    """
    Devolve a malha dos municípios paulistas, com codigo_ibge como texto de
    7 dígitos e o contorno de cada um. Baixa do IBGE só na primeira vez.
    """
    if not MALHA_SP_GEOJSON.exists():
        try:
            gdf = _baixar_da_api()
        except requests.RequestException as erro:
            print(f"API de malhas não respondeu ({erro}); usando o shapefile de 2022")
            gdf = _baixar_shapefile()
        IBGE_DIR.mkdir(parents=True, exist_ok=True)
        gdf[["codigo_ibge", "geometry"]].to_file(MALHA_SP_GEOJSON, driver="GeoJSON")

    gdf = gpd.read_file(MALHA_SP_GEOJSON)
    # Mesmo cuidado dos CSVs: o código é identificador, não número. Sem isso,
    # um código com zero à esquerda perderia o zero e não acharia o par.
    gdf["codigo_ibge"] = gdf["codigo_ibge"].astype(str).str.zfill(7)
    assert gdf["codigo_ibge"].str.len().eq(7).all(), "código IBGE fora do padrão de 7 dígitos"
    assert gdf["codigo_ibge"].is_unique, "município repetido na malha"
    return gdf
