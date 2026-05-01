"""
Ingestão de dados de qualidade do ar via OpenAQ API v3.
Salva dados brutos em data/raw/air_quality/ sem qualquer transformação.
"""

import os
import time
import requests
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from src.utils.logger import get_logger

load_dotenv()
logger = get_logger(__name__)

RAW_DIR = Path("data/raw/air_quality")
BASE_URL = "https://api.openaq.org/v3"
API_KEY = os.getenv("OPENAQ_API_KEY", "")
HEADERS = {"X-API-Key": API_KEY}
TARGET_STATE = os.getenv("TARGET_STATE", "SP")


def _get(endpoint: str, params: dict) -> dict:
    url = f"{BASE_URL}/{endpoint}"
    response = requests.get(url, headers=HEADERS, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_locations(city: str = "São Paulo", limit: int = 50) -> list[dict]:
    logger.info(f"Buscando estações de qualidade do ar em {city}...")
    data = _get("locations", {"country_id": "BR", "city": city, "limit": limit})
    locations = data.get("results", [])
    logger.info(f"{len(locations)} estações encontradas.")
    return locations


def fetch_measurements(location_id: int, date_from: str, date_to: str, limit: int = 1000) -> list[dict]:
    records = []
    page = 1
    while True:
        data = _get(
            f"locations/{location_id}/measurements",
            {"date_from": date_from, "date_to": date_to, "limit": limit, "page": page},
        )
        batch = data.get("results", [])
        if not batch:
            break
        records.extend(batch)
        if len(batch) < limit:
            break
        page += 1
        time.sleep(0.5)
    return records


def run(date_from: str = "2022-01-01", date_to: str = "2023-12-31") -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    output_file = RAW_DIR / f"openaq_{date_from[:4]}_{date_to[:4]}.csv"
    if output_file.exists():
        logger.info(f"Arquivo já existe: {output_file}. Pulando.")
        return

    locations = fetch_locations()
    if not locations:
        logger.warning("Nenhuma estação encontrada. Verifique a OPENAQ_API_KEY no .env.")
        return

    all_records = []
    for loc in locations:
        loc_id = loc["id"]
        loc_name = loc.get("name", loc_id)
        logger.info(f"Buscando medições: {loc_name} (id={loc_id})")
        try:
            records = fetch_measurements(loc_id, date_from, date_to)
            for r in records:
                r["location_id"] = loc_id
                r["location_name"] = loc_name
            all_records.extend(records)
        except requests.HTTPError as e:
            logger.error(f"Erro ao buscar {loc_name}: {e}")

    if not all_records:
        logger.warning("Nenhuma medição retornada.")
        return

    df = pd.json_normalize(all_records)
    df.to_csv(output_file, index=False)
    logger.info(f"Salvo: {output_file} ({len(df)} registros)")


if __name__ == "__main__":
    run()
