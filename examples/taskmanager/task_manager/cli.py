"""Task Manager CLI

A command-line interface for managing tasks with CRUD operations,
search, filtering, and export capabilities.
"""

import json
import csv
from datetime import datetime
from typing import Optional, List

import typer
from rich.console import Console
from rich.table import Table

from models import Task, get_session, init_db

# Initialize Typer app and Rich console
app = typer.Typer(help="CLI Task Manager - Manage your tasks efficiently")
console = Console()


@app.command()
def add(
    title: str = typer.Argument(..., help="Task title"),
    description: str = typer.Option("", "--description", "-d", help="Task description"),
    priority: str = typer.Option("medium", "--priority", "-p", help="Priority: low, medium, high"),
    status: str = typer.Option("pending", "--status", "-s", help="Status: pending, in_progress, completed"),
    tags: str = typer.Option("", "--tags", "-t", help="Comma-separated tags"),
    due_date: Optional[str] = typer.Option(None, "--due", help="Due date (YYYY-MM-DD)"),
) -> None:
    """Add a new task."""
    session = get_session()

    try:
        task = Task(
            title=title,
            description=description,
            priority=priority,
            status=status,
            tags=tags,
            due_date=datetime.strptime(due_date, "%Y-%m-%d") if due_date else None
        )

        session.add(task)
        session.commit()
        session.refresh(task)

        console.print(f"[green]✓ Task added successfully with ID {task.id}[/green]")

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        session.rollback()
    finally:
        session.close()


@app.command()
def list(
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
    priority: Optional[str] = typer.Option(None, "--priority", "-p", help="Filter by priority"),
    tags: Optional[str] = typer.Option(None, "--tags", "-t", help="Filter by tags (comma-separated)"),
) -> None:
    """List all tasks with optional filtering."""
    session = get_session()

    try:
        query = session.query(Task)

        if status:
            query = query.filter(Task.status == status)
        if priority:
            query = query.filter(Task.priority == priority)
        if tags:
            # Simple tag filtering (contains any of the specified tags)
            tag_list = [t.strip() for t in tags.split(',')]
            for tag in tag_list:
                query = query.filter(Task.tags.contains(tag))

        tasks = query.order_by(Task.created_at.desc()).all()

        if not tasks:
            console.print("[yellow]No tasks found.[/yellow]")
            return

        # Create rich table
        table = Table(title=f"Tasks ({len(tasks)} found)")
        table.add_column("ID", style="cyan", width=6)
        table.add_column("Title", style="white")
        table.add_column("Status", style="yellow")
        table.add_column("Priority", style="magenta")
        table.add_column("Due Date", style="blue")

        for task in tasks:
            due = task.due_date.strftime("%Y-%m-%d") if task.due_date else "-"
            table.add_row(
                str(task.id),
                task.title[:40],
                task.status,
                task.priority,
                due
            )

        console.print(table)

    finally:
        session.close()


@app.command()
def show(task_id: int = typer.Argument(..., help="Task ID")) -> None:
    """Show detailed information about a specific task."""
    session = get_session()

    try:
        task = session.query(Task).filter(Task.id == task_id).first()

        if not task:
            console.print(f"[red]Task with ID {task_id} not found.[/red]")
            return

        console.print("\n[bold cyan]Task Details[/bold cyan]")
        console.print(f"[bold]ID:[/bold] {task.id}")
        console.print(f"[bold]Title:[/bold] {task.title}")
        console.print(f"[bold]Description:[/bold] {task.description or '(none)'}")
        console.print(f"[bold]Status:[/bold] {task.status}")
        console.print(f"[bold]Priority:[/bold] {task.priority}")
        console.print(f"[bold]Tags:[/bold] {task.tags or '(none)'}")
        console.print(f"[bold]Created:[/bold] {task.created_at}")
        console.print(f"[bold]Updated:[/bold] {task.updated_at}")
        console.print(f"[bold]Due Date:[/bold] {task.due_date or '(none)'}")
        console.print(f"[bold]Completed:[/bold] {task.completed_at or '(none)'}\n")

    finally:
        session.close()


@app.command()
def edit(
    task_id: int = typer.Argument(..., help="Task ID"),
    title: Optional[str] = typer.Option(None, "--title", help="New title"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="New description"),
    priority: Optional[str] = typer.Option(None, "--priority", "-p", help="New priority"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="New status"),
    tags: Optional[str] = typer.Option(None, "--tags", "-t", help="New tags"),
    due_date: Optional[str] = typer.Option(None, "--due", help="New due date (YYYY-MM-DD)"),
) -> None:
    """Edit an existing task."""
    session = get_session()

    try:
        task = session.query(Task).filter(Task.id == task_id).first()

        if not task:
            console.print(f"[red]Task with ID {task_id} not found.[/red]")
            return

        if title is not None:
            task.title = title
        if description is not None:
            task.description = description
        if priority is not None:
            task.priority = priority
        if status is not None:
            task.status = status
            if status == "completed" and not task.completed_at:
                task.completed_at = datetime.utcnow()
        if tags is not None:
            task.tags = tags
        if due_date is not None:
            task.due_date = datetime.strptime(due_date, "%Y-%m-%d")

        task.updated_at = datetime.utcnow()
        session.commit()

        console.print(f"[green]✓ Task {task_id} updated successfully.[/green]")

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        session.rollback()
    finally:
        session.close()


