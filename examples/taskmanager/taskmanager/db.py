# Database operations for the task manager

import sqlite3
from typing import List, Tuple

DATABASE = 'tasks.db'

# Initialize database and create table if not exists
def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT,
        priority INTEGER DEFAULT 1,
        status TEXT DEFAULT 'incomplete',
        tags TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()

# Add a new task
def add_task(title: str, description: str = '', priority: int = 1, tags: str = ''):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''INSERT INTO tasks (title, description, priority, status, tags) VALUES (?, ?, ?, ?, ?)''',
              (title, description, priority, 'incomplete', tags))
    conn.commit()
    conn.close()

# List all tasks
def list_tasks() -> List[Tuple]:
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''SELECT * FROM tasks''')
    tasks = c.fetchall()
    conn.close()
    return tasks