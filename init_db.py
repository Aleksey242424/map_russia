import asyncio
from sqlalchemy import select
from database import AsyncSessionLocal
from models import Year, People, PopulationStat
from logger import logger

DATA = { ... }  # ваш словарь (такой же как ранее)

async def populate():
    logger.info("Начало заполнения базы данных")
    async with AsyncSessionLocal() as session:
        async with session.begin():
            for year_num, year_data in DATA.items():
                logger.debug(f"Обработка года {year_num}")
                # Проверка, существует ли год
                result = await session.execute(select(Year).where(Year.year == year_num))
                if result.scalar_one_or_none():
                    logger.warning(f"Год {year_num} уже существует, пропускаем")
                    continue
                year_obj = Year(year=year_num, total_population=year_data["total_population"])
                session.add(year_obj)
                await session.flush()
                for p in year_data["peoples"]:
                    result_people = await session.execute(select(People).where(People.name == p["name"]))
                    people = result_people.scalar_one_or_none()
                    if not people:
                        people = People(name=p["name"])
                        session.add(people)
                        await session.flush()
                    stat = PopulationStat(
                        year_id=year_obj.id,
                        people_id=people.id,
                        population=p["population"],
                        percentage=p["percentage"]
                    )
                    session.add(stat)
                logger.info(f"Год {year_num} загружен: {len(year_data['peoples'])} народов")
    logger.success("База данных успешно заполнена")

if __name__ == "__main__":
    asyncio.run(populate())