"""
Ingestão de dados de internações hospitalares via PySUS (SIH/SUS).
Acessa FTP público do DATASUS sem autenticação. Salva em data/raw/health/.

Requer PySUS instalado no container. Se ausente, o pipeline continua
sem dados de saúde e emite aviso — não interrompe as demais ingestões.
"""

import os
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from src.utils.logger import get_logger

load_dotenv()
logger = get_logger(__name__)

RAW_DIR = Path("data/raw/health")
TARGET_STATE = os.getenv("TARGET_STATE", "SP")
INMET_YEARS = [int(y) for y in os.getenv("INMET_YEARS", "2022,2023").split(",")]
RESPIRATORY_CID_PREFIX = "J"

try:
    from pysus.ftp.databases.sih import SIH as _SIH
    PYSUS_AVAILABLE = True
except ImportError:
    PYSUS_AVAILABLE = False


def _check_pysus() -> bool:
    if not PYSUS_AVAILABLE:
        logger.warning(
            "PySUS não está instalado. Para habilitar a ingestão de dados de saúde:\n"
            "  1. Acesse o container: docker compose exec app bash\n"
            "  2. Execute: pip install PySUS pyarrow\n"
            "  3. Rode novamente: python -m src.ingestion.ingest_health"
        )
        return False
    return True


def _check_pyarrow() -> bool:
    try:
        import pyarrow  # noqa: F401
        return True
    except ImportError:
        logger.warning("pyarrow não instalado. Execute: pip install pyarrow")
        return False


def download_sih(state: str, year: int, month: int) -> pd.DataFrame | None:
    try:
        sih = _SIH().load()
        files = sih.get_files("RD", uf=state, year=year, month=month)
        if not files:
            logger.warning(f"Nenhum arquivo SIH: {state}/{year}/{month:02d}")
            return None
        parquet_dir = str(RAW_DIR / "parquet")
        parquet_files = sih.download(files, local_dir=parquet_dir)
        if not parquet_files:
            return None
        return pd.read_parquet(parquet_files[0])
    except Exception as e:
        logger.error(f"Erro SIH {state}/{year}/{month:02d}: {e}")
        return None


def filter_respiratory(df: pd.DataFrame) -> pd.DataFrame:
    col = "DIAG_PRINC" if "DIAG_PRINC" in df.columns else df.columns[0]
    return df[df[col].astype(str).str.startswith(RESPIRATORY_CID_PREFIX)]


def run() -> None:
    if not _check_pysus() or not _check_pyarrow():
        return

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    (RAW_DIR / "parquet").mkdir(parents=True, exist_ok=True)

    for year in INMET_YEARS:
        output_file = RAW_DIR / f"sih_{TARGET_STATE}_{year}.csv"
        if output_file.exists():
            logger.info(f"Já existe: {output_file}. Pulando.")
            continue

        yearly_frames = []
        for month in range(1, 13):
            logger.info(f"Baixando SIH {TARGET_STATE}/{year}/{month:02d}...")
            df = download_sih(TARGET_STATE, year, month)
            if df is not None:
                df_resp = filter_respiratory(df)
                yearly_frames.append(df_resp)
                logger.info(f"  {len(df_resp)} internações respiratórias.")

        if yearly_frames:
            df_year = pd.concat(yearly_frames, ignore_index=True)
            df_year.to_csv(output_file, index=False)
            logger.info(f"Salvo: {output_file} ({len(df_year)} registros)")
        else:
            logger.warning(f"Nenhum dado para {TARGET_STATE}/{year}.")


if __name__ == "__main__":
    run()
