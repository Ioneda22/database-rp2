"""
Orquestra a construção da base: aquisição + integração dos dados.

Uso:
    python main.py            # roda o que faltar
    python main.py --forcar   # reprocessa a SSP mesmo se o painel já existir

Rode a partir da raiz do projeto. A etapa cara é a agregação dos microdados da
SSP (arquivos de 34 a 112 MB, milhões de linhas); ela grava um painel
intermediário em data/processed/ e só é refeita se você mandar.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from config import (
    SSP_DIR, IEGM_RAW_PATH, SSP_CRIMINAIS_GLOB,
    POPULACAO_CSV, PIB_PERCAPITA_CSV, URBANIZACAO_CSV,
    SSP_PAINEL_CSV, DATA_PROCESSED,
)


def etapa(titulo: str) -> None:
    print(f"\n{'=' * 68}\n{titulo}\n{'=' * 68}")


def main() -> None:
    forcar = "--forcar" in sys.argv
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

    etapa("1/4 - IBGE/SIDRA (automático)")
    if not (POPULACAO_CSV.exists() and PIB_PERCAPITA_CSV.exists()
            and URBANIZACAO_CSV.exists()):
        import ibge_sidra
        ibge_sidra.main()
    else:
        print("CSVs do IBGE já estão em data/raw/ibge/ -- pulando a consulta.")
        print("(apague os arquivos para forçar uma atualização)")

    etapa("2/4 - Verificando os arquivos baixados manualmente")
    criminais = sorted(SSP_DIR.glob(SSP_CRIMINAIS_GLOB))
    problemas = []
    if not criminais:
        problemas.append(f"nenhum {SSP_CRIMINAIS_GLOB} em {SSP_DIR}")
    if not IEGM_RAW_PATH.exists():
        problemas.append(f"{IEGM_RAW_PATH} não existe")
    if problemas:
        print("Faltam arquivos que precisam ser baixados MANUALMENTE:")
        for p in problemas:
            print(f"  - {p}")
        print("\nVeja o README.md para o passo a passo de cada portal.")
        return
    print(f"SSP: {len(criminais)} arquivo(s) -> "
          f"{', '.join(a.name for a in criminais)}")
    print(f"IEGM: {IEGM_RAW_PATH.name}")

    etapa("3/4 - Agregando os microdados da SSP (município x ano)")
    if SSP_PAINEL_CSV.exists() and not forcar:
        print(f"{SSP_PAINEL_CSV.name} já existe -- pulando.")
        print("(rode `python main.py --forcar` para reprocessar os .xlsx)")
    else:
        import parse_ssp
        parse_ssp.main()

    etapa("4/4 - Integrando as três fontes na base final")
    import merge_bases
    merge_bases.main()


if __name__ == "__main__":
    main()
