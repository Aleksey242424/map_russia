from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from database import get_db, engine
from models import Base, Year, People, PopulationStat

# Создаём таблицы при старте (если ещё не созданы)
# В реальном проекте лучше использовать Alembic, но для простоты:
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/api/years")
async def get_years(db: Session = Depends(get_db)):
    """Возвращает список доступных годов (отсортированный)"""
    years = db.query(Year.year).order_by(Year.year).all()
    return {"years": [y[0] for y in years]}

@app.get("/api/data/{year}")
async def get_data(year: int, db: Session = Depends(get_db)):
    """
    Возвращает демографические данные для указанного года:
    - total_population (млн)
    - список народов с population (млн) и percentage (%)
    """
    # Находим год в БД
    year_record = db.query(Year).filter(Year.year == year).first()
    if not year_record:
        raise HTTPException(status_code=404, detail=f"Данные за {year} год отсутствуют")
    
    # Загружаем статистику с жадной подгрузкой (joinedload) для оптимизации
    from sqlalchemy.orm import joinedload
    stats = db.query(PopulationStat).filter(PopulationStat.year_id == year_record.id).options(
        joinedload(PopulationStat.people)
    ).all()
    
    peoples_data = []
    for stat in stats:
        peoples_data.append({
            "name": stat.people.name,
            "population": float(stat.population),
            "percentage": float(stat.percentage)
        })
    
    # Сортируем по убыванию численности
    peoples_data.sort(key=lambda x: x["population"], reverse=True)
    
    return {
        "total_population": float(year_record.total_population),
        "peoples": peoples_data
    }

@app.get("/")
async def root():
    return FileResponse("static/index.html")