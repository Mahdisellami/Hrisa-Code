import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Task
from app import add_task, list_tasks, show_task, edit_task, delete_task, search_tasks, export_to_json, export_to_csv, export_to_markdown

class TestTaskIntegration(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(bind=self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        self.task1 = add_task(session=self.session, title='Task 1', description='Description for Task 1', priority=1, status='Pending')
        self.task2 = add_task(session=self.session, title='Task 2', description='Description for Task 2', priority=2, status='Completed')

    def tearDown(self):
        self.session.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_add_and_list_tasks(self):
        list_output = []
        def mock_print(message):
            list_output.append(message)
        original_print = __builtins__.print
        __builtins__.print = mock_print
        list_tasks(session=self.session)
        __builtins__.print = original_print
        self.assertIn('Task 1', '\n'.join(list_output))
        self.assertIn('Task 2', '\n'.join(list_output))

    def test_show_task(self):
        show_output = []
        def mock_print(message):
            show_output.append(message)
        original_print = __builtins__.print
        __builtins__.print = mock_print
        show_task(session=self.session, task_id=self.task1.id)
        __builtins__.print = original_print
        self.assertIn('Title: Task 1', '\n'.join(show_output))
        self.assertIn('Description: Description for Task 1', '\n'.join(show_output))

    def test_edit_task(self):
        edit_task(session=self.session, task_id=self.task1.id, status='Completed')
        updated_task = self.session.query(Task).filter_by(id=self.task1.id).first()
        self.assertEqual(updated_task.status, 'Completed')

    def test_delete_task(self):
        delete_task(session=self.session, task_id=self.task1.id)
        remaining_tasks = self.session.query(Task).all()
        self.assertNotIn(self.task1, remaining_tasks)

    def test_search_tasks(self):
        results = search_tasks(session=self.session, query='Task 1')
        self.assertIn(self.task1, results)
        self.assertNotIn(self.task2, results)

    def test_export_to_json(self):
        export_to_json(session=self.session, file_name='test.json')
        with open('test.json', 'r') as f:
            data = json.load(f)
        self.assertEqual(len(data), 2)
        self.assertIn('Task 1', data[0]['title'])

    def test_export_to_csv(self):
        export_to_csv(session=self.session, file_name='test.csv')
        with open('test.csv', 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)
        self.assertEqual(len(rows), 3)  # Header + two tasks
        self.assertIn('Task 1', rows[1][1])

    def test_export_to_markdown(self):
        export_to_markdown(session=self.session, file_name='test.md')
        with open('test.md', 'r') as f:
            content = f.read()
        self.assertIn('# Task 1', content)
        self.assertIn('Description for Task 1', content)

if __name__ == '__main__':
    unittest.main()