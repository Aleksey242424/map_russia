FROM python:3.10-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    gdal-bin \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Копируем requirements.txt из корня проекта (рядом с Dockerfile)
COPY requirements.txt .

RUN pip config set global.index-url https://mirrors.yandex.ru/pypi/simple/
# или https://pypi.org/simple/ (если заработает)
RUN pip install -r requirements.txt

# Копируем ВСЕ файлы из текущей директории (где лежит Dockerfile) в /app
COPY . .

# Копируем скрипт инициализации (если есть)
COPY init-db.sh /init-db.sh
RUN chmod +x /init-db.sh

EXPOSE 8000

# Запуск (файлы main.py, database.py и т.д. теперь внутри контейнера в /app)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]