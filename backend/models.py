from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(Enum('Employee', 'Manager'), nullable=False)
    
    logs = relationship("EmotionLog", back_populates="user", cascade="all, delete")

class EmotionLog(Base):
    __tablename__ = "emotion_logs"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    emotion = Column(String(50))
    fatigue = Column(String(50), default='Neutral')
    pulse_rate = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)
    work_duration = Column(Integer, default=0)
    status = Column(Enum('Active', 'Inactive'), default='Active')

    user = relationship("User", back_populates="logs")
