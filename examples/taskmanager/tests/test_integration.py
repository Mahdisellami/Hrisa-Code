import pytest
from task_manager.db import create_session, engine, Base
from task_manager.models import Task
from task_manager.cli import add_task, list_tasks, show_task, edit_task, delete_task, search_tasks, export_to_json

@pytest.fixture(scope='module')
def setup_db():
    # Create all tables in the database
    Base.metadata.create_all(engine)
    yield
    # Drop all tables after tests
    Base.metadata.drop_all(engine)

def test_end_to_end_workflow(setup_db):
    session = create_session()
    
    # Test add_task
    task_id = add_task(session, 'Test Task', 'This is a test description', priority=1, status='Pending', tags=['test'], due_date='2023-12-31').id
    assert isinstance(task_id, int)
    
    # Test list_tasks
    captured_output = pytest.capture.result()
    list_tasks(session)
    output = captured_output.out
    assert 'Test Task' in output
    
    # Test show_task
    captured_output = pytest.capture.result()
    show_task(session, task_id)
    output = captured_output.out
    assert 'This is a test description' in output
    
    # Test edit_task
    edit_task(session, task_id, status='Completed')
    edited_task = session.query(Task).get(task_id)
    assert edited_task.status == 'Completed'
    
    # Test search_tasks
    tasks = search_tasks(session, query='test', status='Completed')
    assert len(tasks) == 1
    
    # Test export_to_json
    tasks = session.query(Task).all()
    export_to_json(tasks, 'tasks_export.json')
    with open('tasks_export.json', 'r') as f:
        data = json.load(f)
    assert len(data) == 1
    assert data[0]['title'] == 'Test Task'
    
    # Test delete_task
    captured_output = pytest.capture.result()
    delete_task(session, task_id)
    output = captured_output.out
    assert f'Task {task_id} deleted.' in output
    remaining_tasks = session.query(Task).all()
    assert len(remaining_tasks) == 0