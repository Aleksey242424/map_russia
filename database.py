from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi import Depends

# Замените на свои параметры подключения
DATABASE_URL = "postgresql+psycopg2://postgres:123@localhost:5432/map_russia"

engine = create_engine(
    DATABASE_URL,
    echo=True,  # для отладки, в продакшене выключить
    pool_size=5,  # оптимизация пула соединений
    max_overflow=10
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency для получения сессии в эндпоинтах
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()