"""Task Manager Data Models

This module defines the SQLAlchemy models and database setup for the task manager.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, Text, Enum, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session as SessionType

# Create base class for models
Base = declarative_base()

# Database setup
DATABASE_URL = "sqlite:///tasks.db"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session() -> SessionType:
    """Get a database session.

    Returns:
        Database session instance
    """
    return SessionLocal()


def init_db() -> None:
    """Initialize the database by creating all tables."""
    Base.metadata.create_all(bind=engine)


class Task(Base):
    """Task model representing a single task in the task manager.

    Attributes:
        id: Primary key
        title: Task title (required)
        description: Detailed task description
        priority: Task priority (low, medium, high)
        status: Task status (pending, in_progress, completed)
        tags: Comma-separated tags
        created_at: Timestamp when task was created
        updated_at: Timestamp when task was last updated
        due_date: Optional due date for the task
        completed_at: Timestamp when task was completed
    """

    __tablename__ = 'tasks'

    id: int = Column(Integer, primary_key=True, index=True)
    title: str = Column(String(255), nullable=False)
    description: str = Column(Text, default='')
    priority: str = Column(Enum('low', 'medium', 'high', name='priority_enum'), default='medium')
    status: str = Column(Enum('pending', 'in_progress', 'completed', name='status_enum'), default='pending')
    tags: str = Column(String(255), default='')
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    updated_at: datetime = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    due_date: Optional[datetime] = Column(DateTime, nullable=True)
    completed_at: Optional[datetime] = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        """String representation of Task."""
        return f'<Task id={self.id}, title="{self.title}", status={self.status}>'

    def to_dict(self) -> dict:
        """Convert task to dictionary.

        Returns:
            Dictionary representation of the task
        """
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'priority': self.priority,
            'status': self.status,
            'tags': self.tags.split(',') if self.tags else [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }
