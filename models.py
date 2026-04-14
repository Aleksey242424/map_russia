from sqlalchemy import Column, Integer, Numeric, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base  
from sqlalchemy import Column, Integer, String
from geoalchemy2 import Geometry
from database import Base

class Region(Base):
    __tablename__ = "regions"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)  # Название региона
    geometry = Column(Geometry("MULTIPOLYGON", srid=4326))  # Геометрия границ

class Year(Base):
    __tablename__ = 'years'
    id = Column(Integer, primary_key=True)
    year = Column(Integer, unique=True, nullable=False, index=True)
    total_population = Column(Numeric(10, 2), nullable=False)

    stats = relationship("PopulationStat", back_populates="year", cascade="all, delete-orphan")

class People(Base):
    __tablename__ = 'peoples'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False, index=True)

    stats = relationship("PopulationStat", back_populates="people", cascade="all, delete-orphan")

class PopulationStat(Base):
    __tablename__ = 'population_stats'
    id = Column(Integer, primary_key=True)
    year_id = Column(Integer, ForeignKey('years.id', ondelete='CASCADE'), nullable=False)
    people_id = Column(Integer, ForeignKey('peoples.id', ondelete='CASCADE'), nullable=False)
    population = Column(Numeric(10, 2), nullable=False)
    percentage = Column(Numeric(5, 2), nullable=False)

    __table_args__ = (UniqueConstraint('year_id', 'people_id', name='uq_year_people'),)

    year = relationship("Year", back_populates="stats")
    people = relationship("People", back_populates="stats")