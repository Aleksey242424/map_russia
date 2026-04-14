from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
import time

from database import engine, get_db, Base
from models import Year, People, PopulationStat
from logger import logger

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database import get_db
from models import Region



@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    logger.info("🚀 Запуск FastAPI приложения")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ Инициализация завершена")
    yield
    # shutdown
    logger.info("🛑 Остановка FastAPI приложения")
    await engine.dispose()
    logger.info("Соединения с БД закрыты")

app = FastAPI(lifespan=lifespan)

# Middleware для логирования HTTP запросов
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    logger.info(f"➡️  {request.method} {request.url.path} - начат")
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(f"⬅️  {request.method} {request.url.path} - завершён за {process_time:.3f}s, статус {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"❌ Ошибка при обработке {request.method} {request.url.path}: {str(e)}", exc_info=True)
        raise

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/api/years")
async def get_years(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(Year.year).order_by(Year.year))
        years = result.scalars().all()
        logger.info(f"Успешно получено {len(years)} годов")
        return {"years": years}
    except Exception as e:
        logger.error(f"Ошибка получения списка годов: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

@app.get("/api/data/{year}")
async def get_data(year: int, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(Year).where(Year.year == year))
        year_record = result.scalar_one_or_none()
        if not year_record:
            logger.warning(f"Год {year} не найден в БД")
            raise HTTPException(status_code=404, detail=f"Данные за {year} год отсутствуют")
        result = await db.execute(
            select(PopulationStat)
            .where(PopulationStat.year_id == year_record.id)
            .options(selectinload(PopulationStat.people))
            .order_by(PopulationStat.population.desc())
        )
        stats = result.scalars().all()
        peoples_data = [
            {
                "name": stat.people.name,
                "population": float(stat.population),
                "percentage": float(stat.percentage)
            }
            for stat in stats
        ]
        return {
            "total_population": float(year_record.total_population),
            "peoples": peoples_data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения данных за {year}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

@app.get("/api/regions/geojson")
async def get_regions_geojson(db: AsyncSession = Depends(get_db)):
    # SQL-запрос: преобразуем геометрию PostGIS в GeoJSON
    result = await db.execute(select(Region.name, func.ST_AsGeoJSON(Region.geometry).label("geojson")))
    rows = result.all()
    features = []
    for row in rows:
        features.append({
            "type": "Feature",
            "properties": {"name": row.name},
            "geometry": json.loads(row.geojson) # Преобразуем строку JSON в объект
        })
    return {"type": "FeatureCollection", "features": features}


@app.get("/")
async def root():
    return FileResponse("static/index.html")

# main.py
from sqlalchemy.orm import selectinload
from sqlalchemy import func
from geoalchemy2.functions import ST_AsGeoJSON
from models import Region
import json

@app.get("/api/regions/geojson")
async def get_regions_geojson(db: AsyncSession = Depends(get_db)):
    """
    Возвращает границы регионов в формате GeoJSON.
    """
    # Запрашиваем имя региона и его геометрию в формате GeoJSON
    result = await db.execute(
        select(Region.name, ST_AsGeoJSON(Region.geometry).label("geojson"))
    )
    rows = result.all()
    
    features = []
    for name, geojson_str in rows:
        # Преобразуем строку JSON в объект Python
        geometry = json.loads(geojson_str)
        features.append({
            "type": "Feature",
            "properties": {"name": name},
            "geometry": geometry
        })
    
    return {
        "type": "FeatureCollection",
        "features": features
    }

@app.get("/api/regions/ethnicity")
async def get_regions_ethnicity(
    year: int, 
    people: str, 
    db: AsyncSession = Depends(get_db)
):
    """
    Возвращает словарь: для каждого региона — процент населения заданной национальности.
    """
    # Находим ID выбранного народа
    people_obj = await db.execute(
        select(People).where(People.name == people)
    )
    people_obj = people_obj.scalar_one_or_none()
    if not people_obj:
        raise HTTPException(status_code=404, detail=f"Народ '{people}' не найден")

    # Находим ID выбранного года
    year_obj = await db.execute(
        select(Year).where(Year.year == year)
    )
    year_obj = year_obj.scalar_one_or_none()
    if not year_obj:
        raise HTTPException(status_code=404, detail=f"Год {year} не найден")

    # Здесь должна быть ваша таблица с данными по регионам.
    # Пока заглушка. Вы сможете заменить её на реальную таблицу,
    # как только у вас появятся данные по национальному составу регионов.
    # result = await db.execute(...)

    # ---- ВРЕМЕННАЯ ЗАГЛУШКА: демонстрационные данные ----
    regions = await db.execute(select(Region.name))
    demo_data = {}
    for (region_name,) in regions:
        if people_obj.name == "Русские":
            demo_data[region_name] = 70.0 + (hash(region_name) % 25) / 100
        elif people_obj.name == "Татары":
            demo_data[region_name] = 3.0 + (hash(region_name) % 5) / 100
        else:
            demo_data[region_name] = 1.0 + (hash(region_name) % 10) / 100
    return demo_data
    # ---- КОНЕЦ ВРЕМЕННОЙ ЗАГЛУШКИ ----