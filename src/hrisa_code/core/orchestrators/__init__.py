"""Document generation orchestrators.

This module contains orchestrators for generating various types of documentation:
- README.md generation (progressive and legacy)
- API.md generation (progressive and legacy)
- CONTRIBUTING.md generation (progressive and legacy)
- HRISA.md generation (progressive and legacy)
"""

from .progressive_readme_orchestrator import ProgressiveReadmeOrchestrator
from .progressive_api_orchestrator import ProgressiveApiOrchestrator
from .progressive_contributing_orchestrator import ProgressiveContributingOrchestrator
from .progressive_hrisa_orchestrator import ProgressiveHrisaOrchestrator
from .readme_orchestrator import ReadmeOrchestrator
from .api_orchestrator import ApiOrchestrator
from .contributing_orchestrator import ContributingOrchestrator
from .hrisa_orchestrator import HrisaOrchestrator

__all__ = [
    # Progressive (Phase 1)
    "ProgressiveReadmeOrchestrator",
    "ProgressiveApiOrchestrator",
    "ProgressiveContributingOrchestrator",
    "ProgressiveHrisaOrchestrator",
    # Legacy
    "ReadmeOrchestrator",
    "ApiOrchestrator",
    "ContributingOrchestrator",
    "HrisaOrchestrator",
]
