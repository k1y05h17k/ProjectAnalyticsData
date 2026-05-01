"""
Feature engineering dos dados de internações hospitalares.
Gera contagens diárias, taxa de internações e tempo médio de permanência.
"""

import pandas as pd
from pathlib import Path
from src.utils.logger import get_logger

logger = get_logger(__name__)

PROCESSED_DIR = Path("data/processed")


def load() -> pd.DataFrame:
    path = PROCESSED_DIR / "health.csv"
    if not path.exists():
        raise FileNotFoundError(f"Execute o processamento antes: {path}")
    df = pd.read_csv(path, parse_dates=["admission_date", "discharge_date"])
    return df


def aggregate_daily(df: pd.DataFrame) -> pd.DataFrame:
    """Conta internações por data e município."""
    agg = (
        df.groupby("admission_date")
        .agg(
            admissions=("cid_primary", "count"),
            deaths=("death", "sum") if "death" in df.columns else ("cid_primary", "count"),
            avg_stay_days=("days_hospitalized", "mean") if "days_hospitalized" in df.columns else ("cid_primary", "count"),
        )
        .reset_index()
        .rename(columns={"admission_date": "date"})
    )
    return agg


def add_rolling_average(df: pd.DataFrame, window: int = 7) -> pd.DataFrame:
    df = df.sort_values("date")
    df[f"admissions_ma{window}d"] = df["admissions"].rolling(window, min_periods=1).mean()
    return df


def add_monthly_aggregation(df: pd.DataFrame) -> pd.DataFrame:
    df["year_month"] = df["date"].dt.to_period("M").astype(str)
    return df


def add_cid_breakdown(df_raw: pd.DataFrame) -> pd.DataFrame:
    """Conta internações por subcategoria CID (J0x, J1x, ...) por data."""
    df_raw["cid_group"] = df_raw["cid_primary"].str[:2]
    breakdown = (
        df_raw.groupby(["admission_date", "cid_group"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
        .rename(columns={"admission_date": "date"})
    )
    breakdown.columns = [
        f"cid_{c.lower()}" if c != "date" else c for c in breakdown.columns
    ]
    return breakdown


def run() -> pd.DataFrame:
    output = PROCESSED_DIR / "health_features.csv"
    if output.exists():
        logger.info(f"Já existe: {output}")
        return pd.read_csv(output, parse_dates=["date"])

    df = load()
    df_daily = aggregate_daily(df)
    df_daily = add_rolling_average(df_daily)
    df_daily = add_monthly_aggregation(df_daily)

    df_daily.to_csv(output, index=False)
    logger.info(f"Salvo: {output} ({len(df_daily)} registros)")
    return df_daily


if __name__ == "__main__":
    run()
