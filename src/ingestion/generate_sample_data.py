"""
Gera dados sintéticos brutos no formato exato de cada fonte (OpenAQ, INMET, SIH/DATASUS).
Uso: python -m src.ingestion.generate_sample_data
Idempotente: arquivos já existentes são pulados.
"""

import random
import numpy as np
import pandas as pd
from pathlib import Path
from src.utils.logger import get_logger

logger = get_logger(__name__)

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

DATES = pd.date_range("2022-01-01", "2023-12-31", freq="D")

SP_STATIONS = [
    {"id": "A701", "name": "SAO PAULO - IAG", "lat": -23.651, "lon": -46.623},
    {"id": "A711", "name": "SAO PAULO - MIRANTE",  "lat": -23.496, "lon": -46.620},
]

AQ_LOCATIONS = [
    {"id": "100001", "name": "Pinheiros",    "lat": -23.563, "lon": -46.701},
    {"id": "100002", "name": "Ibirapuera",   "lat": -23.587, "lon": -46.657},
    {"id": "100003", "name": "Santo Andre",  "lat": -23.647, "lon": -46.532},
]

POLLUTANTS = {
    "pm25": (10.0, 15.0, 0.0, 150.0),
    "pm10": (20.0, 20.0, 0.0, 300.0),
    "co":   (0.4,  0.2,  0.0,  5.0),
    "no2":  (30.0, 20.0, 0.0, 200.0),
    "o3":   (40.0, 15.0, 0.0, 200.0),
    "so2":  (5.0,  3.0,  0.0,  50.0),
}

CID_J_CODES = [
    "J00", "J06", "J10", "J11", "J18", "J20", "J21", "J22",
    "J40", "J41", "J42", "J43", "J44", "J45", "J46",
]


def _seasonal_multiplier(date: pd.Timestamp) -> float:
    """Winter (Jun-Aug) has higher pollution and health events."""
    month = date.month
    if month in (6, 7, 8):
        return 1.4
    if month in (12, 1, 2):
        return 1.1
    return 1.0


# ---------------------------------------------------------------------------
# 1. Air quality — OpenAQ v3 flat CSV format
# ---------------------------------------------------------------------------

def generate_air_quality() -> None:
    out_dir = Path("data/raw/air_quality")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "openaq_2022_2023.csv"

    if out_file.exists():
        logger.info(f"Já existe: {out_file}. Pulando.")
        return

    rows = []
    for date in DATES:
        mult = _seasonal_multiplier(date)
        for hour in (0, 6, 12, 18):
            ts_utc = date + pd.Timedelta(hours=hour + 3)   # UTC = BRT + 3
            ts_local = date + pd.Timedelta(hours=hour)
            for loc in AQ_LOCATIONS:
                for pollutant, (mu, sigma, lo, hi) in POLLUTANTS.items():
                    value = float(np.clip(np.random.normal(mu * mult, sigma), lo, hi))
                    rows.append({
                        "location_id": loc["id"],
                        "location_name": loc["name"],
                        "parameter": pollutant,
                        "value": round(value, 2),
                        "unit": "µg/m³" if pollutant != "co" else "mg/m³",
                        "date.utc": ts_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "date.local": ts_local.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                        "coordinates.latitude": loc["lat"],
                        "coordinates.longitude": loc["lon"],
                    })

    pd.DataFrame(rows).to_csv(out_file, index=False)
    logger.info(f"Salvo: {out_file} ({len(rows)} registros)")


# ---------------------------------------------------------------------------
# 2. Climate — INMET historical CSV format (8-line metadata + semicolon data)
# ---------------------------------------------------------------------------

def _inmet_header(station: dict, year: int) -> str:
    return (
        f"REGIAO: Sudeste;\n"
        f"UF: SP;\n"
        f"ESTACAO: {station['id']};\n"
        f"NOME: {station['name']};\n"
        f"CODIGO (WMO): {station['id']};\n"
        f"LATITUDE: {station['lat']};\n"
        f"LONGITUDE: {station['lon']};\n"
        f"DATA DE FUNDACAO: 01/01/1960;\n"
    )


def _inmet_data_header() -> str:
    cols = [
        "Data", "Hora UTC",
        "PRECIPITAÇÃO TOTAL, HORÁRIO (mm)",
        "TEMPERATURA DO AR - BULBO SECO, HORARIA (°C)",
        "TEMPERATURA MÁXIMA NA HORA ANT. (AUT) (°C)",
        "TEMPERATURA MÍNIMA NA HORA ANT. (AUT) (°C)",
        "UMIDADE RELATIVA DO AR, HORARIA (%)",
        "UMIDADE REL. MAX. NA HORA ANT. (AUT) (%)",
        "UMIDADE REL. MIN. NA HORA ANT. (AUT) (%)",
        "VENTO, VELOCIDADE HORARIA (m/s)",
        "PRESSAO ATMOSFERICA AO NIVEL DA ESTACAO, HORARIA (mb)",
    ]
    return ";".join(cols) + ";"


