from typing import Optional
from datetime import datetime
import typer
from sqlalchemy.exc import IntegrityError
from task_model import Task, Session

def add_task(title: str, description: Optional[str] = None, priority: Optional[int] = 1, status: Optional[str] = 'pending', tags: Optional[str] = '', due_date: Optional[datetime] = None):
    if not title:
        raise ValueError('Title is required')
    session = Session()
    task = Task(
        title=title,
        description=description,
        priority=priority,
        status=status,
        tags=tags,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        due_date=due_date
    )
    try:
        session.add(task)
        session.commit()
        typer.echo(f'Task added successfully with ID: {task.id}')
    except IntegrityError as e:
        session.rollback()
        raise ValueError('Failed to add task due to integrity error') from e
    finally:
        session.close()

app = typer.Typer()

@app.command()
def add(title: str, description: Optional[str] = typer.Option(None, help='Description of the task'),
         priority: Optional[int] = typer.Option(1, help='Priority level of the task (default: 1)'),
         status: Optional[str] = typer.Option('pending', help='Status of the task (default: pending)'),
         tags: Optional[str] = typer.Option('', help='Tags associated with the task'),
         due_date: Optional[datetime] = typer.Option(None, help='Due date for the task')):
    add_task(title=title, description=description, priority=priority, status=status, tags=tags, due_date=due_date)

if __name__ == '__main__':
    app()