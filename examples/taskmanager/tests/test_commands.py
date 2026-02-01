import unittest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from task_manager.models import Base, Task
from task_manager.cli import add_task, list_tasks, show_task, edit_task, delete_task, search_tasks
from io import StringIO
import sys

class TestTaskManagerCommands(unittest.TestCase):
    def setUp(self):
        # Set up an in-memory SQLite database for testing
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def tearDown(self):
        self.session.close()
        self.engine.dispose()

    def test_add_task(self):
        task = add_task(self.session, 'Test Task', 'This is a test task.', 1, 'pending', ['test'], datetime.now(), None)
        self.assertEqual(task.title, 'Test Task')
        self.assertEqual(task.description, 'This is a test task.')
        self.assertEqual(task.priority, 1)
        self.assertEqual(task.status, 'pending')
        self.assertEqual(task.tags, ['test'])

    def test_list_tasks(self):
        captured_output = StringIO()
        sys.stdout = captured_output
        add_task(self.session, 'Test Task 1', '', 2, 'in_progress', [], datetime.now(), None)
        add_task(self.session, 'Test Task 2', '', 3, 'completed', ['test'], datetime.now(), None)
        list_tasks(self.session)
        sys.stdout = sys.__stdout__
        output = captured_output.getvalue()
        self.assertIn('Test Task 1', output)
        self.assertIn('Test Task 2', output)

    def test_show_task(self):
        captured_output = StringIO()
        sys.stdout = captured_output
        task = add_task(self.session, 'Show Task', '', 1, 'pending', [], datetime.now(), None)
        show_task(self.session, task.id)
        sys.stdout = sys.__stdout__
        output = captured_output.getvalue()
        self.assertIn('Show Task', output)

    def test_edit_task(self):
        task = add_task(self.session, 'Edit Task', '', 1, 'pending', [], datetime.now(), None)
        edited_task = edit_task(self.session, task.id, title='Updated Task')
        self.assertEqual(edited_task.title, 'Updated Task')

    def test_delete_task(self):
        captured_output = StringIO()
        sys.stdout = captured_output
        task = add_task(self.session, 'Delete Task', '', 1, 'pending', [], datetime.now(), None)
        delete_task(self.session, task.id)
        show_task(self.session, task.id)
        sys.stdout = sys.__stdout__
        output = captured_output.getvalue()
        self.assertIn('No task found with ID', output)

    def test_search_tasks(self):
        add_task(self.session, 'Search Task 1', '', 2, 'in_progress', ['search'], datetime.now(), None)
        add_task(self.session, 'Search Task 2', '', 3, 'completed', ['test'], datetime.now(), None)
        tasks = search_tasks(self.session, query='search')
        self.assertEqual(len(tasks), 1)

if __name__ == '__main__':
    unittest.main()
