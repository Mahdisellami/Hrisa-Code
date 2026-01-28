from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, default='')
    priority = Column(Integer, default=1)
    status = Column(String(50), default='pending')
    tags = Column(ARRAY(String(50)), default=[])
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    due_date = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)