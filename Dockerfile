FROM python:3.10-slim

WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Instalar Poetry
RUN pip install --no-cache-dir poetry==1.7.1

# Copiar archivos de configuración de Poetry
COPY pyproject.toml poetry.lock* ./

# Configurar Poetry para que no cree un entorno virtual e instalar dependencias
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi

# Copiar el código de la aplicación
COPY . .

# Exponer el puerto que usará la aplicación
EXPOSE 5000

# Comando para ejecutar la aplicación con gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:create_app()", "--log-level", "debug"]
