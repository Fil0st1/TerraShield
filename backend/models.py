from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

from database import Base
import datetime

class SensorData(Base):
    __tablename__ = 'sensor_data'

    id = Column(Integer, primary_key=True)
    moisture = Column(Float)
    vibration = Column(Float)
    tilt = Column(Float, default=0)   # <-- Add this line
    battery = Column(Float)
    latitude = Column(Float)
    longitude = Column(Float)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class Alerts(Base):
    __tablename__ = 'alerts'
    id = Column(Integer, primary_key=True)
    message = Column(Float)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class UserPref(Base):
    __tablename__ = "user_prefs"
    id = Column(Integer, primary_key=True)
    phone = Column(String, unique=True, index=True)   # store E.164 like +9198xxxx
    language = Column(String, default="english")      # 'english'|'hindi'|'marathi'
    subscribed = Column(Boolean, default=True)
