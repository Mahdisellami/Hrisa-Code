# Data models for the task manager

from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Task:
    id: int
    title: str
    description: Optional[str] = None
    priority: int = 1
    status: str = 'incomplete'
    tags: Optional[List[str]] = None
    created_at: Optional[str] = None