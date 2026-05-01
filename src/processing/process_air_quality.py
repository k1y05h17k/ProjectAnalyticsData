"""
Processamento dos dados brutos de qualidade do ar (OpenAQ).
Regras: tratar nulos, corrigir tipos, padronizar colunas, remover duplicatas.
NÃO aplicar regras de negócio nesta etapa.
"""

import pandas as pd
from pathlib import Path
from src.utils.logger import get_logger

logger = get_logger(__name__)

RAW_DIR = Path("data/raw/air_quality")
PROCESSED_DIR = Path("data/processed")

COLUMN_MAP = {
    "location_id": "location_id",
    "location_name": "location_name",
    "parameter": "pollutant",
    "value": "value",
    "unit": "unit",
    "date.utc": "measured_at",
    "date.local": "measured_at_local",
    "coordinates.latitude": "latitude",
    "coordinates.longitude": "longitude",
}

REQUIRED_COLUMNS = ["location_id", "pollutant", "value", "measured_at"]


def load_raw() -> pd.DataFrame:
    files = sorted(RAW_DIR.glob("openaq_*.csv"))
    if not files:
        raise FileNotFoundError(f"Nenhum arquivo OpenAQ encontrado em {RAW_DIR}")
    frames = [pd.read_csv(f) for f in files]
    df = pd.concat(frames, ignore_index=True)
    logger.info(f"{len(df)} registros brutos carregados de {len(files)} arquivo(s).")
    return df


def rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    existing = {k: v for k, v in COLUMN_MAP.items() if k in df.columns}
    return df.rename(columns=existing)


def fix_types(df: pd.DataFrame) -> pd.DataFrame:
    df["measured_at"] = pd.to_datetime(df["measured_at"], utc=True, errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df["location_id"] = df["location_id"].astype(str)
    df["pollutant"] = df["pollutant"].str.lower().str.strip()
    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)

    df = df.drop_duplicates(subset=["location_id", "pollutant", "measured_at"])
    df = df.dropna(subset=REQUIRED_COLUMNS)
    df = df[df["value"] >= 0]

    discarded = before - len(df)
    if discarded:
        logger.info(f"{discarded} registros descartados (duplicatas/nulos/valores negativos).")
    return df


def select_columns(df: pd.DataFrame) -> pd.DataFrame:
    keep = [c for c in REQUIRED_COLUMNS + ["unit", "measured_at_local", "latitude", "longitude", "location_name"] if c in df.columns]
    return df[keep]


def run() -> pd.DataFrame:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    output = PROCESSED_DIR / "air_quality.csv"

    if output.exists():
        logger.info(f"Arquivo já processado: {output}")
        return pd.read_csv(output)

    df = load_raw()
    df = rename_columns(df)
    df = fix_types(df)
    df = clean(df)
    df = select_columns(df)

    df.to_csv(output, index=False)
    logger.info(f"Salvo: {output} ({len(df)} registros)")
    return df


if __name__ == "__main__":
    run()
