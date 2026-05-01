"""
Orquestrador da camada de transformação e integração.
Entrada: data/processed/ (CSVs limpos) — Saída: data/processed/dataset_final.csv
"""

from src.utils.logger import get_logger
from src.transformation import transform_air_quality, transform_climate, transform_health, integrate

logger = get_logger("transformation")


def run() -> None:
    logger.info("=== INICIANDO TRANSFORMAÇÃO ===")

    logger.info("--- [1/4] Feature Engineering — Qualidade do Ar ---")
    transform_air_quality.run()

    logger.info("--- [2/4] Feature Engineering — Clima ---")
    transform_climate.run()

    logger.info("--- [3/4] Feature Engineering — Saúde ---")
    transform_health.run()

    logger.info("--- [4/4] Integração dos Datasets ---")
    df_final = integrate.run()

    logger.info(f"=== TRANSFORMAÇÃO CONCLUÍDA — dataset_final: {len(df_final)} linhas x {len(df_final.columns)} colunas ===")


if __name__ == "__main__":
    run()
