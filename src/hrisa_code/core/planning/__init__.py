"""Planning and agent execution.

This module contains components for agentic behavior:
- Autonomous agent loops
- Task planning and execution
- User approval management
- Goal tracking and completion detection
- Loop detection and prevention
- Result verification and relevance checking

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
    ApprovalDecision,
    create_file_write_request,
    create_file_delete_request,
    create_command_request,
    create_git_commit_request,
    create_git_push_request,
)
from .goal_tracker import GoalTracker, GoalStatus, ToolResult
from .loop_detector import LoopDetector, LoopStatus, ToolCall
from .result_verifier import (
    ResultVerifier,
    VerificationResult,
    RelevanceScore,
    InformationGap,
)
from .tool_advisor import (
    ToolAdvisor,
    ToolCapability,
    ToolValidationResult,
    ParameterSuggestion,
    ValidationStatus,
)

__all__ = [
    # Agent
    "AgentLoop",
    # Approval
    "ApprovalManager",
    "ApprovalType",
    "ApprovalRequest",
    "ApprovalDecision",
    "create_file_write_request",
    "create_file_delete_request",
    "create_command_request",
    "create_git_commit_request",
    "create_git_push_request",
    # Goal tracking
    "GoalTracker",
    "GoalStatus",
    "ToolResult",
    # Loop detection
    "LoopDetector",
    "LoopStatus",
    "ToolCall",
    # Result verification
    "ResultVerifier",
    "VerificationResult",
    "RelevanceScore",
    "InformationGap",
    # Tool selection guidance
    "ToolAdvisor",
    "ToolCapability",
    "ToolValidationResult",
    "ParameterSuggestion",
    "ValidationStatus",
]
