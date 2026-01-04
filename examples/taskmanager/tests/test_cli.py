"""Tests for CLI task manager commands."""
import pytest
from typer.testing import CliRunner
from task_manager.cli import app
from task_manager.models import Task, init_db, get_session

runner = CliRunner()


@pytest.fixture(autouse=True)
def setup_db():
    """Initialize test database before each test."""
    init_db()
    yield
    # Cleanup
    session = get_session()
    session.query(Task).delete()
    session.commit()
    session.close()


def test_add_task():
    """Test adding a new task."""
    result = runner.invoke(app, ["add", "Test Task", "-d", "Test description", "-p", "high"])
    assert result.exit_code == 0
    assert "Task added successfully" in result.output


def test_list_tasks():
    """Test listing tasks."""
    runner.invoke(app, ["add", "Task 1"])
    runner.invoke(app, ["add", "Task 2"])
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "Task 1" in result.output
    assert "Task 2" in result.output


def test_show_task():
    """Test showing task details."""
    runner.invoke(app, ["add", "Show Test"])
    result = runner.invoke(app, ["show", "1"])
    assert result.exit_code == 0
    assert "Show Test" in result.output


def test_complete_task():
    """Test marking task as complete."""
    runner.invoke(app, ["add", "Complete Me"])
    result = runner.invoke(app, ["complete", "1"])
    assert result.exit_code == 0
    assert "completed" in result.output.lower()


def test_delete_task():
    """Test deleting a task."""
    runner.invoke(app, ["add", "Delete Me"])
    result = runner.invoke(app, ["delete", "1", "--yes"])
    assert result.exit_code == 0
    assert "deleted" in result.output.lower()
