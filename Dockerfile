FROM python:3.11-slim

WORKDIR /app

# Dependências de sistema necessárias para compilar extensões C (psycopg2, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instala dependências principais
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# PySUS requer Rust para compilar pyreaddbc.
# Instala Rust + PySUS em etapa separada; falha não bloqueia o build.
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y 2>/dev/null || true
ENV PATH="/root/.cargo/bin:${PATH}"
RUN pip install --no-cache-dir PySUS==0.8.1 pyarrow==16.1.0 || \
    echo "AVISO: PySUS não instalado. Ingestão de dados de saúde indisponível."

EXPOSE 8888

CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root", "--NotebookApp.token=''"]
