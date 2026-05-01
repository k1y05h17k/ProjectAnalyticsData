"""
Análise estatística descritiva do dataset_final.
Gera resumo de média, mediana, desvio padrão e quartis por grupo de variáveis.
"""

import pandas as pd
from pathlib import Path
from sqlalchemy import text
from src.utils.db import get_engine
from src.utils.logger import get_logger

logger = get_logger(__name__)
PROCESSED_DIR = Path("data/processed")

VARIABLE_GROUPS = {
    "pollution": lambda cols: [c for c in cols if c.startswith("pollution_") and not c.endswith("_ma7d")],
    "climate":   lambda cols: [c for c in cols if any(c.startswith(p) for p in ("temperature_", "humidity_", "precipitation_", "temp_variation"))],
    "health":    lambda cols: [c for c in cols if c in ("admissions", "deaths", "avg_stay_days")],
}


def load_dataset() -> pd.DataFrame:
    engine = get_engine()
    with engine.connect() as conn:
        df = pd.read_sql(text("SELECT * FROM dataset_final"), conn, parse_dates=["date"])
    logger.info(f"dataset_final carregado: {len(df)} registros, {len(df.columns)} colunas.")
    return df


def summarize_group(df: pd.DataFrame, group_name: str, cols: list[str]) -> pd.DataFrame:
    available = [c for c in cols if c in df.columns]
    if not available:
        logger.warning(f"Nenhuma coluna encontrada para o grupo '{group_name}'.")
        return pd.DataFrame()

    stats = df[available].describe(percentiles=[0.25, 0.5, 0.75]).T
    stats["median"]  = df[available].median()
    stats["missing"] = df[available].isnull().sum()
    stats["missing_pct"] = (stats["missing"] / len(df) * 100).round(2)
    stats.index.name = "variable"
    stats["group"] = group_name
    return stats.reset_index()


def run() -> dict[str, pd.DataFrame]:
    output_dir = PROCESSED_DIR / "analysis"
    output_dir.mkdir(parents=True, exist_ok=True)

    df = load_dataset()
    results = {}

    for group_name, col_selector in VARIABLE_GROUPS.items():
        cols = col_selector(df.columns.tolist())
        summary = summarize_group(df, group_name, cols)
        if summary.empty:
            continue

        output = output_dir / f"stats_{group_name}.csv"
        summary.to_csv(output, index=False)
        results[group_name] = summary

        logger.info(f"[{group_name}] {len(summary)} variáveis analisadas → {output.name}")
        for _, row in summary.iterrows():
            logger.info(
                f"  {row['variable']:<35} mean={row['mean']:>8.2f}  "
                f"std={row['std']:>8.2f}  median={row['median']:>8.2f}  "
                f"missing={row['missing_pct']:>5.1f}%"
            )

    return results


if __name__ == "__main__":
    run()
