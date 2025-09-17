# Dockerfile para FastAPI
FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Instalar uv
RUN pip install uv

# Copiar archivos de dependencias
COPY pyproject.toml ./
COPY uv.lock* ./

# Crear venv e instalar dependencias
RUN uv venv
RUN uv sync --frozen --no-dev

# Copiar código de la aplicación
COPY . .

# Crear entrypoint script
RUN cat > entrypoint.sh << 'EOF'
#!/bin/bash
set -e

echo "Esperando base de datos..."
until pg_isready -h postgres -p 5432 -U sales_user; do
    echo "Esperando PostgreSQL..."
    sleep 2
done
echo "¡Base de datos lista!"

echo "Ejecutando migraciones..."
uv run alembic upgrade head

echo "Iniciando servidor FastAPI..."
exec uv run uvicorn main:app --host 0.0.0.0 --port 5000 --reload
EOF

RUN chmod +x entrypoint.sh

EXPOSE 5000

ENTRYPOINT ["./entrypoint.sh"]