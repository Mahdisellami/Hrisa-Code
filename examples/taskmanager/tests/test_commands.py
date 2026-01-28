import unittest
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from models import Task, Base
def setup_test_db():
    """Set up an in-memory SQLite database for testing."""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()
class TestTaskCommands(unittest.TestCase):

    def setUp(self):
        self.session = setup_test_db()

    def tearDown(self):
        self.session.close()

    def test_add_task(self):
        from app import add_task
        task = add_task(self.session, 'Test Task', 'This is a test task', priority=1)
        self.assertIsNotNone(task.id)
        self.assertEqual(task.title, 'Test Task')
        self.assertEqual(task.description, 'This is a test task')
        self.assertEqual(task.priority, 1)

    def test_list_tasks(self):
        from app import add_task, list_tasks
        add_task(self.session, 'Task 1', 'Description 1')
        add_task(self.session, 'Task 2', 'Description 2')
        output = []
        def print_mock(*args):
            output.append(' '.join(map(str, args)))
        original_print = __builtins__.print
        try:
            __builtins__.print = print_mock
            list_tasks(self.session)
        finally:
            __builtins__.print = original_print
        self.assertIn('Task 1', '\n'.join(output))
        self.assertIn('Task 2', '\n'.join(output))

    def test_show_task(self):
        from app import add_task, show_task
        task = add_task(self.session, 'Show Task', 'This is a show task')
        output = []
        def print_mock(*args):
            output.append(' '.join(map(str, args)))
        original_print = __builtins__.print
        try:
            __builtins__.print = print_mock
            show_task(self.session, task.id)
        finally:
            __builtins__.print = original_print
        self.assertIn('Show Task', '\n'.join(output))
        self.assertIn('This is a show task', '\n'.join(output))

    def test_edit_task(self):
        from app import add_task, edit_task
        task = add_task(self.session, 'Edit Task', 'Initial description')
        edited_task = edit_task(self.session, task.id, description='Updated description')
        self.assertEqual(edited_task.description, 'Updated description')

    def test_delete_task(self):
        from app import add_task, delete_task
        task = add_task(self.session, 'Delete Task', 'This is a delete task')
        delete_task(self.session, task.id)
        remaining_tasks = self.session.query(Task).all()
        self.assertEqual(len(remaining_tasks), 0)

    def test_search_tasks(self):
        from app import add_task, search_tasks
        add_task(self.session, 'Search Task', 'Description for searching')
        results = search_tasks(self.session, 'searching')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, 'Search Task')

    def test_export_to_json(self):
        from app import add_task, export_to_json
        add_task(self.session, 'Export Task', 'Description for exporting')
        output = []
        def print_mock(*args):
            output.append(' '.join(map(str, args)))
        original_print = __builtins__.print
        try:
            __builtins__.print = print_mock
            export_to_json(self.session)
        finally:
            __builtins__.print = original_print
        with open('tasks.json', 'r') as file:
            data = json.load(file)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['title'], 'Export Task')

if __name__ == '__main__':
    unittest.main()
