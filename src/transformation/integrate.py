"""
Integração dos três datasets transformados.
Chave de join: date. Produz dataset_final.csv em data/processed/.
"""

import pandas as pd
from pathlib import Path
from src.utils.logger import get_logger

logger = get_logger(__name__)

PROCESSED_DIR = Path("data/processed")


def load_features() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    def _load(name: str) -> pd.DataFrame:
        path = PROCESSED_DIR / name
        if not path.exists():
            raise FileNotFoundError(f"Execute a transformação antes: {path}")
        return pd.read_csv(path, parse_dates=["date"])

    return (
        _load("air_quality_features.csv"),
        _load("climate_features.csv"),
        _load("health_features.csv"),
    )


def align_dates(*dfs: pd.DataFrame) -> tuple[pd.DataFrame, ...]:
    """Garante que 'date' está em datetime sem timezone em todos os datasets."""
    aligned = []
    for df in dfs:
        df["date"] = pd.to_datetime(df["date"]).dt.normalize()
        aligned.append(df)
    return tuple(aligned)


def aggregate_to_state_daily(df_air: pd.DataFrame, df_climate: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Agrega qualidade do ar e clima para nível estadual diário.
    Necessário porque múltiplas estações/localizações existem por data.
    """
    pollution_cols = [c for c in df_air.columns if c.startswith("pollution_")]
    air_agg = (
        df_air.groupby("date")[pollution_cols]
        .mean()
        .reset_index()
    )

    climate_numeric = [
        c for c in df_climate.columns
        if c not in ("date", "station_code", "station_name", "state", "year_month")
        and df_climate[c].dtype in ("float64", "int64")
    ]
    climate_agg = (
        df_climate.groupby("date")[climate_numeric]
        .mean()
        .reset_index()
    )

    return air_agg, climate_agg


def join_datasets(df_air: pd.DataFrame, df_climate: pd.DataFrame, df_health: pd.DataFrame) -> pd.DataFrame:
    df = df_air.merge(df_climate, on="date", how="inner")
    df = df.merge(df_health, on="date", how="inner")
    logger.info(f"Join concluído: {len(df)} registros no dataset_final.")
    return df


def validate(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df.dropna(subset=["date"])
    df = df.drop_duplicates(subset=["date"])
    discarded = before - len(df)
    if discarded:
        logger.warning(f"{discarded} registros removidos na validação do join.")
    return df


def run() -> pd.DataFrame:
    output = PROCESSED_DIR / "dataset_final.csv"
    if output.exists():
        logger.info(f"Já existe: {output}")
        return pd.read_csv(output, parse_dates=["date"])

    df_air, df_climate, df_health = load_features()
    df_air, df_climate, df_health = align_dates(df_air, df_climate, df_health)
    df_air, df_climate = aggregate_to_state_daily(df_air, df_climate)
    df_final = join_datasets(df_air, df_climate, df_health)
    df_final = validate(df_final)

    df_final.to_csv(output, index=False)
    logger.info(f"Salvo: {output} ({len(df_final)} registros, {len(df_final.columns)} colunas)")
    return df_final


if __name__ == "__main__":
    run()
