"""
Análise de padrões temporais: tendências mensais e sazonalidade.
Base para as séries temporais que serão plotadas na Fase 8.
"""

import pandas as pd
from pathlib import Path
from sqlalchemy import text
from src.utils.db import get_engine
from src.utils.logger import get_logger

logger = get_logger(__name__)
PROCESSED_DIR = Path("data/processed")


def load_dataset() -> pd.DataFrame:
    engine = get_engine()
    with engine.connect() as conn:
        df = pd.read_sql(text("SELECT * FROM dataset_final"), conn, parse_dates=["date"])
    df = df.sort_values("date")
    return df


def monthly_aggregation(df: pd.DataFrame) -> pd.DataFrame:
    df["year_month"] = df["date"].dt.to_period("M")
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    monthly = df.groupby("year_month")[numeric_cols].mean().reset_index()
    monthly["year_month"] = monthly["year_month"].astype(str)
    return monthly


def monthly_health_totals(df: pd.DataFrame) -> pd.DataFrame:
    """Internações devem ser somadas por mês, não calculada a média."""
    df["year_month"] = df["date"].dt.to_period("M")
    health_cols = [c for c in ["admissions", "deaths"] if c in df.columns]
    totals = df.groupby("year_month")[health_cols].sum().reset_index()
    totals["year_month"] = totals["year_month"].astype(str)
    return totals


def seasonal_profile(df: pd.DataFrame) -> pd.DataFrame:
    """Perfil por mês do ano (janeiro=1, ..., dezembro=12)."""
    df["month"] = df["date"].dt.month
    numeric_cols = [
        c for c in df.select_dtypes(include="number").columns
        if c not in ("month",) and "_ma7d" not in c
    ]
    profile = df.groupby("month")[numeric_cols].mean().reset_index()
    return profile


def run() -> dict[str, pd.DataFrame]:
    output_dir = PROCESSED_DIR / "analysis"
    output_dir.mkdir(parents=True, exist_ok=True)

    df = load_dataset()

    monthly = monthly_aggregation(df)
    monthly.to_csv(output_dir / "monthly_trends.csv", index=False)
    logger.info(f"Tendências mensais: {len(monthly)} períodos.")

    health_totals = monthly_health_totals(df)
    health_totals.to_csv(output_dir / "monthly_health_totals.csv", index=False)
    logger.info(f"Totais mensais de internações: {len(health_totals)} períodos.")

    seasonal = seasonal_profile(df)
    seasonal.to_csv(output_dir / "seasonal_profile.csv", index=False)
    logger.info(f"Perfil sazonal por mês: {len(seasonal)} meses.")

    return {
        "monthly_trends": monthly,
        "health_totals": health_totals,
        "seasonal_profile": seasonal,
    }


if __name__ == "__main__":
    run()
