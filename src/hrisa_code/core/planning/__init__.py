"""Planning and agent execution.

This module contains components for agentic behavior:
- Autonomous agent loops
- Task planning and execution
- User approval management
- Goal tracking and completion detection
- Loop detection and prevention

FUTURE: This will be expanded with:
- Multi-step planning
- Reasoning and reflection
- Plan optimization
- Parallel execution strategies
"""

from .agent import AgentLoop
from .approval_manager import (
    ApprovalManager,
    ApprovalType,
    ApprovalRequest,
    create_file_write_request,
    create_file_delete_request,
    create_command_request,
    create_git_commit_request,
    create_git_push_request,
)
from .goal_tracker import GoalTracker, GoalStatus
from .loop_detector import LoopDetector, LoopStatus

__all__ = [
    # Agent
    "AgentLoop",
    # Approval
    "ApprovalManager",
    "ApprovalType",
    "ApprovalRequest",
    "create_file_write_request",
    "create_file_delete_request",
    "create_command_request",
    "create_git_commit_request",
    "create_git_push_request",
    # Goal tracking
    "GoalTracker",
    "GoalStatus",
    # Loop detection
    "LoopDetector",
    "LoopStatus",
]
