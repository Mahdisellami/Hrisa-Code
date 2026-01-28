# Hrisa Code - Project Guide for AI Assistants

This document provides context and guidelines for AI coding assistants (like Claude Code) working on this project.

## Project Overview

**Hrisa Code** is a CLI coding assistant powered by local LLMs via Ollama. It's inspired by Claude Code but runs entirely locally with open-source models.

### Key Features
- Interactive CLI chat interface
- Local LLM integration via Ollama
- **Multi-turn tool calling** (Claude Code style)
- **Text-based tool call parsing** (qwen2.5-coder:32b compatibility)
- **Agent mode** for autonomous multi-step tasks
- **Background task execution** with process management
- **HRISA.md generation** with multi-step orchestration
- **Approval manager** for write operation safety
- **Loop detection** to prevent repetitive tool calls
- **Goal tracking** for task completion detection
- File operations (read, write, delete, search)
- Git integration (status, diff, log, branch, commit, push, pull, stash)
- Command execution
- Conversation management
- Docker support

### Tech Stack
- **Language**: Python 3.10+
- **CLI Framework**: Typer
- **Terminal UI**: Rich
- **LLM Backend**: Ollama
- **Testing**: pytest
- **Code Quality**: black, ruff, mypy
- **Deployment**: Docker & Docker Compose

## Project Structure

```
src/hrisa_code/          # Main package
├── cli.py              # CLI entry point with Typer commands
├── core/               # Core functionality
│   ├── config.py       # YAML-based configuration with fallback chain
│   ├── conversation.py # Conversation orchestration & multi-turn tool calling
│   ├── interactive.py  # Interactive session with prompt-toolkit
│   ├── ollama_client.py # Async Ollama API client
│   ├── agent.py        # Autonomous agent loop for multi-step tasks
│   ├── task_manager.py # Background task execution & process management
│   ├── base_orchestrator.py # Base framework for multi-step orchestration
│   ├── hrisa_orchestrator.py # HRISA.md generation orchestrator
│   ├── readme_orchestrator.py # README.md generation orchestrator
│   ├── contributing_orchestrator.py # CONTRIBUTING.md orchestrator
│   ├── api_orchestrator.py # API.md generation orchestrator
│   ├── model_router.py # Multi-model orchestration & model selection
│   ├── approval_manager.py # User approval for write operations
│   ├── loop_detector.py    # Detection of repetitive tool calls
│   ├── goal_tracker.py     # Task completion detection
│   └── repo_context.py # Repository context management
├── tools/              # Extensible tool system
│   ├── file_operations.py # File/command tools with function calling
│   └── git_operations.py  # Git integration tools (status, diff, log, branch)
└── mcp/                # MCP integration (future)
```

## Architecture Principles

1. **Modularity**: Each component has a single responsibility
2. **Async-First**: Use async/await for I/O operations
3. **Type Safety**: Type hints on all functions
4. **Configuration**: Fallback chain (project → user → defaults)
5. **Tool System**: Extensible via function calling pattern
6. **Testing**: Comprehensive unit tests

## Key Components

### 1. CLI (`cli.py`)
- Entry point with Typer commands
- Commands: `chat`, `models`, `init`, `hrisa`, `readme`, `contributing`, `api`
- Uses Rich for beautiful output

### 2. Ollama Client (`core/ollama_client.py`)
- Async client for Ollama API
- Conversation history management
- Streaming support
- Model listing

### 3. Conversation Manager (`core/conversation.py`)
- Orchestrates LLM + tools
- **Multi-turn tool calling** (Claude Code style)
- **Text-based tool call parsing** (extracts JSON from LLM text output)
- Executes tool calls with error recovery
- Path validation to prevent placeholder paths
- Save/load conversations

### 4. Agent Loop (`core/agent.py`)
- Autonomous multi-step task execution
- Reflection and planning
- Error recovery with retry logic
- Completion detection ([TASK_COMPLETE] markers)
- Progress tracking and reporting

