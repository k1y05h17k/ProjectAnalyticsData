"""
Orquestrador da camada de processamento.
Entrada: data/raw/ — Saída: data/processed/ (CSV limpos e padronizados)
"""

from src.utils.logger import get_logger
from src.processing import process_air_quality, process_climate, process_health

logger = get_logger("processing")


def run() -> dict:
    logger.info("=== INICIANDO PROCESSAMENTO ===")

    logger.info("--- [1/3] Qualidade do Ar ---")
    df_air = process_air_quality.run()

    logger.info("--- [2/3] Dados Climáticos ---")
    df_climate = process_climate.run()

    logger.info("--- [3/3] Internações Hospitalares ---")
    df_health = process_health.run()

    logger.info("=== PROCESSAMENTO CONCLUÍDO ===")
    return {"air_quality": df_air, "climate": df_climate, "health": df_health}


if __name__ == "__main__":
    run()
