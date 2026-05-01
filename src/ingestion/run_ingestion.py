"""
Orquestrador da camada de ingestão.
Executa os três scripts em sequência. Idempotente: arquivos já existentes são pulados.
"""

from src.utils.logger import get_logger
from src.ingestion import ingest_air_quality, ingest_climate, ingest_health

logger = get_logger("ingestion")


def run() -> None:
    logger.info("=== INICIANDO INGESTÃO ===")

    logger.info("--- [1/3] Qualidade do Ar (OpenAQ) ---")
    ingest_air_quality.run()

    logger.info("--- [2/3] Dados Climáticos (INMET) ---")
    ingest_climate.run()

    logger.info("--- [3/3] Internações Hospitalares (DATASUS/PySUS) ---")
    ingest_health.run()

    logger.info("=== INGESTÃO CONCLUÍDA ===")


if __name__ == "__main__":
    run()
