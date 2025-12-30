"""Core functionality for Hrisa Code.

This package is organized for agentic architecture:
- orchestrators: Document generation orchestrators
- conversation: LLM interaction and conversation management
- planning: Agent execution, approval, goal tracking, loop detection
- memory: Context management and task execution
- interface: User interface components (CLI, interactive)
- config: Configuration management
"""

# Re-export key components for backward compatibility
from .config import Config
from .conversation import ConversationManager, OllamaClient, OllamaConfig
from .orchestrators import (
    ProgressiveReadmeOrchestrator,
    ProgressiveApiOrchestrator,
    ProgressiveContributingOrchestrator,
    ProgressiveHrisaOrchestrator,
)
from .planning import AgentLoop, ApprovalManager, GoalTracker, LoopDetector
from .memory import RepoContext, TaskManager
from .interface import InteractiveSession

__all__ = [
    # Config
    "Config",
    # Conversation
    "ConversationManager",
    "OllamaClient",
    "OllamaConfig",
    # Orchestrators
    "ProgressiveReadmeOrchestrator",
    "ProgressiveApiOrchestrator",
    "ProgressiveContributingOrchestrator",
    "ProgressiveHrisaOrchestrator",
    # Planning
    "AgentLoop",
    "ApprovalManager",
    "GoalTracker",
    "LoopDetector",
    # Memory
    "RepoContext",
    "TaskManager",
    # Interface
    "InteractiveSession",
]