@app.command()
def complete(task_id: int = typer.Argument(..., help="Task ID")) -> None:
    """Mark a task as completed."""
    session = get_session()

    try:
        task = session.query(Task).filter(Task.id == task_id).first()

        if not task:
            console.print(f"[red]Task with ID {task_id} not found.[/red]")
            return

        task.status = "completed"
        task.completed_at = datetime.utcnow()
        task.updated_at = datetime.utcnow()
        session.commit()

        console.print(f"[green]✓ Task {task_id} marked as completed.[/green]")

    finally:
        session.close()


@app.command()
def delete(
    task_id: int = typer.Argument(..., help="Task ID"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """Delete a task."""
    session = get_session()

    try:
        task = session.query(Task).filter(Task.id == task_id).first()

        if not task:
            console.print(f"[red]Task with ID {task_id} not found.[/red]")
            return

        if not force:
            confirm = typer.confirm(f"Delete task '{task.title}'?")
            if not confirm:
                console.print("[yellow]Deletion cancelled.[/yellow]")
                return

        session.delete(task)
        session.commit()

        console.print(f"[green]✓ Task {task_id} deleted successfully.[/green]")

    finally:
        session.close()


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    field: str = typer.Option("title", "--field", "-f", help="Field to search: title, description, tags"),
) -> None:
    """Search tasks by text."""
    session = get_session()

    try:
        if field == "title":
            tasks = session.query(Task).filter(Task.title.contains(query)).all()
        elif field == "description":
            tasks = session.query(Task).filter(Task.description.contains(query)).all()
        elif field == "tags":
            tasks = session.query(Task).filter(Task.tags.contains(query)).all()
        else:
            console.print(f"[red]Invalid field: {field}[/red]")
            return

        if not tasks:
            console.print(f"[yellow]No tasks found matching '{query}'.[/yellow]")
            return

        console.print(f"\n[bold]Found {len(tasks)} task(s):[/bold]\n")
        for task in tasks:
            console.print(f"[cyan]#{task.id}[/cyan] {task.title} [{task.status}]")

    finally:
        session.close()


@app.command()
def export(
    format: str = typer.Argument(..., help="Export format: json, csv, markdown"),
    output: str = typer.Option("tasks", "--output", "-o", help="Output filename (without extension)"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
) -> None:
    """Export tasks to various formats."""
    session = get_session()

    try:
        query = session.query(Task)
        if status:
            query = query.filter(Task.status == status)

        tasks = query.order_by(Task.created_at.desc()).all()

        if not tasks:
            console.print("[yellow]No tasks to export.[/yellow]")
            return

        if format == "json":
            filename = f"{output}.json"
            with open(filename, 'w') as f:
                json.dump([task.to_dict() for task in tasks], f, indent=2)
            console.print(f"[green]✓ Exported {len(tasks)} tasks to {filename}[/green]")

        elif format == "csv":
            filename = f"{output}.csv"
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['ID', 'Title', 'Description', 'Priority', 'Status', 'Tags', 'Created', 'Due Date'])
                for task in tasks:
                    writer.writerow([
                        task.id,
                        task.title,
                        task.description,
                        task.priority,
                        task.status,
                        task.tags,
                        task.created_at,
                        task.due_date or ''
                    ])
            console.print(f"[green]✓ Exported {len(tasks)} tasks to {filename}[/green]")

        elif format == "markdown":
            filename = f"{output}.md"
            with open(filename, 'w') as f:
                f.write("# Task List\n\n")
                for task in tasks:
                    f.write(f"## #{task.id}: {task.title}\n\n")
                    f.write(f"- **Status:** {task.status}\n")
                    f.write(f"- **Priority:** {task.priority}\n")
                    if task.description:
                        f.write(f"- **Description:** {task.description}\n")
                    if task.tags:
                        f.write(f"- **Tags:** {task.tags}\n")
                    if task.due_date:
                        f.write(f"- **Due:** {task.due_date.strftime('%Y-%m-%d')}\n")
                    f.write("\n")
            console.print(f"[green]✓ Exported {len(tasks)} tasks to {filename}[/green]")

        else:
            console.print(f"[red]Invalid format: {format}. Use: json, csv, or markdown[/red]")

    finally:
        session.close()


@app.command()
def init() -> None:
    """Initialize the database."""
    init_db()
    console.print("[green]✓ Database initialized successfully.[/green]")


if __name__ == "__main__":
    # Initialize database on first run
    init_db()
    app()
