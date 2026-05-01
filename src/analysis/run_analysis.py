"""
Orquestrador da camada de análise.
Gera estatísticas descritivas, correlações e padrões temporais.
Resultados salvos em data/processed/analysis/.
"""

from src.utils.db import test_connection
from src.utils.logger import get_logger
from src.analysis import descriptive_stats, correlations, temporal_patterns

logger = get_logger("analysis")


def run() -> None:
    logger.info("=== INICIANDO ANÁLISE ===")

    if not test_connection():
        logger.error("Conexão com PostgreSQL falhou.")
        return

    logger.info("--- [1/3] Estatísticas Descritivas ---")
    stats = descriptive_stats.run()

    logger.info("--- [2/3] Correlações ---")
    corr = correlations.run()

    logger.info("--- [3/3] Padrões Temporais ---")
    temporal = temporal_patterns.run()

    logger.info("=== ANÁLISE CONCLUÍDA ===")
    logger.info("Resultados em: data/processed/analysis/")

    # Exibe hipóteses confirmadas (correlação >= 0.4)
    hyp = corr.get("hypotheses", None)
    if hyp is not None and not hyp.empty:
        relevant = hyp[hyp["abs_r"] >= 0.4]
        if not relevant.empty:
            logger.info("\nHipóteses com correlação moderada ou forte (base para ML):")
            for _, row in relevant.iterrows():
                logger.info(f"  ✓ {row['hypothesis']} → r={row['pearson_r']:.4f} [{row['strength']}]")
        else:
            logger.info("Nenhuma correlação moderada/forte encontrada. Revisar dados ou features.")


if __name__ == "__main__":
    run()
