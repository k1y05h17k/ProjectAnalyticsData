"""
Feature engineering dos dados de qualidade do ar.
Gera agregações diárias e médias móveis por poluente.
"""

import pandas as pd
from pathlib import Path
from src.utils.logger import get_logger

logger = get_logger(__name__)

PROCESSED_DIR = Path("data/processed")
POLLUTANTS = ["pm25", "pm10", "co", "no2", "o3", "so2"]


def load() -> pd.DataFrame:
    path = PROCESSED_DIR / "air_quality.csv"
    if not path.exists():
        raise FileNotFoundError(f"Execute o processamento antes: {path}")
    df = pd.read_csv(path, parse_dates=["measured_at"])
    df["date"] = df["measured_at"].dt.date
    return df


def aggregate_daily(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega medições horárias para nível diário por poluente e localização."""
    agg = (
        df.groupby(["date", "location_id", "location_name", "pollutant"])["value"]
        .agg(mean_value="mean", max_value="max", min_value="min", count="count")
        .reset_index()
    )
    agg["date"] = pd.to_datetime(agg["date"])
    return agg


def pivot_pollutants(df_daily: pd.DataFrame) -> pd.DataFrame:
    """Pivota poluentes em colunas para facilitar análise e join."""
    pivot = df_daily.pivot_table(
        index=["date", "location_id", "location_name"],
        columns="pollutant",
        values="mean_value",
    ).reset_index()
    pivot.columns = [
        f"pollution_{c}" if c not in ("date", "location_id", "location_name") else c
        for c in pivot.columns
    ]
    return pivot


def add_rolling_average(df: pd.DataFrame, window: int = 7) -> pd.DataFrame:
    """Adiciona média móvel de 7 dias por localização para cada poluente."""
    df = df.sort_values(["location_id", "date"])
    pollution_cols = [c for c in df.columns if c.startswith("pollution_")]
    for col in pollution_cols:
        df[f"{col}_ma{window}d"] = (
            df.groupby("location_id")[col]
            .transform(lambda x: x.rolling(window, min_periods=1).mean())
        )
    return df


def add_monthly_aggregation(df: pd.DataFrame) -> pd.DataFrame:
    df["year_month"] = df["date"].dt.to_period("M").astype(str)
    return df


def run() -> pd.DataFrame:
    output = PROCESSED_DIR / "air_quality_features.csv"
    if output.exists():
        logger.info(f"Já existe: {output}")
        return pd.read_csv(output, parse_dates=["date"])

    df = load()
    df_daily = aggregate_daily(df)
    df_pivot = pivot_pollutants(df_daily)
    df_pivot = add_rolling_average(df_pivot)
    df_pivot = add_monthly_aggregation(df_pivot)

    df_pivot.to_csv(output, index=False)
    logger.info(f"Salvo: {output} ({len(df_pivot)} registros)")
    return df_pivot


if __name__ == "__main__":
    run()
