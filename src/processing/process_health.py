"""
Processamento dos dados brutos de internações hospitalares (DATASUS/SIH).
Foco em doenças respiratórias (CID-10 capítulo J).
NÃO aplicar regras de negócio nesta etapa.
"""

import os
import pandas as pd
from pathlib import Path
from src.utils.logger import get_logger

logger = get_logger(__name__)

RAW_DIR = Path("data/raw/health")
PROCESSED_DIR = Path("data/processed")
TARGET_STATE = os.getenv("TARGET_STATE", "SP")
INMET_YEARS = [int(y) for y in os.getenv("INMET_YEARS", "2022,2023").split(",")]

COLUMN_MAP = {
    "DIAG_PRINC": "cid_primary",
    "DT_INTER": "admission_date",
    "DT_SAIDA": "discharge_date",
    "MUNIC_RES": "municipality_code",
    "MUNIC_MOV": "hospital_municipality",
    "IDADE": "age",
    "SEXO": "sex",
    "QT_DIARIAS": "days_hospitalized",
    "VAL_TOT": "total_cost",
    "MORTE": "death",
    "DIAG_SECUN": "cid_secondary",
}

REQUIRED_COLUMNS = ["cid_primary", "admission_date"]


def load_raw() -> pd.DataFrame:
    files = [RAW_DIR / f"sih_{TARGET_STATE}_{year}.csv" for year in INMET_YEARS]
    files = [f for f in files if f.exists()]

    if not files:
        raise FileNotFoundError(f"Nenhum arquivo SIH encontrado em {RAW_DIR}")

    frames = [pd.read_csv(f, dtype=str) for f in files]
    df = pd.concat(frames, ignore_index=True)
    logger.info(f"{len(df)} registros brutos carregados de {len(files)} arquivo(s).")
    return df


def rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    mapping = {k: v for k, v in COLUMN_MAP.items() if k in df.columns}
    return df.rename(columns=mapping)


def fix_types(df: pd.DataFrame) -> pd.DataFrame:
    for col in ["admission_date", "discharge_date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], format="%Y%m%d", errors="coerce")

    for col in ["age", "days_hospitalized"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in ["total_cost"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "death" in df.columns:
        df["death"] = df["death"].map({"1": True, "0": False})

    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)

    df = df.dropna(subset=REQUIRED_COLUMNS)
    df = df.drop_duplicates()
    df = df[df["cid_primary"].str.match(r"^J", na=False)]

    discarded = before - len(df)
    if discarded:
        logger.info(f"{discarded} registros descartados (nulos/duplicatas/CID não-respiratório).")
    return df


def select_columns(df: pd.DataFrame) -> pd.DataFrame:
    keep = [c for c in COLUMN_MAP.values() if c in df.columns]
    return df[keep]


def run() -> pd.DataFrame:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    output = PROCESSED_DIR / "health.csv"

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
