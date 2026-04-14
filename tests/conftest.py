import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport  # важно!
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select

from main import app
from database import Base, get_db
from models import Year, People, PopulationStat

# Используем SQLite в памяти – не будет проблем с файлами
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine_test = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(engine_test, expire_on_commit=False)

async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestingSessionLocal() as session:
        yield session
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine_test.dispose()

@pytest_asyncio.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)  # правильный способ
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

@pytest_asyncio.fixture
async def fill_test_data(db_session: AsyncSession):
    year1 = Year(year=2000, total_population=145.0)
    db_session.add(year1)
    await db_session.flush()
    people1 = People(name="Русские")
    db_session.add(people1)
    people2 = People(name="Татары")
    db_session.add(people2)
    await db_session.flush()
    stat1 = PopulationStat(year_id=year1.id, people_id=people1.id, population=110.0, percentage=75.0)
    stat2 = PopulationStat(year_id=year1.id, people_id=people2.id, population=5.0, percentage=3.5)
    db_session.add_all([stat1, stat2])
    year2 = Year(year=2010, total_population=142.9)
    db_session.add(year2)
    await db_session.flush()
    stat3 = PopulationStat(year_id=year2.id, people_id=people1.id, population=111.0, percentage=77.7)
    stat4 = PopulationStat(year_id=year2.id, people_id=people2.id, population=5.3, percentage=3.7)
    db_session.add_all([stat3, stat4])
    await db_session.commit()