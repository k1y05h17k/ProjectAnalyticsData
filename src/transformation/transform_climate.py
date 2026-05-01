"""
Feature engineering dos dados climáticos (INMET).
Gera agregações diárias, variação de temperatura e médias mensais por estação.
"""

import pandas as pd
from pathlib import Path
from src.utils.logger import get_logger

logger = get_logger(__name__)

PROCESSED_DIR = Path("data/processed")


def load() -> pd.DataFrame:
    path = PROCESSED_DIR / "climate.csv"
    if not path.exists():
        raise FileNotFoundError(f"Execute o processamento antes: {path}")
    df = pd.read_csv(path, parse_dates=["measured_at"])
    df["date"] = df["measured_at"].dt.date
    return df


def aggregate_daily(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega medições horárias para nível diário por estação."""
    agg_map = {}
    if "temperature_c" in df.columns:
        agg_map["temperature_c"] = ["mean", "max", "min"]
    if "humidity_pct" in df.columns:
        agg_map["humidity_pct"] = ["mean", "max", "min"]
    if "precipitation_mm" in df.columns:
        agg_map["precipitation_mm"] = "sum"
    if "wind_speed_ms" in df.columns:
        agg_map["wind_speed_ms"] = "mean"
    if "pressure_mb" in df.columns:
        agg_map["pressure_mb"] = "mean"

    agg = df.groupby(["date", "station_code", "station_name", "state"]).agg(agg_map)
    agg.columns = ["_".join(c).strip("_") if isinstance(c, tuple) else c for c in agg.columns]
    agg = agg.reset_index()
    agg["date"] = pd.to_datetime(agg["date"])
    return agg


def add_temperature_variation(df: pd.DataFrame) -> pd.DataFrame:
    """Variação diária de temperatura (amplitude térmica)."""
    if "temperature_c_max" in df.columns and "temperature_c_min" in df.columns:
        df["temp_variation_c"] = df["temperature_c_max"] - df["temperature_c_min"]
    return df


def add_rolling_average(df: pd.DataFrame, window: int = 7) -> pd.DataFrame:
    df = df.sort_values(["station_code", "date"])
    for col in ["temperature_c_mean", "humidity_pct_mean", "precipitation_mm_sum"]:
        if col in df.columns:
            df[f"{col}_ma{window}d"] = (
                df.groupby("station_code")[col]
                .transform(lambda x: x.rolling(window, min_periods=1).mean())
            )
    return df


def add_monthly_aggregation(df: pd.DataFrame) -> pd.DataFrame:
    df["year_month"] = df["date"].dt.to_period("M").astype(str)
    return df


def run() -> pd.DataFrame:
    output = PROCESSED_DIR / "climate_features.csv"
    if output.exists():
        logger.info(f"Já existe: {output}")
        return pd.read_csv(output, parse_dates=["date"])

    df = load()
    df_daily = aggregate_daily(df)
    df_daily = add_temperature_variation(df_daily)
    df_daily = add_rolling_average(df_daily)
    df_daily = add_monthly_aggregation(df_daily)

    df_daily.to_csv(output, index=False)
    logger.info(f"Salvo: {output} ({len(df_daily)} registros)")
    return df_daily


if __name__ == "__main__":
    run()
