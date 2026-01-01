import subprocess
import pytest
from task_manager.cli import app

def test_add_task():
    result = subprocess.run(['python', '-m', 'task_manager', 'add', '--title', 'Test Task'], capture_output=True, text=True)
    assert result.returncode == 0
    assert 'Task added successfully' in result.stdout

def test_list_tasks():
    result = subprocess.run(['python', '-m', 'task_manager', 'list'], capture_output=True, text=True)
    assert result.returncode == 0
    assert 'Test Task' in result.stdout

def test_show_task():
    result = subprocess.run(['python', '-m', 'task_manager', 'show', '--id', '1'], capture_output=True, text=True)
    assert result.returncode == 0
    assert 'Title: Test Task' in result.stdout

def test_edit_task():
    result = subprocess.run(['python', '-m', 'task_manager', 'edit', '--id', '1', '--title', 'Updated Task'], capture_output=True, text=True)
    assert result.returncode == 0
    assert 'Task updated successfully' in result.stdout

def test_complete_task():
    result = subprocess.run(['python', '-m', 'task_manager', 'complete', '--id', '1'], capture_output=True, text=True)
    assert result.returncode == 0
    assert 'Task marked as completed' in result.stdout

def test_delete_task():
    result = subprocess.run(['python', '-m', 'task_manager', 'delete', '--id', '1'], capture_output=True, text=True)
    assert result.returncode == 0
    assert 'Task deleted successfully' in result.stdout