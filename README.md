# ProjectAnalyticsData — Air Quality & Health Analytics

Pipeline de engenharia de dados para analisar a relação entre **qualidade do ar**, **condições climáticas** e **internações hospitalares** no estado de São Paulo (2022–2023).

---

## Visão Geral

| Item | Detalhe |
|------|---------|
| Período dos dados | 2022–2023 |
| Região | São Paulo, Brasil |
| Fontes | OpenAQ (poluição), INMET (clima), DATASUS (saúde) |
| Registros brutos | ~93.000 (52K ar + 11K clima + 29K saúde) |
| Dataset final integrado | 731 linhas × 31 colunas |

---

## Arquitetura do Pipeline

```
Fontes de Dados
    ↓
[1. Ingestão]      → /data/raw/         (dados brutos, imutáveis)
    ↓
[2. Processamento] → /data/processed/   (limpeza, tipagem, padronização)
    ↓
[3. Transformação] → feature engineering (médias móveis 7 dias, agregações)
    ↓
[4. Integração]    → dataset_final.csv  (join por data: ar + clima + saúde)
    ↓
[5. Armazenamento] → PostgreSQL         (tabelas normalizadas)
    ↓
[6. Análise]       → correlações, padrões temporais, estatísticas descritivas
    ↓
[7. Visualização]  → 7 gráficos PNG em /data/processed/analysis/plots/
```

Cada etapa possui responsabilidade exclusiva — nunca misturar lógicas entre camadas.

---

## Fontes de Dados

### Qualidade do Ar — OpenAQ
- **Arquivo:** `data/raw/air_quality/openaq_2022_2023.csv`
- **Registros:** 52.561
- **Poluentes:** CO, NO2, O3, PM10, PM2.5, SO2
- **Colunas:** location, pollutant, value, date, unit

### Dados Climáticos — INMET
- **Arquivo:** `data/raw/climate/2022-2023/INMET_*.CSV`
- **Registros:** 11.681
- **Variáveis:** temperatura (média/min/máx), umidade, precipitação, vento, pressão

### Dados de Saúde — DATASUS (SIH-SP)
- **Arquivo:** `data/raw/health/sih_SP_2022-2023.csv`
- **Registros:** 29.034
- **Colunas:** data, internações, óbitos, tempo médio de permanência

---

## Estrutura de Diretórios

```
ProjectAnalyticsData/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env
│
├── data/
│   ├── raw/                          # Dados brutos — nunca modificar
│   │   ├── air_quality/
│   │   ├── climate/
│   │   └── health/
│   └── processed/
│       ├── air_quality.csv
│       ├── climate.csv
│       ├── health.csv
│       ├── air_quality_features.csv
│       ├── climate_features.csv
│       ├── health_features.csv
│       ├── dataset_final.csv         # Dataset integrado (731 linhas × 31 colunas)
│       └── analysis/plots/           # 7 visualizações PNG
│
├── src/
│   ├── ingestion/                    # Carga dos dados brutos
│   │   ├── run_ingestion.py
│   │   ├── ingest_air_quality.py
│   │   ├── ingest_climate.py
│   │   └── ingest_health.py
│   │
│   ├── processing/                   # Limpeza e padronização
│   │   ├── run_processing.py
│   │   ├── process_air_quality.py
│   │   ├── process_climate.py
│   │   └── process_health.py
│   │
│   ├── transformation/               # Feature engineering e integração
│   │   ├── run_transformation.py
│   │   ├── transform_air_quality.py
│   │   ├── transform_climate.py
│   │   ├── transform_health.py
│   │   └── integrate.py
│   │
│   ├── analysis/                     # Análise estatística e visualizações
│   │   ├── run_analysis.py
│   │   ├── descriptive_stats.py
│   │   ├── correlations.py
│   │   ├── temporal_patterns.py
│   │   └── visualizations.py
│   │
│   ├── storage/                      # Persistência no PostgreSQL
│   │   ├── run_storage.py
│   │   ├── load.py
│   │   └── schema.py
│   │
│   └── utils/
│       ├── db.py                     # Conexão SQLAlchemy
│       └── logger.py                 # Logger centralizado
│
└── notebooks/
    └── 01_air_quality_analytics.ipynb
```

---

## Stack Tecnológica