### 5. Task Manager (`core/task_manager.py`)
- Background command execution
- Process management (create, monitor, kill)
- Task status tracking
- Output capture and retrieval

### 6. Documentation Orchestration Framework
- **BaseOrchestrator** (`core/base_orchestrator.py`): Framework for multi-step workflows
- **HRISA Orchestrator** (`core/hrisa_orchestrator.py`): AI assistant-focused repository documentation
  - 4 discovery phases: Architecture → Components → Features → Workflows → Synthesis
- **README Orchestrator** (`core/readme_orchestrator.py`): User-friendly project overview
  - 4 discovery phases: Project Discovery → Feature Highlights → Installation → Usage Examples → Synthesis
- **CONTRIBUTING Orchestrator** (`core/contributing_orchestrator.py`): Contributor guidelines
  - 4 discovery phases: Project Setup → Code Standards → Contribution Workflow → Architecture Guide → Synthesis
- **API Orchestrator** (`core/api_orchestrator.py`): Complete API reference
  - 4 discovery phases: CLI Commands → Tools Discovery → Core APIs → Configuration → Synthesis
- **Model Router** (`core/model_router.py`): Multi-model orchestration with specialized model selection

### 7. Approval Manager (`core/approval_manager.py`)
- User confirmation for write operations
- Interactive prompts with rich formatting
- Diff preview for file overwrites
- Session-based memory (always/never approvals)
- Destructive operation detection
- Auto-approve mode for testing

### 8. Loop Detector (`core/loop_detector.py`)
- Detects repetitive tool calls
- Prevents models from getting stuck
- Configurable thresholds (max 3 identical calls)
- Provides feedback to the LLM

### 9. Goal Tracker (`core/goal_tracker.py`)
- Tracks task completion status
- Detects when sufficient information gathered
- Monitors progress across tool rounds
- Prevents premature termination

### 10. Configuration (`core/config.py`)
- Pydantic models for validation
- YAML-based configuration
- Three-level fallback: project → user → defaults
- Configures models, tools, and server settings

### 11. Tools (`tools/file_operations.py` and `tools/git_operations.py`)
- Tool definition via get_definition()
- Tool execution via execute()
- **File operation tools**: read_file, write_file, delete_file, list_directory, execute_command, search_files
- **Git read tools**: git_status, git_diff, git_log, git_branch
- **Git write tools** (require approval): git_commit, git_push, git_pull, git_stash

**IMPORTANT NOTE ON FILE EDITING:**
- There is **NO edit_file or patch tool** available in the tool system
- To modify existing files, **ALWAYS use write_file with the complete file content**
- Read the file first with read_file, make modifications, then write_file the complete new version
- Never attempt to use edit_file, patch_file, or similar - they do not exist

**CRITICAL: DATABASE FILE NAMING REQUIREMENT:**
- When creating database layers for projects, you **MUST** use `db.py` (not database.py, not models.py)
- Location: Project root directory (same level as pyproject.toml)
- Content: SQLAlchemy models AND session management in ONE file
- Example structure:
  ```python
  # db.py
  from sqlalchemy import create_engine, Column, Integer, String
  from sqlalchemy.orm import declarative_base, sessionmaker

  Base = declarative_base()

  class MyModel(Base):
      __tablename__ = 'my_table'
      id = Column(Integer, primary_key=True)
      # ... other columns

  def get_session():
      engine = create_engine('sqlite:///./app.db')
      Session = sessionmaker(bind=engine)
      return Session()
  ```
- **DO NOT** create separate files like `models.py` and `database.py`
- **DO NOT** create subdirectories like `src/myapp/models.py` unless explicitly requested
- This convention ensures consistent, predictable file structure

