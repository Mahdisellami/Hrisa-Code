from typing import Optional
import typer
from models import Task
from db import init_db
from sqlalchemy.orm import Session
from datetime import datetime

def add_task(title: str, description: Optional[str] = None, priority: int = 1, status: str = 'pending', tags: Optional[str] = None, due_date: Optional[str] = None):
    if not title:
        raise ValueError('Title cannot be empty')
    engine, SessionLocal = init_db()
    session = SessionLocal()
    task = Task(
        title=title,
        description=description or '',
        priority=priority,
        status=status,
        tags=tags.split(',') if tags else [],
        created_at=datetime.now(),
        updated_at=datetime.now(),
        due_date=datetime.fromisoformat(due_date) if due_date else None
    )
    session.add(task)
    session.commit()
    return task

app = typer.Typer()

@app.command()
def add(title: str, description: Optional[str] = typer.Option(None, help='Description of the task'), priority: int = typer.Option(1, help='Priority level of the task (default: 1)'), status: str = typer.Option('pending', help='Status of the task (default: pending)'), tags: Optional[str] = typer.Option(None, help='Comma-separated list of tags for the task'), due_date: Optional[str] = typer.Option(None, help='Due date in ISO format (YYYY-MM-DDTHH:MM:SS)')):
    try:
        task = add_task(title, description, priority, status, tags, due_date)
        print(f'Task added with ID: {task.id}')
    except ValueError as e:
        print(e)

if __name__ == '__main__':
    app()