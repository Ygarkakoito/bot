from sqlalchemy import Column, Integer, String, create_engine, ForeignKey, Text, Float,DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


db_url = 'postgresql://bot_market:3jv6ETm2z2fSM9Mo7Pfh@80.89.239.246:5432/bot_market'
engine = create_engine(db_url)
from sqlalchemy.orm import sessionmaker

Session = sessionmaker(bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(255))
    name = Column(String)
    surname = Column(String)
    profile_type_legal = Column(String(255))
    profile_type_individual = Column(String(255))
    city_id = Column(String(255))
    country = Column(String)
    photo_id = Column(String(255))
    contact = Column(String(255))
    updated_profile_type= Column(String(255))
    city_name= Column(String(255))


class Ad(Base):
    __tablename__ = 'ads'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    title = Column(String)
    photo_url = Column(String)
    description = Column(String)
    date = Column(DateTime)
    cost = Column(String)
    location = Column(String)
    category = Column(String)  # Add this line to define the category column

class Country(Base):
    __tablename__ = 'countries'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True)


class City(Base):
    __tablename__ = 'City'

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)

class Movie(Base):
    __tablename__ = 'Movie'

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    img = Column(Text(), nullable=False)
    genre = Column(String(50), nullable=False)
    about = Column(Text(), nullable=False)
    country = Column(String(50), nullable=False)
    time = Column(String(50), nullable=False)
    city_id = Column(Integer, ForeignKey("City.id"))


class Activity(Base):
    __tablename__ = 'activities'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)



class Location(Base):
    __tablename__ = 'locations'
    id = Column(Integer, primary_key=True)
    country = Column(String(255))
    city = Column(String(255))



session = Session()
session.close()
Base.metadata.create_all(bind=engine)