**IMPORT VALIDATION BEFORE WRITING CODE:**
- Before importing from any module in your code, verify the file exists
- Use `find_files` or `list_directory` to check file exists first
- Only import from files you have created in the current session
- If you create `db.py`, then import from `db` (not from non-existent modules)
- Example of correct workflow:
  1. Create db.py with models
  2. Use find_files to verify db.py exists
  3. Then create cli.py that imports from db
- **NEVER** import from hypothetical files that don't exist yet

**CRITICAL: pyproject.toml STRUCTURE AFFECTS FILE LOCATION:**
- The entry point structure in pyproject.toml determines where models create files
- **For simple projects, use FLAT structure** (files at project root):
  ```toml
  [project.scripts]
  myapp = "cli:app"  # ← Flat structure, files at root
  ```
- **AVOID package structure** unless explicitly needed:
  ```toml
  [project.scripts]
  myapp = "myapp.cli:app"  # ← Package structure, creates myapp/ subdirectory
  ```
- **Why this matters:** Models prioritize structural signals (pyproject.toml) over documentation (CLAUDE.md)
- **V11 Test Proof:** Changing from `taskmanager.cli:app` to `cli:app` fixed critical file location issues
- **When package structure is needed:**
  - Large projects with multiple modules
  - Libraries that need proper package distribution
  - Projects explicitly requesting modular structure
- **Default recommendation:** Use flat structure unless project requirements dictate otherwise
- **Architecture > Documentation:** Models will follow pyproject.toml structure even if CLAUDE.md says otherwise

## Development Practices

### Code Style
- **Formatting**: Black with 100 char line length
- **Linting**: Ruff for fast Python linting
- **Type Checking**: MyPy with strict mode
- **Docstrings**: Google-style for all public functions
- **NO EMOJIS**: Do not use emojis in code, UI, or terminal output. Documentation (README, markdown files) may use emojis sparingly if needed, but code and user interfaces must be emoji-free
- **Syntax Validation**: Before calling write_file, double-check all syntax:
  - Import statements have no typos (e.g., `import typer` not `timport typer`)
  - Type hints have proper syntax (e.g., `Optional[str]` not `Optional`)
  - All opening brackets have matching closing brackets
  - No missing commas in function arguments or dictionary literals

### Loop Prevention Best Practices
When using tools during implementation, avoid getting stuck in loops:
- **File Search**: If a file doesn't exist after 2 search attempts, STOP searching and CREATE the file instead
- **Reading Non-Existent Files**: Never repeatedly try to read files that don't exist (e.g., `src/main.py`)
- **Verification**: Use `find_files` to verify a file exists BEFORE trying to read it
- **Tool Call Limits**: Be aware the system allows max 12 tool rounds per step
- **System Warnings**: If you see "Loop detected" or "approaching tool round limit", immediately change strategy
- **Progress Check**: After 3-4 tool calls with no progress, provide a summary or final answer instead of continuing

### Testing
- **Framework**: pytest with coverage
- **Location**: tests/ directory mirrors src/
- **Coverage Target**: >80% for core modules
- **Run**: `pytest` or `make test`

### Git Workflow
- **Branch naming**: `feature/`, `fix/`, `docs/`, `refactor/`
- **Commits**: Conventional commits (feat:, fix:, docs:, etc.)
- **Testing**: Run tests before committing

## Common Tasks

### Adding a New CLI Command

1. Add command in `cli.py`:
```python
@app.command()
def mycommand(arg: str = typer.Argument(...)) -> None:
    """Command description."""
    # Implementation
```

2. Add tests in `tests/test_cli.py`
3. Update documentation

### Adding a New Tool

1. Create tool class in appropriate module (e.g., `tools/file_operations.py` or `tools/git_operations.py`):
```python
class MyTool:
    @staticmethod
    def get_definition() -> Dict[str, Any]:
        return {...}  # Tool definition for LLM

    @staticmethod
    def execute(**kwargs) -> str:
        # Implementation
```

