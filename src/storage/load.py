"""
Carga dos dados processados no PostgreSQL.
Cada CSV em data/processed/ corresponde a uma tabela normalizada.
Idempotente: usa if_exists='replace' para recarregar sem duplicatas.
"""

import pandas as pd
from pathlib import Path
from sqlalchemy import Engine, inspect, text
from src.utils.db import get_engine
from src.utils.logger import get_logger
from src.storage.schema import (
    AIR_QUALITY_DTYPES,
    CLIMATE_DTYPES,
    HEALTH_DTYPES,
    DATASET_FINAL_DTYPES,
)

logger = get_logger(__name__)
PROCESSED_DIR = Path("data/processed")

TABLES = {
    "air_quality_daily": ("air_quality_features.csv", AIR_QUALITY_DTYPES),
    "climate_daily":     ("climate_features.csv",     CLIMATE_DTYPES),
    "health_daily":      ("health_features.csv",       HEALTH_DTYPES),
    "dataset_final":     ("dataset_final.csv",         DATASET_FINAL_DTYPES),
}

DATE_COLUMNS = {"date", "admission_date", "discharge_date", "measured_at"}


def _parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.columns:
        if col in DATE_COLUMNS:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def _load_table(df: pd.DataFrame, table: str, dtype_map: dict, engine: Engine) -> None:
    valid_dtypes = {k: v for k, v in dtype_map.items() if k in df.columns}
    df.to_sql(
        table,
        engine,
        if_exists="replace",
        index=False,
        dtype=valid_dtypes,
        method="multi",
        chunksize=500,
    )
    logger.info(f"Tabela '{table}' carregada: {len(df)} registros.")


def get_table_summary(engine: Engine) -> None:
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    logger.info(f"Tabelas no banco: {tables}")
    with engine.connect() as conn:
        for table in tables:
            count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            logger.info(f"  {table}: {count} registros")


def run() -> None:
    engine = get_engine()

    for table_name, (filename, dtype_map) in TABLES.items():
        path = PROCESSED_DIR / filename
        if not path.exists():
            logger.warning(f"Arquivo não encontrado, pulando: {path}")
            continue

        logger.info(f"Carregando '{table_name}' a partir de {filename}...")
        df = pd.read_csv(path)
        df = _parse_dates(df)
        _load_table(df, table_name, dtype_map, engine)

    get_table_summary(engine)


if __name__ == "__main__":
    run()
