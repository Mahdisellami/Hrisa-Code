from typing import Optional
import typer
from datetime import datetime
from sqlalchemy.orm import Session
from .models import Task, Base, engine
from .database import get_session

app = typer.Typer()

def create_tables():
    Base.metadata.create_all(bind=engine)

create_tables()

@app.command()
def add(title: str,
        description: Optional[str] = None,
        priority: int = 1,
        status: str = 'pending',
        tags: Optional[str] = None,
        due_date: Optional[str] = None):
    """
    Add a new task to the task manager.

    :param title: The title of the task (required).
    :param description: A detailed description of the task (optional).
    :param priority: The priority level of the task (default is 1).
    :param status: The status of the task (e.g., 'pending', 'in_progress', 'completed') (default is 'pending').
    :param tags: A comma-separated list of tags for the task (optional).
    :param due_date: The due date of the task in YYYY-MM-DD format (optional).
    """
    if not title:
        typer.echo('Title cannot be empty.')
        return

    session: Session = get_session()
    try:
        new_task = Task(
            title=title,
            description=description,
            priority=priority,
            status=status,
            tags=tags.split(',') if tags else [],
            created_at=datetime.now(),
            updated_at=datetime.now(),
            due_date=datetime.strptime(due_date, '%Y-%m-%d') if due_date else None
        )
        session.add(new_task)
        session.commit()
        typer.echo(f'Task added with ID: {new_task.id}')
    except Exception as e:
        session.rollback()
        typer.echo(f'Error adding task: {str(e)}')
    finally:
        session.close()

if __name__ == '__main__':
    app()