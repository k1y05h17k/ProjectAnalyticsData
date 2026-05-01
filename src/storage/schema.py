"""
Definição explícita dos tipos de coluna por tabela.
Garante que datas, inteiros e floats sejam criados com os tipos corretos no PostgreSQL.
"""

from sqlalchemy import Date, Float, Integer, Text, Boolean

AIR_QUALITY_DTYPES = {
    "date": Date(),
    "location_id": Text(),
    "location_name": Text(),
    "year_month": Text(),
}

CLIMATE_DTYPES = {
    "date": Date(),
    "station_code": Text(),
    "station_name": Text(),
    "state": Text(),
    "year_month": Text(),
}

HEALTH_DTYPES = {
    "date": Date(),
    "admissions": Integer(),
    "deaths": Float(),
    "avg_stay_days": Float(),
    "year_month": Text(),
}

DATASET_FINAL_DTYPES = {
    "date": Date(),
    "admissions": Integer(),
    "year_month": Text(),
}
