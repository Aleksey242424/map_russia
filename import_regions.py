import os
import sys
import json
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database import DATABASE_URL

# Синхронный URL (убираем асинхронный драйвер)
SYNC_DATABASE_URL = DATABASE_URL.replace("+asyncpg", "").replace("+aiosqlite", "")

def ensure_postgis(engine):
    """Активирует PostGIS, если он установлен"""
    with engine.connect() as conn:
        try:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
            conn.commit()
            print("✓ PostGIS активирован")
        except Exception as e:
            print(f"✗ Не удалось активировать PostGIS: {e}")
            return False
    return True

def create_regions_table(engine):
    """Создаёт таблицу regions, если её нет"""
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS regions (
                id SERIAL PRIMARY KEY,
                name VARCHAR(200),
                geometry geometry(MULTIPOLYGON, 4326)
            );
        """))
        conn.commit()
        print("✓ Таблица regions создана")

def insert_test_regions(engine):
    """Вставляет тестовые полигоны"""
    with engine.connect() as conn:
        # Очищаем старые данные
        conn.execute(text("DELETE FROM regions;"))
        conn.commit()
        
        # Вставляем тестовые регионы (простые прямоугольники)
        conn.execute(text("""
            INSERT INTO regions (name, geometry) VALUES
            ('Москва', ST_GeomFromGeoJSON('{"type":"Polygon","coordinates":[[[37.4,55.6],[37.7,55.6],[37.7,55.9],[37.4,55.9],[37.4,55.6]]]}')),
            ('Санкт-Петербург', ST_GeomFromGeoJSON('{"type":"Polygon","coordinates":[[[30.2,59.8],[30.4,59.8],[30.4,60.0],[30.2,60.0],[30.2,59.8]]]}')),
            ('Татарстан', ST_GeomFromGeoJSON('{"type":"Polygon","coordinates":[[[48.0,55.0],[52.0,55.0],[52.0,56.0],[48.0,56.0],[48.0,55.0]]]}'))
        """))
        conn.commit()
        
        # Проверяем
        count = conn.execute(text("SELECT COUNT(*) FROM regions;")).scalar()
        print(f"✓ Вставлено тестовых регионов: {count}")
        if count == 0:
            print("⚠ Внимание: регионы не вставились. Проверьте PostGIS.")

def import_geojson(engine, path):
    """Импорт реального GeoJSON"""
    with open(path, 'r', encoding='utf-8') as f:
        geojson = json.load(f)
    
    session = Session(engine)
    added = 0
    for feature in geojson.get('features', []):
        props = feature.get('properties', {})
        name = props.get('name') or props.get('admin_name') or props.get('region')
        if not name:
            continue
        geom = json.dumps(feature['geometry'])
        session.execute(
            text("INSERT INTO regions (name, geometry) VALUES (:name, ST_GeomFromGeoJSON(:geom))"),
            {"name": name, "geom": geom}
        )
        added += 1
    session.commit()
    print(f"✓ Импортировано регионов из GeoJSON: {added}")
    session.close()

def main():
    print("=== Импорт границ регионов ===\n")
    print(f"Подключение к БД: {SYNC_DATABASE_URL}")
    engine = create_engine(SYNC_DATABASE_URL, echo=False)
    
    # Шаг 1: PostGIS
    if not ensure_postgis(engine):
        print("\n❌ Ошибка: PostGIS не установлен. Установите PostGIS и повторите.")
        return
    
    # Шаг 2: Таблица
    create_regions_table(engine)
    
    # Шаг 3: Импорт данных
    geojson_path = "data/russia.json"
    if os.path.exists(geojson_path):
        import_geojson(engine, geojson_path)
    else:
        print(f"Файл {geojson_path} не найден, использую тестовые регионы.")
        insert_test_regions(engine)
    
    print("\n✅ Готово! Перезапустите сервер и откройте карту.")

if __name__ == "__main__":
    main()