def _fmt(v: float) -> str:
    return f"{v:.1f}".replace(".", ",")


def generate_climate() -> None:
    for station in SP_STATIONS:
        for year in (2022, 2023):
            out_dir = Path(f"data/raw/climate/{year}")
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file = out_dir / f"INMET_SE_SP_{station['id']}_{year}.CSV"

            if out_file.exists():
                logger.info(f"Já existe: {out_file}. Pulando.")
                continue

            lines = [_inmet_header(station, year), _inmet_data_header()]
            year_dates = [d for d in DATES if d.year == year]

            for date in year_dates:
                mult = _seasonal_multiplier(date)
                base_temp = 22.0 - (mult - 1.0) * 5.0
                base_humidity = 70.0 + (mult - 1.0) * 10.0

                for hour in range(0, 24, 3):
                    temp = round(float(np.clip(np.random.normal(base_temp, 3.0), 5.0, 40.0)), 1)
                    temp_max = round(temp + abs(float(np.random.normal(2.0, 0.5))), 1)
                    temp_min = round(temp - abs(float(np.random.normal(2.0, 0.5))), 1)
                    hum = round(float(np.clip(np.random.normal(base_humidity, 8.0), 20.0, 100.0)), 1)
                    hum_max = round(min(100.0, hum + abs(float(np.random.normal(5.0, 1.0)))), 1)
                    hum_min = round(max(20.0, hum - abs(float(np.random.normal(5.0, 1.0)))), 1)
                    precip = round(max(0.0, float(np.random.exponential(0.3))), 1)
                    wind = round(max(0.0, float(np.random.exponential(2.0))), 1)
                    pressure = round(float(np.clip(np.random.normal(940.0, 5.0), 900.0, 980.0)), 1)

                    row = ";".join([
                        date.strftime("%Y/%m/%d"),
                        f"{hour * 100:04d}",
                        _fmt(precip),
                        _fmt(temp),
                        _fmt(temp_max),
                        _fmt(temp_min),
                        _fmt(hum),
                        _fmt(hum_max),
                        _fmt(hum_min),
                        _fmt(wind),
                        _fmt(pressure),
                    ]) + ";"
                    lines.append(row)

            out_file.write_text("\n".join(lines), encoding="latin-1")
            logger.info(f"Salvo: {out_file} ({len(lines) - 2} leituras)")


# ---------------------------------------------------------------------------
# 3. Health — SIH/DATASUS flat CSV format
# ---------------------------------------------------------------------------

def generate_health() -> None:
    out_dir = Path("data/raw/health")
    out_dir.mkdir(parents=True, exist_ok=True)

    for year in (2022, 2023):
        out_file = out_dir / f"sih_SP_{year}.csv"

        if out_file.exists():
            logger.info(f"Já existe: {out_file}. Pulando.")
            continue

        rows = []
        year_dates = [d for d in DATES if d.year == year]

        for date in year_dates:
            mult = _seasonal_multiplier(date)
            n_admissions = int(np.random.poisson(35 * mult))

            for _ in range(n_admissions):
                days_stay = max(1, int(np.random.exponential(4.5)))
                discharge = date + pd.Timedelta(days=days_stay)
                is_death = 1 if random.random() < 0.04 else 0
                rows.append({
                    "DIAG_PRINC": random.choice(CID_J_CODES),
                    "DT_INTER": date.strftime("%Y%m%d"),
                    "DT_SAIDA": discharge.strftime("%Y%m%d"),
                    "MUNIC_RES": random.choice(["355030", "354780", "354870"]),
                    "MUNIC_MOV": "355030",
                    "IDADE": random.randint(0, 90),
                    "SEXO": random.choice(["1", "3"]),
                    "QT_DIARIAS": days_stay,
                    "VAL_TOT": round(random.uniform(500.0, 5000.0), 2),
                    "MORTE": str(is_death),
                    "DIAG_SECUN": random.choice(CID_J_CODES + [""]),
                })

        pd.DataFrame(rows).to_csv(out_file, index=False)
        logger.info(f"Salvo: {out_file} ({len(rows)} registros)")


def run() -> None:
    logger.info("=== GERANDO DADOS SINTÉTICOS (substituto de APIs/FTP) ===")
    generate_air_quality()
    generate_climate()
    generate_health()
    logger.info("=== GERAÇÃO CONCLUÍDA ===")


if __name__ == "__main__":
    run()
