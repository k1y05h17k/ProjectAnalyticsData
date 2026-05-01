"""
Análise de correlações entre qualidade do ar, clima e internações.
Gera matriz de correlação e ranking das correlações mais relevantes para o ML.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sqlalchemy import text
from src.utils.db import get_engine
from src.utils.logger import get_logger

logger = get_logger(__name__)
PROCESSED_DIR = Path("data/processed")

# Pares de correlação com hipótese específica definida no CLAUDE.md
HYPOTHESIS_PAIRS = [
    ("pollution_pm25",      "admissions",          "PM2.5 × internações respiratórias"),
    ("pollution_pm10",      "admissions",          "PM10 × internações respiratórias"),
    ("pollution_no2",       "admissions",          "NO2 × internações respiratórias"),
    ("pollution_o3",        "admissions",          "O3 × internações respiratórias"),
    ("temperature_c_mean",  "pollution_pm25",      "Temperatura × PM2.5"),
    ("humidity_pct_mean",   "pollution_pm25",      "Umidade × PM2.5"),
    ("temp_variation_c",    "admissions",          "Amplitude térmica × internações"),
    ("precipitation_mm_sum","pollution_pm10",      "Precipitação × PM10"),
]


def load_dataset() -> pd.DataFrame:
    engine = get_engine()
    with engine.connect() as conn:
        df = pd.read_sql(text("SELECT * FROM dataset_final"), conn, parse_dates=["date"])
    return df


def compute_full_matrix(df: pd.DataFrame) -> pd.DataFrame:
    numeric = df.select_dtypes(include="number")
    # Remove colunas de médias móveis para evitar multicolinearidade na análise
    numeric = numeric[[c for c in numeric.columns if "_ma7d" not in c]]
    corr = numeric.corr(method="pearson")
    return corr


def compute_hypothesis_correlations(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for col_a, col_b, label in HYPOTHESIS_PAIRS:
        if col_a not in df.columns or col_b not in df.columns:
            logger.warning(f"Colunas não encontradas: {col_a}, {col_b}")
            continue
        pair = df[[col_a, col_b]].dropna()
        if len(pair) < 10:
            logger.warning(f"Dados insuficientes para: {label}")
            continue
        r = pair[col_a].corr(pair[col_b])
        rows.append({
            "hypothesis": label,
            "col_a": col_a,
            "col_b": col_b,
            "pearson_r": round(r, 4),
            "abs_r": round(abs(r), 4),
            "n_obs": len(pair),
            "strength": _classify_strength(r),
        })

    result = pd.DataFrame(rows).sort_values("abs_r", ascending=False)
    return result


def _classify_strength(r: float) -> str:
    r = abs(r)
    if r >= 0.7:
        return "forte"
    if r >= 0.4:
        return "moderada"
    if r >= 0.2:
        return "fraca"
    return "negligível"


def top_correlations_with_admissions(corr_matrix: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    if "admissions" not in corr_matrix.columns:
        return pd.DataFrame()
    series = corr_matrix["admissions"].drop("admissions").dropna()
    series = series.reindex(series.abs().sort_values(ascending=False).index)
    df = series.head(top_n).reset_index()
    df.columns = ["variable", "pearson_r"]
    df["abs_r"] = df["pearson_r"].abs()
    df["strength"] = df["pearson_r"].apply(_classify_strength)
    return df


def run() -> dict[str, pd.DataFrame]:
    output_dir = PROCESSED_DIR / "analysis"
    output_dir.mkdir(parents=True, exist_ok=True)

    df = load_dataset()

    # Matriz completa
    corr_matrix = compute_full_matrix(df)
    corr_matrix.to_csv(output_dir / "correlation_matrix.csv")
    logger.info(f"Matriz de correlação salva: {corr_matrix.shape}")

    # Correlações hipóteses
    hyp = compute_hypothesis_correlations(df)
    hyp.to_csv(output_dir / "hypothesis_correlations.csv", index=False)
    logger.info("\nCorrelações das hipóteses do projeto:")
    for _, row in hyp.iterrows():
        logger.info(f"  {row['hypothesis']:<45} r={row['pearson_r']:>7.4f}  [{row['strength']}]")

    # Top correlações com internações
    top = top_correlations_with_admissions(corr_matrix)
    if not top.empty:
        top.to_csv(output_dir / "top_correlations_admissions.csv", index=False)
        logger.info("\nVariáveis mais correlacionadas com internações:")
        for _, row in top.iterrows():
            logger.info(f"  {row['variable']:<40} r={row['pearson_r']:>7.4f}  [{row['strength']}]")

    return {"correlation_matrix": corr_matrix, "hypotheses": hyp, "top_admissions": top}


if __name__ == "__main__":
    run()
