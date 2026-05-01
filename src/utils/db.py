"""
Utilitário de conexão com o PostgreSQL via SQLAlchemy.
Lê credenciais exclusivamente do .env.
"""

import os
from sqlalchemy import create_engine, text, Engine
from dotenv import load_dotenv
from src.utils.logger import get_logger

load_dotenv()
logger = get_logger(__name__)


def get_engine() -> Engine:
    url = (
        f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
    return create_engine(url, echo=False)


def test_connection() -> bool:
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Conexão com PostgreSQL estabelecida.")
        return True
    except Exception as e:
        logger.error(f"Falha na conexão com PostgreSQL: {e}")
        return False
