# Defines the SQLite data model using SQLAlchemy
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime

Base = declarative_base()

engine = create_engine('sqlite:///tasks.db')
Session = sessionmaker(bind=engine)

session = Session()

class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    priority = Column(Integer, default=1)
    status = Column(Boolean, default=False)
    tags = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.datetime.utcnow)
    due_date = Column(DateTime)
    completed_at = Column(DateTime)

Base.metadata.create_all(engine)