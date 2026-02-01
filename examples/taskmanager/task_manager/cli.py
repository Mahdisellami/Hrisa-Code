from datetime import datetime
from typing import Optional
import typer
from sqlalchemy.orm import Session
from task_manager.models import Task, Base
def get_session():
    from task_manager.db import engine
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    return Session()

def add_task(title: str, description: Optional[str] = typer.Option(None, help='Description of the task'), priority: int = typer.Option(1, help='Priority level of the task', min=1), status: str = typer.Option('pending', help='Status of the task'), tags: Optional[str] = typer.Option(None, help='Comma-separated tags for the task')):
    if not title:
        raise ValueError('Title is required')

    session = get_session()
    task = Task(
        title=title,
        description=description,
        priority=priority,
        status=status,
        tags=tags.split(',') if tags else [],
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    session.add(task)
    session.commit()
    typer.echo(f'Task added with ID: {task.id}')

if __name__ == '__main__':
    app = typer.Typer()
    app.command()(add_task)
    app()