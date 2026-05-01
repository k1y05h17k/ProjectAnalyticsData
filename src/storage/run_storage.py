"""
Orquestrador da camada de armazenamento.
Valida conexão antes de carregar os dados.
"""

from src.utils.db import test_connection
from src.utils.logger import get_logger
from src.storage import load

logger = get_logger("storage")


def run() -> None:
    logger.info("=== INICIANDO ARMAZENAMENTO ===")

    if not test_connection():
        logger.error("Conexão com PostgreSQL falhou. Verifique o .env e se o container db está rodando.")
        return

    load.run()
    logger.info("=== ARMAZENAMENTO CONCLUÍDO ===")


if __name__ == "__main__":
    run()
