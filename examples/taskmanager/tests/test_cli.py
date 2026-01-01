import pytest
from typer.testing import CliRunner
from cli import app
from models import Task, Session

runner = CliRunner()

def test_add_task():
    result = runner.invoke(app, ['add', 'title', 'description', '--priority', '1', '--due-date', '2023-10-01'])
    assert result.exit_code == 0
    session = Session()
    task = session.query(Task).filter_by(title='title').first()
    assert task is not None
    assert task.description == 'description'
    assert task.priority == 1
    assert task.due_date == '2023-10-01'

def test_list_tasks():
    result = runner.invoke(app, ['list'])
    assert result.exit_code == 0
    assert 'title' in result.output

def test_show_task():
    session = Session()
    task = Task(title='test', description='test desc', priority=1)
    session.add(task)
    session.commit()
    result = runner.invoke(app, ['show', str(task.id)])
    assert result.exit_code == 0
    assert 'test' in result.output

def test_edit_task():
    session = Session()
    task = Task(title='old title', description='old desc', priority=1)
    session.add(task)
    session.commit()
    result = runner.invoke(app, ['edit', str(task.id), 'new title', 'new desc', '--priority', '2'])
    assert result.exit_code == 0
    updated_task = session.query(Task).get(task.id)
    assert updated_task.title == 'new title'
    assert updated_task.description == 'new desc'
    assert updated_task.priority == 2

def test_complete_task():
    session = Session()
    task = Task(title='complete me', description='test', priority=1, status='incomplete')
    session.add(task)
    session.commit()
    result = runner.invoke(app, ['complete', str(task.id)])
    assert result.exit_code == 0
    completed_task = session.query(Task).get(task.id)
    assert completed_task.status == 'completed'

def test_delete_task():
    session = Session()
    task = Task(title='delete me', description='test', priority=1)
    session.add(task)
    session.commit()
    result = runner.invoke(app, ['delete', str(task.id)])
    assert result.exit_code == 0
    deleted_task = session.query(Task).get(task.id)
    assert deleted_task is None