| Categoria | Tecnologia |
|-----------|-----------|
| Linguagem | Python 3.11 |
| Dados | pandas 2.2.2, numpy 1.26.4 |
| Visualização | matplotlib 3.9.0, seaborn 0.13.2 |
| Banco de dados | PostgreSQL 16 |
| ORM / Conexão | SQLAlchemy 2.0.30, psycopg2 2.9.9 |
| Ambiente | Docker + Docker Compose |
| Documentação | JupyterLab 4.2.2 |
| Configuração | python-dotenv 1.0.1 |

---

## Como Executar

### Pré-requisitos

- Docker e Docker Compose instalados

### 1. Configurar variáveis de ambiente

```bash
cp .env.example .env
# Editar .env com as credenciais e thresholds desejados
```

Variáveis obrigatórias no `.env`:

```env
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_DB=analytics
POSTGRES_USER=postgres
POSTGRES_PASSWORD=sua_senha

POLLUTION_THRESHOLD=50.0   # Limiar de poluição alta (µg/m³)
```

### 2. Subir os containers

```bash
docker compose up -d
```

Serviços disponíveis:
- **app** — Python + JupyterLab em `http://localhost:8888`
- **db** — PostgreSQL em `localhost:5432`

### 3. Executar o pipeline

```bash
docker compose exec app python src/ingestion/run_ingestion.py
docker compose exec app python src/processing/run_processing.py
docker compose exec app python src/transformation/run_transformation.py
docker compose exec app python src/storage/run_storage.py
docker compose exec app python src/analysis/run_analysis.py
```

Cada etapa é idempotente — pode ser reexecutada sem efeitos colaterais.

### 4. Abrir o notebook de análise

Acesse `http://localhost:8888` e abra `notebooks/01_air_quality_analytics.ipynb`.

---

## Features Geradas

### Qualidade do Ar
- Concentração diária por poluente (CO, NO2, O3, PM10, PM2.5, SO2)
- Média móvel de 7 dias por poluente
- Indicador binário de poluição alta (baseado no threshold do `.env`)

### Clima
- Temperatura média, mínima e máxima diária
- Variação de temperatura (máx − mín)
- Umidade relativa média
- Precipitação acumulada
- Velocidade do vento e pressão atmosférica
- Médias móveis de 7 dias

### Saúde
- Total de internações diárias
- Total de óbitos diários
- Tempo médio de permanência hospitalar
- Médias móveis de 7 dias

### Dataset Final
- Join de todas as features acima pela chave `data`
- 731 registros (dias únicos), 31 colunas
- Indicadores sazonais (mês, trimestre)

---

## Visualizações Geradas

Salvas em `data/processed/analysis/plots/`:

| Arquivo | Conteúdo |
|---------|---------|
| `01_pollution_timeseries.png` | Série temporal de poluentes (2022–2023) |
| `02_admissions_timeseries.png` | Série temporal de internações |
| `03_correlation_heatmap.png` | Heatmap de correlação entre variáveis |
| `04_pollution_distributions.png` | Distribuição de cada poluente |
| `05_pollution_vs_admissions.png` | Dispersão: poluição × internações |
| `06_monthly_trends.png` | Tendências mensais agregadas |
| `07_seasonal_profile.png` | Perfil sazonal de poluição e saúde |

---

## Regras e Restrições

- Dados em `/data/raw` são imutáveis — nunca modificar
- Todas as configurações via `.env` — nada hardcoded
- Logs via `logging` — nunca `print()`
- Poluição alta: threshold definido no `.env`
- Dado inválido: removido e registrado em log
- Separação estrita de responsabilidades entre camadas

---

## Checklist de Entrega

- [x] Dados carregados dos três datasets (ar, clima, saúde)
- [x] Pipeline end-to-end funcionando (7 etapas)
- [x] Integração entre datasets via join por data
- [x] Feature engineering com médias móveis de 7 dias
- [x] Persistência no PostgreSQL
- [x] Análise de correlações e padrões temporais
- [x] 7 visualizações geradas
- [x] Notebook documentado com insights

---

## Extensões Opcionais (não implementadas)

- Dashboard interativo com Streamlit
- API REST para consulta de dados
- Agendamento automático do pipeline (Airflow / cron)