2. Register in appropriate `TOOLS` dict
3. Import and merge into `AVAILABLE_TOOLS` in `file_operations.py`
4. Add tests in `tests/test_*.py`
5. Update docs (README.md, CLAUDE.md)

### Adding a New Orchestrator

1. Create orchestrator class inheriting from `BaseOrchestrator`:
```python
from hrisa_code.core.base_orchestrator import (
    BaseOrchestrator,
    WorkflowDefinition,
    WorkflowStep,
)

class MyOrchestrator(BaseOrchestrator):
    @property
    def workflow_definition(self) -> WorkflowDefinition:
        return WorkflowDefinition(
            name="MY_DOC",
            description="Description of what it generates",
            audience="Target audience",
            output_filename="MY_DOC.md",
            steps=[
                WorkflowStep(
                    name="discovery_step",
                    display_name="Discovery Step Name",
                    model_preference="architecture",  # or "features", "workflows", "components"
                    prompt_template="""Discovery prompt with {project_path}.

Steps:
1. Use find_files to locate files (be explicit about paths)
2. Read files directly (avoid complex regex)
3. Extract information

IMPORTANT: Use find_files before read_file. Read files directly.

Provide a summary of...""",
                ),
                # Add more steps...
            ],
            synthesis_prompt_template="""Synthesis prompt.

Here are your findings:
{discoveries}

Generate the complete MY_DOC.md content now:""",
        )
```

2. Add CLI command in `cli.py` to expose the orchestrator
3. Follow prompt engineering best practices:
   - Use explicit `find_files` instructions with actual paths (e.g., "src/hrisa_code/tools/")
   - Instruct to read files directly instead of complex regex patterns
   - Add fallback strategies for when goal tracker warns
   - Specify exact file locations when known
4. Add tests for the orchestrator
5. Update docs (README.md, CLAUDE.md)

### Modifying Configuration

1. Edit models in `core/config.py`
2. Update example in `examples/config.example.yaml`
3. Add tests for new config options
4. Document in README

## Important Files

### Core Logic
- `src/hrisa_code/cli.py` - CLI commands
- `src/hrisa_code/core/ollama_client.py` - LLM client
- `src/hrisa_code/core/conversation.py` - Main logic
- `src/hrisa_code/tools/file_operations.py` - File operation tools
- `src/hrisa_code/tools/git_operations.py` - Git integration tools

### Configuration
- `pyproject.toml` - Project metadata and dependencies
- `docker-compose.yml` - Docker orchestration
- `Makefile` - Development commands

### Documentation
- `README.md` - Main documentation
- `docs/ARCHITECTURE.md` - Technical deep dive
- `docs/DOCKER.md` - Docker guide
- `docs/DEVELOPMENT.md` - Development guide
- `docs/QUICKSTART.md` - Getting started

## Dependencies

### Core Dependencies
- `ollama` - Ollama Python client
- `typer[all]` - CLI framework
- `rich` - Terminal UI
- `prompt-toolkit` - Interactive prompts
- `pydantic` - Data validation
- `pyyaml` - Config files

### Dev Dependencies
- `pytest` & `pytest-cov` - Testing
- `black` - Code formatting
- `ruff` - Linting
- `mypy` - Type checking

## Testing Strategy

### Unit Tests
- Test individual functions/classes
- Mock external dependencies (Ollama API)
- Fast execution (<1s for all tests)

### Integration Tests
- Test component interaction
- Use real Ollama (if available)
- Slower but more comprehensive

### Manual Testing
- Test CLI commands
- Test with various models
- Test error handling

## Known Limitations

1. **MCP Integration**: Basic structure only, not fully implemented
2. **Tool Streaming**: Tools work but not with streaming responses
3. **Context Management**: Basic conversation history only
4. **Multi-file Operations**: Single file at a time currently
5. **Model Compatibility**: Some models (e.g., qwen2.5-coder:32b) output tool calls as text instead of structured API - handled via text-based parsing
6. **Loop Detection**: Agent/conversation loops not yet optimized
7. **Performance**: Execution time not yet optimized (functionality-first phase)

