from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator
from logger import logger

DATABASE_URL = "postgresql+asyncpg://postgres:123@localhost:5432/map_russia"

logger.info(f"Создание асинхронного движка PostgreSQL: {DATABASE_URL.split('@')[1]}")  # без пароля

engine = create_async_engine(
    DATABASE_URL,
    echo=False,          # отключаем echo, чтобы не дублировать логи (loguru уже всё пишет)
    pool_size=5,
    max_overflow=10
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session