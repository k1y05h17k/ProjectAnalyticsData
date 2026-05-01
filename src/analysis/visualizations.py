"""
Geração dos gráficos obrigatórios do projeto.
Salva PNGs em data/processed/analysis/plots/.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from pathlib import Path
from sqlalchemy import text
from src.utils.db import get_engine
from src.utils.logger import get_logger

logger = get_logger(__name__)
PLOTS_DIR = Path("data/processed/analysis/plots")

sns.set_theme(style="whitegrid", palette="muted", font_scale=1.1)
plt.rcParams["figure.dpi"] = 120


def _save(fig: plt.Figure, name: str) -> None:
    path = PLOTS_DIR / name
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    logger.info(f"Gráfico salvo: {path.name}")


def load_dataset() -> pd.DataFrame:
    engine = get_engine()
    with engine.connect() as conn:
        df = pd.read_sql(text("SELECT * FROM dataset_final"), conn, parse_dates=["date"])
    return df.sort_values("date")


# ── 1. Série temporal — poluição ──────────────────────────────────────────────

def plot_pollution_timeseries(df: pd.DataFrame) -> None:
    poll_cols = [c for c in ["pollution_pm25", "pollution_pm10", "pollution_no2", "pollution_o3"] if c in df.columns]
    if not poll_cols:
        logger.warning("Nenhuma coluna de poluição encontrada para série temporal.")
        return

    fig, axes = plt.subplots(len(poll_cols), 1, figsize=(14, 3 * len(poll_cols)), sharex=True)
    if len(poll_cols) == 1:
        axes = [axes]

    for ax, col in zip(axes, poll_cols):
        label = col.replace("pollution_", "").upper()
        ax.plot(df["date"], df[col], linewidth=0.8, alpha=0.7, label=label)
        ma_col = f"{col}_ma7d"
        if ma_col in df.columns:
            ax.plot(df["date"], df[ma_col], linewidth=1.8, label="Média 7d")
        ax.set_ylabel(label)
        ax.legend(loc="upper right", fontsize=9)

    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%b/%Y"))
    fig.autofmt_xdate()
    fig.suptitle("Série Temporal — Qualidade do Ar", fontsize=14, y=1.01)
    _save(fig, "01_pollution_timeseries.png")


# ── 2. Série temporal — internações ──────────────────────────────────────────

def plot_admissions_timeseries(df: pd.DataFrame) -> None:
    if "admissions" not in df.columns:
        return

    fig, ax = plt.subplots(figsize=(14, 4))
    ax.bar(df["date"], df["admissions"], color="steelblue", alpha=0.5, width=1, label="Internações")
    ma_col = "admissions_ma7d"
    if ma_col in df.columns:
        ax.plot(df["date"], df[ma_col], color="crimson", linewidth=2, label="Média 7d")

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b/%Y"))
    fig.autofmt_xdate()
    ax.set_ylabel("Internações / dia")
    ax.set_title("Série Temporal — Internações Respiratórias")
    ax.legend()
    _save(fig, "02_admissions_timeseries.png")


# ── 3. Heatmap de correlação ──────────────────────────────────────────────────

def plot_correlation_heatmap(df: pd.DataFrame) -> None:
    keep = [c for c in df.columns if "_ma7d" not in c and c not in ("date", "year_month", "location_id", "location_name", "station_code", "station_name", "state")]
    numeric = df[keep].select_dtypes(include="number")
    if numeric.shape[1] < 2:
        return

    corr = numeric.corr()
    fig, ax = plt.subplots(figsize=(max(10, len(corr) * 0.7), max(8, len(corr) * 0.6)))
    mask = np.triu(np.ones_like(corr, dtype=bool))
    sns.heatmap(
        corr, mask=mask, annot=True, fmt=".2f", cmap="RdBu_r",
        center=0, vmin=-1, vmax=1, linewidths=0.5,
        annot_kws={"size": 8}, ax=ax,
    )
    ax.set_title("Matriz de Correlação — Dataset Final", pad=12)
    fig.tight_layout()
    _save(fig, "03_correlation_heatmap.png")


# ── 4. Distribuições — poluição ───────────────────────────────────────────────

def plot_pollution_distributions(df: pd.DataFrame) -> None:
    poll_cols = [c for c in ["pollution_pm25", "pollution_pm10", "pollution_no2", "pollution_o3"] if c in df.columns]
    if not poll_cols:
        return

    fig, axes = plt.subplots(2, len(poll_cols), figsize=(4 * len(poll_cols), 8))
    if len(poll_cols) == 1:
        axes = axes.reshape(2, 1)

    for i, col in enumerate(poll_cols):
        label = col.replace("pollution_", "").upper()
        data = df[col].dropna()

        sns.histplot(data, ax=axes[0, i], kde=True, color="steelblue")
        axes[0, i].set_title(f"Distribuição {label}")
        axes[0, i].set_xlabel("")

        sns.boxplot(y=data, ax=axes[1, i], color="lightblue")
        axes[1, i].set_title(f"Boxplot {label}")
        axes[1, i].set_xlabel("")

    fig.suptitle("Distribuições — Poluentes", fontsize=14)
    fig.tight_layout()
    _save(fig, "04_pollution_distributions.png")


# ── 5. Scatter — poluição × internações ──────────────────────────────────────

def plot_pollution_vs_admissions(df: pd.DataFrame) -> None:
    if "admissions" not in df.columns:
        return
    poll_cols = [c for c in ["pollution_pm25", "pollution_pm10"] if c in df.columns]
    if not poll_cols:
        return

    fig, axes = plt.subplots(1, len(poll_cols), figsize=(6 * len(poll_cols), 5))
    if len(poll_cols) == 1:
        axes = [axes]

    for ax, col in zip(axes, poll_cols):
        label = col.replace("pollution_", "").upper()
        data = df[[col, "admissions"]].dropna()
        ax.scatter(data[col], data["admissions"], alpha=0.4, s=20, color="steelblue")

        if len(data) > 2:
            m, b = np.polyfit(data[col], data["admissions"], 1)
            x_line = np.linspace(data[col].min(), data[col].max(), 100)
            ax.plot(x_line, m * x_line + b, color="crimson", linewidth=2, label=f"Tendência")
            r = data[col].corr(data["admissions"])
            ax.set_title(f"{label} × Internações  (r={r:.3f})")

        ax.set_xlabel(label)
        ax.set_ylabel("Internações / dia")
        ax.legend(fontsize=9)

    fig.suptitle("Poluição × Internações Respiratórias", fontsize=13)
    fig.tight_layout()
    _save(fig, "05_pollution_vs_admissions.png")


# ── 6. Tendência mensal ────────────────────────────────────────────────────────

def plot_monthly_trends(df: pd.DataFrame) -> None:
    if "admissions" not in df.columns:
        return

    df = df.copy()
    df["year_month"] = df["date"].dt.to_period("M").astype(str)
    monthly = df.groupby("year_month").agg(
        admissions=("admissions", "sum"),
        **{c: (c, "mean") for c in ["pollution_pm25", "temperature_c_mean"] if c in df.columns},
    ).reset_index()

    fig, ax1 = plt.subplots(figsize=(14, 5))
    ax2 = ax1.twinx()

    ax1.bar(monthly["year_month"], monthly["admissions"], color="steelblue", alpha=0.6, label="Internações (soma)")
    ax1.set_ylabel("Internações / mês", color="steelblue")

    if "pollution_pm25" in monthly.columns:
        ax2.plot(monthly["year_month"], monthly["pollution_pm25"], color="crimson", marker="o", linewidth=2, label="PM2.5 (média)")
        ax2.set_ylabel("PM2.5", color="crimson")

    ticks = monthly["year_month"].tolist()
    ax1.set_xticks(range(len(ticks)))
    ax1.set_xticklabels(ticks, rotation=45, ha="right", fontsize=9)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")

    ax1.set_title("Tendência Mensal — Internações e PM2.5")
    fig.tight_layout()
    _save(fig, "06_monthly_trends.png")


# ── 7. Perfil sazonal ─────────────────────────────────────────────────────────

def plot_seasonal_profile(df: pd.DataFrame) -> None:
    df = df.copy()
    df["month"] = df["date"].dt.month
    month_names = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]

    cols = [c for c in ["pollution_pm25", "admissions", "temperature_c_mean", "humidity_pct_mean"] if c in df.columns]
    if not cols:
        return

    seasonal = df.groupby("month")[cols].mean().reset_index()

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    axes = axes.flatten()

    for ax, col in zip(axes, cols):
        label = col.replace("pollution_", "").replace("_mean", "").replace("_pct", " (%)").replace("_c", " (°C)").upper()
        ax.plot(seasonal["month"], seasonal[col], marker="o", linewidth=2, color="steelblue")
        ax.set_xticks(range(1, 13))
        ax.set_xticklabels(month_names, rotation=45, ha="right", fontsize=9)
        ax.set_title(f"Perfil Sazonal — {label}")
        ax.set_ylabel(label)

    for ax in axes[len(cols):]:
        ax.set_visible(False)

    fig.suptitle("Sazonalidade — Médias por Mês do Ano", fontsize=13)
    fig.tight_layout()
    _save(fig, "07_seasonal_profile.png")


def run() -> None:
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    df = load_dataset()

    plot_pollution_timeseries(df)
    plot_admissions_timeseries(df)
    plot_correlation_heatmap(df)
    plot_pollution_distributions(df)
    plot_pollution_vs_admissions(df)
    plot_monthly_trends(df)
    plot_seasonal_profile(df)

    logger.info(f"Todos os gráficos gerados em {PLOTS_DIR}")


if __name__ == "__main__":
    run()
