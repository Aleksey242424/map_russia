#!/bin/bash
set -e

echo "Ожидание запуска PostgreSQL..."
while ! pg_isready -h db -p 5432 -U postgres; do
  sleep 1
done

echo "PostgreSQL готов, выполняем инициализацию..."

# Установка расширения PostGIS (если не установлено)
PGPASSWORD=postgres psql -h db -U postgres -d peoples_db -c "CREATE EXTENSION IF NOT EXISTS postgis;"

# Запуск скрипта создания таблиц и импорта данных (синхронный скрипт)
python /app/import_regions.py

echo "Инициализация завершена. Запускаем FastAPI..."

# Запуск переданной команды (uvicorn)
exec "$@"