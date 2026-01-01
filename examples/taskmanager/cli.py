# Contains Typer commands for user interaction
import typer
from models import Task, Session

app = typer.Typer()

@app.command()
def add(title: str, description: str, priority: int):
    # Add a new task
    pass

@app.command()
def list():
    # List all tasks
    pass

@app.command()
def show(task_id: int):
    # Show details of a specific task
    pass

@app.command()
def edit(task_id: int, title: str = None, description: str = None, priority: int = None):
    # Edit an existing task
    pass

@app.command()
def complete(task_id: int):
    # Mark a task as completed
    pass

@app.command()
def delete(task_id: int):
    # Delete a task
    pass

if __name__ == "__main__":
    app()