"""Memory and context management.

This module handles:
- Repository context and analysis
- Background task management
- Process monitoring
- Long-term memory storage

FUTURE: This will be expanded with:
- Vector-based memory search
- Context summarization
- Long-term memory persistence
- Cross-session memory
"""

from .repo_context import RepoContext
from .task_manager import TaskManager, BackgroundTask

__all__ = [
    "RepoContext",
    "TaskManager",
    "BackgroundTask",
]
