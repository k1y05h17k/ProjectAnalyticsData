"""
Ingestão de dados climáticos via INMET Dados Históricos.
Download direto sem autenticação. Salva ZIPs e CSVs brutos em data/raw/climate/.
"""

import os
import zipfile
import requests
from pathlib import Path
from dotenv import load_dotenv
from src.utils.logger import get_logger

load_dotenv()
logger = get_logger(__name__)

RAW_DIR = Path("data/raw/climate")
INMET_URL = "https://portal.inmet.gov.br/uploads/dadoshistoricos/{year}.zip"
TARGET_STATE = os.getenv("TARGET_STATE", "SP")
INMET_YEARS = [int(y) for y in os.getenv("INMET_YEARS", "2022,2023").split(",")]


def download_zip(year: int) -> Path:
    zip_path = RAW_DIR / f"inmet_{year}.zip"
    if zip_path.exists():
        logger.info(f"ZIP {year} já existe, pulando download.")
        return zip_path

    url = INMET_URL.format(year=year)
    logger.info(f"Baixando dados INMET {year}...")
    response = requests.get(url, timeout=120, stream=True)
    response.raise_for_status()

    with open(zip_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    logger.info(f"ZIP salvo: {zip_path}")
    return zip_path


def extract_state(zip_path: Path, year: int) -> int:
    output_dir = RAW_DIR / str(year)
    if output_dir.exists() and any(output_dir.iterdir()):
        logger.info(f"INMET {year} já extraído, pulando.")
        return 0

    output_dir.mkdir(parents=True, exist_ok=True)
    extracted = 0

    with zipfile.ZipFile(zip_path, "r") as zf:
        # Estações SP têm sufixo _SP_ no nome do arquivo
        targets = [f for f in zf.namelist() if f"_{TARGET_STATE}_" in f]
        if not targets:
            logger.warning(f"Nenhum arquivo de {TARGET_STATE} encontrado, extraindo tudo.")
            targets = zf.namelist()

        for filename in targets:
            zf.extract(filename, output_dir)
            extracted += 1

    logger.info(f"{extracted} arquivos de {TARGET_STATE} extraídos em {output_dir}")
    return extracted


def run() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    for year in INMET_YEARS:
        zip_path = download_zip(year)
        extract_state(zip_path, year)


if __name__ == "__main__":
    run()
