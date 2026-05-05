# 1. Imagen base: Usamos una versión ligera de Python 3.10
FROM python:3.10-slim

# 2. Variables de entorno de Python
# Evita que Python genere archivos .pyc y asegura que los logs se vean en tiempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Directorio de trabajo dentro del contenedor
WORKDIR /app

# 4. Instalación de dependencias del sistema necesarias para PostgreSQL y gRPC
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# 5. Gestión de dependencias de Python
# Copiamos primero solo el requirements.txt para aprovechar el caché de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 6. Copiar el código fuente
# Copiamos todo el contenido de tu carpeta actual al directorio /app del contenedor
COPY . .

# Nota: No incluimos un comando CMD final. 
# Esto es porque en el docker-compose.yml cada servicio ejecutará su propio comando:
# (ej. uvicorn, python -m modules.auth.grpc_server, etc.)