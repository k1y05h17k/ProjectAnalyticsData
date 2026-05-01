"""
Processamento dos dados climáticos brutos (INMET).
CSVs do INMET têm 8 linhas de metadados no cabeçalho, separador ';' e decimal ','.
NÃO aplicar regras de negócio nesta etapa.
"""

import os
import re
import pandas as pd
from pathlib import Path
from src.utils.logger import get_logger

load_dotenv_imported = False
try:
    from dotenv import load_dotenv
    load_dotenv()
    load_dotenv_imported = True
except ImportError:
    pass

logger = get_logger(__name__)

RAW_DIR = Path("data/raw/climate")
PROCESSED_DIR = Path("data/processed")
INMET_YEARS = [int(y) for y in os.getenv("INMET_YEARS", "2022,2023").split(",")]

COLUMN_MAP = {
    "data": "date",
    "hora utc": "hour_utc",
    "precipitação total, horário (mm)": "precipitation_mm",
    "temperatura do ar - bulbo seco, horaria (°c)": "temperature_c",
    "temperatura máxima na hora ant. (aut) (°c)": "temp_max_c",
    "temperatura mínima na hora ant. (aut) (°c)": "temp_min_c",
    "umidade relativa do ar, horaria (%)": "humidity_pct",
    "umidade rel. max. na hora ant. (aut) (%)": "humidity_max_pct",
    "umidade rel. min. na hora ant. (aut) (%)": "humidity_min_pct",
    "vento, velocidade horaria (m/s)": "wind_speed_ms",
    "pressao atmosferica ao nivel da estacao, horaria (mb)": "pressure_mb",
}

NUMERIC_COLS = [
    "precipitation_mm", "temperature_c", "temp_max_c", "temp_min_c",
    "humidity_pct", "humidity_max_pct", "humidity_min_pct",
    "wind_speed_ms", "pressure_mb",
]


def _extract_station_metadata(filepath: Path) -> dict:
    """Lê as 8 primeiras linhas de metadados do CSV do INMET."""
    meta = {}
    with open(filepath, encoding="latin-1") as f:
        for _ in range(8):
            line = f.readline().strip()
            if ":" in line:
                key, _, val = line.partition(":")
                meta[key.strip().lower()] = val.strip().strip(";")
    return meta


def _read_inmet_csv(filepath: Path) -> pd.DataFrame:
    meta = _extract_station_metadata(filepath)
    df = pd.read_csv(
        filepath,
        skiprows=8,
        sep=";",
        decimal=",",
        encoding="latin-1",
        na_values=["-9999", "-9999.0", ""],
    )
    df.columns = df.columns.str.lower().str.strip()
    df["station_code"] = meta.get("estacao", "")
    df["station_name"] = meta.get("nome", "")
    df["state"] = meta.get("uf", "")
    df["latitude"] = pd.to_numeric(meta.get("latitude", None), errors="coerce")
    df["longitude"] = pd.to_numeric(meta.get("longitude", None), errors="coerce")
    return df


def load_raw(years: list[int]) -> pd.DataFrame:
    frames = []
    for year in years:
        year_dir = RAW_DIR / str(year)
        if not year_dir.exists():
            logger.warning(f"Diretório não encontrado: {year_dir}")
            continue
        csv_files = list(year_dir.rglob("*.CSV")) + list(year_dir.rglob("*.csv"))
        for f in csv_files:
            try:
                frames.append(_read_inmet_csv(f))
            except Exception as e:
                logger.error(f"Erro ao ler {f.name}: {e}")

    if not frames:
        raise FileNotFoundError(f"Nenhum CSV INMET encontrado em {RAW_DIR}")

    df = pd.concat(frames, ignore_index=True)
    logger.info(f"{len(df)} registros brutos carregados ({len(frames)} arquivos).")
    return df


def rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    mapping = {k: v for k, v in COLUMN_MAP.items() if k in df.columns}
    return df.rename(columns=mapping)


def fix_types(df: pd.DataFrame) -> pd.DataFrame:
    if "date" in df.columns and "hour_utc" in df.columns:
        df["hour_utc"] = df["hour_utc"].astype(str).str.zfill(4).str[:2] + ":00"
        df["measured_at"] = pd.to_datetime(
            df["date"] + " " + df["hour_utc"], format="%Y/%m/%d %H:%M", errors="coerce"
        )
        df = df.drop(columns=["date", "hour_utc"])

    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df.dropna(subset=["measured_at"])
    df = df.drop_duplicates(subset=["station_code", "measured_at"])

    # Remover linhas onde todas as variáveis meteorológicas são nulas
    meteo_cols = [c for c in NUMERIC_COLS if c in df.columns]
    df = df.dropna(subset=meteo_cols, how="all")

    discarded = before - len(df)
    if discarded:
        logger.info(f"{discarded} registros descartados.")
    return df


def run() -> pd.DataFrame:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    output = PROCESSED_DIR / "climate.csv"

    if output.exists():
        logger.info(f"Arquivo já processado: {output}")
        return pd.read_csv(output)

    df = load_raw(INMET_YEARS)
    df = rename_columns(df)
    df = fix_types(df)
    df = clean(df)

    df.to_csv(output, index=False)
    logger.info(f"Salvo: {output} ({len(df)} registros)")
    return df


if __name__ == "__main__":
    run()