## Future Enhancements

**See [FUTURE.md](FUTURE.md) for comprehensive future roadmap!**

### Immediate Priorities
1. Full MCP (Model Context Protocol) integration
2. Enhanced tool calling with streaming
3. Code analysis tools (linting, type checking)
4. Additional git operations (commit, push, pull, stash)

### Major Future Work: Meta-Orchestration System

We're developing a **general-purpose meta-orchestrator** that can handle ANY complex workflow autonomously:

1. **Complexity Detection Module**: Automatically determines if a task needs orchestration
2. **Dynamic Planning Module**: LLM generates task-specific execution plans
3. **Adaptive Execution Engine**: Executes plans with intelligence and adaptation

**Key Innovation**: Instead of hard-coding workflows (like we do for HRISA.md), the system will:
- Analyze any task to determine complexity
- Generate a custom step-by-step plan
- Execute adaptively based on discoveries
- Handle errors and pivot strategies
- Work for diverse task types (not just documentation)

**Example Use Cases**:
```
Task: "Add comprehensive logging"
→ System generates: Discover existing → Design strategy → Implement → Test

Task: "Implement authentication"
→ System generates: Research patterns → Design flow → Implement → Verify

Task: "Refactor error handling"
→ System generates: Audit current → Plan refactor → Execute → Test
```

**Development Philosophy**:
- **Current Phase**: Functionality first - make it work!
- **Future Phase**: Optimize performance, minimize tool calls, adaptive workflows

For detailed architecture and implementation plans, see **[FUTURE.md](FUTURE.md)**.

## When Making Changes

### Before Coding
1. Read relevant code in src/
2. Check existing tests
3. Review architecture in docs/ARCHITECTURE.md

### While Coding
1. Follow existing patterns
2. Add type hints
3. Write docstrings
4. Keep functions small and focused

### After Coding
1. Run tests: `make test`
2. Format code: `make format`
3. Lint: `make lint`
4. Type check: `make type-check`
5. Update docs if needed

## Quick Commands

```bash
# Setup
make setup              # or make setup-uv

# Development
make test               # Run tests
make test-cov           # With coverage
make format             # Format code
make lint               # Lint code
make type-check         # Type check
make check              # Run all checks

# Docker
make docker-up          # Start services
make docker-chat        # Start chat
make docker-down        # Stop services

# Usage
hrisa chat              # Start chat
hrisa models            # List models
hrisa init              # Initialize config
```

## Code Patterns

### Async Functions
```python
async def my_function() -> str:
    result = await client.chat("message")
    return result
```

### Tool Definition
```python
def get_definition() -> Dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": "tool_name",
            "description": "What it does",
            "parameters": {...}
        }
    }
```

### Configuration
```python
class MyConfig(BaseModel):
    option: str = "default"
    flag: bool = True
```

### Error Handling
```python
try:
    result = operation()
except SpecificError as e:
    return f"Error: {str(e)}"
```

## Contact & Resources

- **Repository**: https://github.com/yourusername/Hrisa-Code
- **Issues**: Report bugs and feature requests
- **Discussions**: Ask questions
- **Ollama Docs**: https://ollama.ai/
- **MCP Docs**: https://modelcontextprotocol.io/

## Notes for AI Assistants

- **File Operations**: This is a CLI tool that performs file operations. Be careful with writes.
- **Testing**: Always run tests after making changes
- **Documentation**: Keep docs in sync with code
- **Architecture**: Respect the modular structure
- **Security**: No secrets in code, validate user input
- **Performance**: Async for I/O, efficient for large files

## Version Information

- **Current Version**: 0.1.0
- **Python**: 3.10+
- **Status**: Alpha - core features implemented, MCP integration pending

---

This is a living document. Update it as the project evolves!
- did we test enough?