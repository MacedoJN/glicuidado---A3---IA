FROM python:3.11-slim

WORKDIR /app

# libgomp1 é necessária para o scikit-learn (OpenMP) nas imagens slim.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Instala dependências primeiro (cache de camada do Docker).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código.
COPY . .

# Treina o modelo no build (o dataset já está versionado em data/diabetes.csv),
# para a imagem já vir com modelo, métricas e figuras prontos.
RUN python models/treino_modelo.py

# Banco SQLite em volume persistente (montado pelo docker-compose em /data).
ENV GLICUIDADO_DB_PATH=/data/glicuidado.db

EXPOSE 8501

# As configurações de servidor ficam em .streamlit/config.toml.
CMD ["streamlit", "run", "app.py"]
