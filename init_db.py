import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Year, People, PopulationStat

# Подключение к PostgreSQL (измените параметры на свои)
DATABASE_URL = "postgresql+psycopg2://postgres:123@localhost:5432/map_russia"
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine)

# Создание таблиц
Base.metadata.drop_all(engine)   # осторожно, удалит существующие
Base.metadata.create_all(engine)

session = SessionLocal()

# Исходные данные из вашего словаря
DATA = {
    1897: {
        "total_population": 125.6,
        "peoples": [
            {"name": "Русские", "population": 55.7, "percentage": 44.3},
            {"name": "Украинцы", "population": 22.4, "percentage": 17.8},
            {"name": "Белорусы", "population": 5.9, "percentage": 4.7},
            {"name": "Поляки", "population": 7.9, "percentage": 6.3},
            {"name": "Евреи", "population": 5.2, "percentage": 4.1},
            {"name": "Татары", "population": 3.7, "percentage": 2.9},
            {"name": "Немцы", "population": 1.8, "percentage": 1.4},
        ]
    },
    1926: {
        "total_population": 147.0,
        "peoples": [
            {"name": "Русские", "population": 77.7, "percentage": 52.9},
            {"name": "Украинцы", "population": 31.2, "percentage": 21.2},
            {"name": "Белорусы", "population": 4.7, "percentage": 3.2},
            {"name": "Татары", "population": 3.8, "percentage": 2.6},
            {"name": "Евреи", "population": 2.7, "percentage": 1.8},
            {"name": "Немцы", "population": 1.2, "percentage": 0.8},
        ]
    },
    1959: {
        "total_population": 208.8,
        "peoples": [
            {"name": "Русские", "population": 114.1, "percentage": 54.6},
            {"name": "Украинцы", "population": 37.3, "percentage": 17.8},
            {"name": "Белорусы", "population": 7.9, "percentage": 3.8},
            {"name": "Татары", "population": 4.9, "percentage": 2.3},
            {"name": "Евреи", "population": 2.3, "percentage": 1.1},
            {"name": "Немцы", "population": 1.6, "percentage": 0.8},
        ]
    },
    1989: {
        "total_population": 286.7,
        "peoples": [
            {"name": "Русские", "population": 145.2, "percentage": 50.6},
            {"name": "Украинцы", "population": 44.2, "percentage": 15.4},
            {"name": "Белорусы", "population": 10.0, "percentage": 3.5},
            {"name": "Татары", "population": 6.6, "percentage": 2.3},
            {"name": "Немцы", "population": 2.0, "percentage": 0.7},
            {"name": "Чеченцы", "population": 1.3, "percentage": 0.5},
        ]
    },
    2010: {
        "total_population": 142.9,
        "peoples": [
            {"name": "Русские", "population": 111.0, "percentage": 77.7},
            {"name": "Татары", "population": 5.3, "percentage": 3.7},
            {"name": "Украинцы", "population": 1.9, "percentage": 1.3},
            {"name": "Башкиры", "population": 1.6, "percentage": 1.1},
            {"name": "Чеченцы", "population": 1.4, "percentage": 1.0},
            {"name": "Армяне", "population": 1.2, "percentage": 0.8},
        ]
    },
    2015: {
        "total_population": 146.3,
        "peoples": [
            {"name": "Русские", "population": 112.2, "percentage": 76.7},
            {"name": "Татары", "population": 5.4, "percentage": 3.7},
            {"name": "Украинцы", "population": 1.5, "percentage": 1.0},
            {"name": "Чеченцы", "population": 1.5, "percentage": 1.0},
            {"name": "Башкиры", "population": 1.6, "percentage": 1.1},
            {"name": "Армяне", "population": 1.2, "percentage": 0.8},
            {"name": "Аварцы", "population": 1.0, "percentage": 0.7},
        ]
    },
    2020: {
        "total_population": 146.2,
        "peoples": [
            {"name": "Русские", "population": 110.3, "percentage": 75.5},
            {"name": "Татары", "population": 5.3, "percentage": 3.6},
            {"name": "Чеченцы", "population": 1.6, "percentage": 1.1},
            {"name": "Башкиры", "population": 1.5, "percentage": 1.0},
            {"name": "Украинцы", "population": 1.2, "percentage": 0.8},
            {"name": "Армяне", "population": 1.1, "percentage": 0.75},
            {"name": "Аварцы", "population": 1.0, "percentage": 0.7},
        ]
    },
    2025: {
        "total_population": 145.8,
        "peoples": [
            {"name": "Русские", "population": 109.5, "percentage": 75.1},
            {"name": "Татары", "population": 5.2, "percentage": 3.6},
            {"name": "Чеченцы", "population": 1.8, "percentage": 1.2},
            {"name": "Башкиры", "population": 1.5, "percentage": 1.0},
            {"name": "Армяне", "population": 1.1, "percentage": 0.75},
            {"name": "Аварцы", "population": 1.1, "percentage": 0.75},
            {"name": "Украинцы", "population": 0.9, "percentage": 0.6},
        ]
    }
}

def populate_database():
    for year_num, year_data in DATA.items():
        # Создаём запись года
        year_obj = Year(year=year_num, total_population=year_data["total_population"])
        session.add(year_obj)
        session.flush()  # чтобы получить year_obj.id

        # Добавляем народы и статистику
        for people_info in year_data["peoples"]:
            name = people_info["name"]
            # Ищем или создаём народ
            people_obj = session.query(People).filter_by(name=name).first()
            if not people_obj:
                people_obj = People(name=name)
                session.add(people_obj)
                session.flush()

            stat = PopulationStat(
                year_id=year_obj.id,
                people_id=people_obj.id,
                population=people_info["population"],
                percentage=people_info["percentage"]
            )
            session.add(stat)

    session.commit()
    print("Данные успешно загружены")

if __name__ == "__main__":
    populate_database()