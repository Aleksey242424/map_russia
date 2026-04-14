from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from models import Year, People, PopulationStat
from database import get_db
from main import app
import pytest

pytestmark = pytest.mark.asyncio

class TestYearsEndpoint:
    async def test_get_years_success(self, client: AsyncClient, fill_test_data):
        response = await client.get("/api/years")
        assert response.status_code == 200
        data = response.json()
        assert "years" in data
        assert data["years"] == [2000, 2010]

    async def test_get_years_empty_db(self, client: AsyncClient, db_session):
        response = await client.get("/api/years")
        assert response.status_code == 200
        assert response.json() == {"years": []}

class TestDataEndpoint:
    async def test_get_data_existing_year(self, client: AsyncClient, fill_test_data):
        response = await client.get("/api/data/2000")
        assert response.status_code == 200
        data = response.json()
        assert data["total_population"] == 145.0
        assert len(data["peoples"]) == 2
        assert data["peoples"][0]["name"] == "Русские"
        assert data["peoples"][0]["population"] == 110.0
        assert data["peoples"][0]["percentage"] == 75.0
        assert data["peoples"][1]["name"] == "Татары"

    async def test_get_data_nonexistent_year(self, client: AsyncClient, fill_test_data):
        response = await client.get("/api/data/1990")
        assert response.status_code == 404
        assert "Данные за 1990 год отсутствуют" in response.json()["detail"]

    async def test_data_correct_float_conversion(self, client: AsyncClient, fill_test_data):
        response = await client.get("/api/data/2010")
        data = response.json()
        assert isinstance(data["total_population"], float)
        assert isinstance(data["peoples"][0]["population"], float)
        assert isinstance(data["peoples"][0]["percentage"], float)

    async def test_data_sorted_by_population_desc(self, client: AsyncClient, fill_test_data):
        response = await client.get("/api/data/2000")
        peoples = response.json()["peoples"]
        populations = [p["population"] for p in peoples]
        assert populations == sorted(populations, reverse=True)

class TestDatabaseIntegration:
    async def test_database_structure(self, db_session):
        year = Year(year=2025, total_population=145.8)
        db_session.add(year)
        await db_session.commit()
        result = await db_session.execute(select(Year).where(Year.year == 2025))
        assert result.scalar_one() is not None

    async def test_relationship_loading(self, fill_test_data, db_session):
        # Убедимся, что данные есть
        year = await db_session.execute(select(Year).where(Year.year == 2000))
        year_obj = year.scalar_one()
        stats = await db_session.execute(
            select(PopulationStat)
            .where(PopulationStat.year_id == year_obj.id)
            .options(selectinload(PopulationStat.people))
        )
        stats_list = stats.scalars().all()
        assert len(stats_list) == 2
        for stat in stats_list:
            assert stat.people is not None
            assert stat.people.name in ("Русские", "Татары")

class TestErrorHandling:
    async def test_invalid_year_format(self, client: AsyncClient):
        response = await client.get("/api/data/abc")
        assert response.status_code == 422

    async def test_database_error_500(self, client: AsyncClient):
        async def broken_get_db():
            class BrokenSession:
                async def execute(self, *args, **kwargs):
                    raise Exception("Query failed")
                async def __aenter__(self):
                    return self
                async def __aexit__(self, *args):
                    pass
            yield BrokenSession()
        app.dependency_overrides[get_db] = broken_get_db
        response = await client.get("/api/years")
        assert response.status_code == 500
        assert "Внутренняя ошибка сервера" in response.json()["detail"]
        app.dependency_overrides.pop(get_db, None)