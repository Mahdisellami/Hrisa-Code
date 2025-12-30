# Architecture Reorganization

**Date**: December 30, 2025
**Purpose**: Prepare codebase for future agentic architecture

## Overview

The `src/hrisa_code/core/` directory has been reorganized to support future agentic capabilities while maintaining backward compatibility.

## New Structure

```
src/hrisa_code/core/
├── __init__.py                # Re-exports for backward compatibility
├── config.py                  # Configuration management (unchanged)
├── model_catalog.py          # Model catalog (unchanged)
├── model_router.py           # Model routing (unchanged)
│
├── orchestrators/            # Document generation orchestration
│   ├── __init__.py
│   ├── base_orchestrator.py
│   ├── progressive_readme_orchestrator.py
│   ├── progressive_api_orchestrator.py
│   ├── progressive_contributing_orchestrator.py
│   ├── progressive_hrisa_orchestrator.py
│   ├── readme_orchestrator.py (legacy)
│   ├── api_orchestrator.py (legacy)
│   ├── contributing_orchestrator.py (legacy)
│   └── hrisa_orchestrator.py (legacy)
│
├── conversation/             # LLM interaction & conversation management
│   ├── __init__.py
│   ├── conversation.py       # ConversationManager
│   └── ollama_client.py      # OllamaClient, OllamaConfig
│
├── planning/                 # Agentic execution & planning
│   ├── __init__.py
│   ├── agent.py              # AgentLoop for autonomous tasks
│   ├── approval_manager.py   # User approval for operations
│   ├── goal_tracker.py       # Task completion detection
│   └── loop_detector.py      # Repetitive behavior prevention
│
├── memory/                   # Context & memory management
│   ├── __init__.py
│   ├── repo_context.py       # Repository context analysis
│   └── task_manager.py       # Background task execution
│
└── interface/                # User interface components
    ├── __init__.py
    └── interactive.py        # Interactive CLI sessions
```

## Module Responsibilities

### orchestrators/
**Purpose**: Document generation through multi-phase orchestration

Contains both progressive (Phase 1) and legacy orchestrators for generating:
- README.md
- API.md
- CONTRIBUTING.md
- HRISA.md

**Key Pattern**: Extract facts → Build sections → Validate → Assemble

### conversation/
**Purpose**: LLM communication and conversation management

- `ConversationManager`: Multi-turn tool calling, conversation history
- `OllamaClient`: Async Ollama API client
- `OllamaConfig`: LLM configuration

**Key Features**:
- Streaming responses
- Tool execution
- Error recovery
- Text-based tool call parsing

### planning/
**Purpose**: Autonomous agent execution and task planning

**Current Components**:
- `AgentLoop`: Multi-step autonomous task execution
- `ApprovalManager`: User approval for write operations
- `GoalTracker`: Task completion detection
- `LoopDetector`: Prevents repetitive tool calls

**Future Expansion** (ROADMAP):
- Multi-step planning algorithms
- Reasoning and reflection
- Plan optimization strategies
- Parallel execution orchestration
- Meta-planning capabilities

### memory/
**Purpose**: Context management and persistent state

**Current Components**:
- `RepoContext`: Repository analysis and context
- `TaskManager`: Background process management

**Future Expansion** (ROADMAP):
- Vector-based memory search
- Context summarization
- Long-term memory persistence
- Cross-session memory
- Semantic memory retrieval

### interface/
**Purpose**: User interaction and CLI components

**Current Components**:
- `InteractiveSession`: prompt-toolkit based interactive CLI

**Future Expansion** (ROADMAP):
- Multiple UI modes (CLI, TUI, API)
- Custom prompt templates
- Conversation threading
- Rich formatting extensions

## Backward Compatibility

All public APIs are re-exported from `hrisa_code.core.__init__.py`:

```python
# Works before and after reorganization
from hrisa_code.core import ConversationManager, OllamaClient
from hrisa_code.core.orchestrators import ProgressiveReadmeOrchestrator
from hrisa_code.core.planning import ApprovalManager
from hrisa_code.core.memory import TaskManager
```

## Migration Notes

### For External Code

No changes needed! All imports continue to work as before.

### For Internal Development

New imports follow the logical grouping:

```python
# Before
from hrisa_code.core.conversation import ConversationManager
from hrisa_code.core.approval_manager import ApprovalManager

# After (same result, clearer organization)
from hrisa_code.core.conversation import ConversationManager
from hrisa_code.core.planning import ApprovalManager
```

## Circular Import Resolution

**Issue**: `conversation.py` needed `planning` components, and `agent.py` needed `ConversationManager`.

**Solution**: Used `TYPE_CHECKING` and `from __future__ import annotations`:

```python
# In agent.py
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hrisa_code.core.conversation import ConversationManager

class AgentLoop:
    def __init__(self, conversation_manager: ConversationManager):
        # TYPE_CHECKING makes this work without circular import
        ...
```

## Testing

All imports verified:
```bash
python3 -c "
from hrisa_code.core import Config, ConversationManager, OllamaClient
from hrisa_code.core.orchestrators import ProgressiveReadmeOrchestrator
from hrisa_code.core.planning import ApprovalManager
from hrisa_code.core.memory import TaskManager
from hrisa_code.core.interface import InteractiveSession
print('✓ All imports successful!')
"
# Output: ✓ All imports successful!
```

CLI verified:
```bash
hrisa --version
# Output: Hrisa Code version 0.1.0
```

## Future Architecture Vision

This reorganization prepares for:

1. **Tools Module** (exists at `hrisa_code/tools/`):
   - File operations
   - Git operations
   - Command execution
   - Search and discovery

2. **Planning Module** (prepared for expansion):
   - Task decomposition
   - Multi-agent collaboration
   - Reflection and reasoning
   - Adaptive strategies

3. **Memory Module** (prepared for expansion):
   - Vector embeddings
   - Semantic search
   - Long-term persistence
   - Cross-session context

4. **Interface Module** (prepared for expansion):
   - Multiple UI modes
   - Custom interactions
   - API endpoints
   - Webhooks/integrations

## Benefits

1. **Clearer Organization**: Each module has a clear responsibility
2. **Future-Ready**: Structure supports planned agentic features
3. **Backward Compatible**: No breaking changes for existing code
4. **Better Navigation**: Easier to find and understand components
5. **Modularity**: Each subsystem can evolve independently

## Related Documentation

- Phase 1 completion: `docs/PHASE1_100_PERCENT_COMPLETE.md`
- Test results: `docs/PHASE1_TEST_RESULTS.md`
- Original architecture: `docs/ARCHITECTURE.md`
- Future roadmap: `FUTURE.md`

---

**Status**: ✅ Complete
**Backward Compatibility**: ✅ Maintained
**Tests**: ✅ Passing
**CLI**: ✅ Working
