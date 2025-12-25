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
- File operations (read, write, search)
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
│   ├── hrisa_orchestrator.py # Multi-step orchestration for HRISA.md
│   └── repo_context.py # Repository context management
├── tools/              # Extensible tool system
│   └── file_operations.py # File/command tools with function calling
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
- Commands: `chat`, `models`, `init`
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

### 6. HRISA Orchestrator (`core/hrisa_orchestrator.py`)
- Multi-step repository analysis
- 5-phase orchestration: Architecture → Components → Features → Workflows → Synthesis
- Guided LLM exploration
- Comprehensive documentation generation

### 7. Configuration (`core/config.py`)
- Pydantic models for validation
- YAML-based configuration
- Three-level fallback: project → user → defaults
- Configures models, tools, and server settings

### 8. Tools (`tools/file_operations.py`)
- Tool definition via get_definition()
- Tool execution via execute()
- Available tools: read_file, write_file, list_directory, execute_command, search_files

## Development Practices

### Code Style
- **Formatting**: Black with 100 char line length
- **Linting**: Ruff for fast Python linting
- **Type Checking**: MyPy with strict mode
- **Docstrings**: Google-style for all public functions

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

1. Create tool class in `tools/file_operations.py`:
```python
class MyTool:
    @staticmethod
    def get_definition() -> Dict[str, Any]:
        return {...}  # Tool definition for LLM

    @staticmethod
    def execute(**kwargs) -> str:
        # Implementation
```

2. Register in `AVAILABLE_TOOLS` dict
3. Add tests
4. Update docs

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
- `src/hrisa_code/tools/file_operations.py` - Tools

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
3. Git integration (commit, diff, status)
4. Code analysis tools (linting, type checking)

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
