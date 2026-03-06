# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Hrisa Code** is a reverse-engineered implementation of Claude Code (Anthropic's official CLI coding assistant) that runs entirely locally using open-source LLMs via Ollama. The goal is to replicate Claude Code's functionality—interactive chat, tool calling, autonomous agents, and multi-step task execution—without requiring API access or internet connectivity.

### Key Features
- Interactive CLI chat with three execution modes (normal, agent, plan)
- Local LLM integration via Ollama with multi-turn tool calling
- Autonomous agent mode for multi-step tasks
- Plan mode with intelligent complexity detection and step-by-step execution
- Background task execution and process management
- Documentation orchestration (HRISA.md, README.md, CONTRIBUTING.md, API.md)
- Approval manager for safe write operations
- Loop detection and goal tracking
- Comprehensive tool system (29 tools across 5 categories)

### Tech Stack
- **Language**: Python 3.10+
- **CLI Framework**: Typer
- **Terminal UI**: Rich, prompt-toolkit
- **LLM Backend**: Ollama
- **Testing**: pytest with coverage
- **Code Quality**: black, ruff, mypy

## Architecture

The codebase follows a modular, async-first architecture:

```
src/hrisa_code/
├── cli.py                      # CLI entry point (Typer)
├── core/
│   ├── conversation/           # LLM client & conversation orchestration
│   │   ├── ollama_client.py    # Async Ollama API client
│   │   ├── conversation.py     # Multi-turn tool calling
│   │   └── json_repair.py      # Tool call parsing
│   ├── interface/              # Terminal UI
│   │   └── interactive.py      # Interactive session (prompt-toolkit)
│   ├── planning/               # Execution modes & intelligence
│   │   ├── agent.py            # Agent mode (autonomous execution)
│   │   ├── dynamic_planner.py  # Plan mode (complexity detection & planning)
│   │   ├── approval_manager.py # User approval for writes
│   │   ├── loop_detector.py    # Repetitive call detection
│   │   └── goal_tracker.py     # Task completion detection
│   ├── memory/                 # Context & task management
│   │   ├── repo_context.py     # Repository context
│   │   └── task_manager.py     # Background process management
│   ├── orchestrators/          # Multi-step documentation generation
│   │   ├── base_orchestrator.py         # Base framework
│   │   ├── progressive_base.py          # Progressive context building
│   │   ├── *_orchestrator.py            # Traditional orchestrators
│   │   └── progressive_*_orchestrator.py # Progressive variants
│   ├── validation/             # Code quality & preflight checks
│   │   ├── preflight_check.py  # Dependency verification
│   │   ├── setup_manager.py    # Cross-platform setup wizard
│   │   └── code_quality.py     # Syntax & quality validation
│   ├── config.py               # YAML-based configuration (3-level fallback)
│   ├── model_router.py         # Multi-model orchestration
│   └── model_catalog.py        # Model definitions
├── tools/                      # Extensible tool system
│   ├── file_operations.py      # File ops (read, write, delete, search, execute)
│   ├── git_operations.py       # Git ops (status, diff, log, branch, commit, etc.)
│   ├── system_tools.py         # System monitoring (5 tools)
│   ├── docker_tools.py         # Docker management (5 tools)
│   ├── network_tools.py        # Network testing (4 tools)
│   └── cli_introspection.py    # CLI self-inspection
└── mcp/                        # MCP integration (future)
```

### Key Design Principles
1. **Modularity**: Each component has single responsibility
2. **Async-First**: Use async/await for all I/O operations
3. **Type Safety**: Type hints on all functions (mypy strict mode)
4. **Configuration**: Fallback chain (project → user → defaults)
5. **Tool System**: Extensible via function calling pattern
6. **Testing**: Comprehensive unit tests with >80% coverage target

## Development Commands

```bash
# Initial Setup
make setup              # Create venv and install dependencies (macOS/Linux)
make setup-uv           # Faster setup with uv (macOS/Linux)
.\scripts\setup-windows.ps1  # Windows PowerShell setup
.\scripts\setup-windows.bat  # Windows CMD setup

hrisa setup             # Run comprehensive setup wizard
hrisa setup --auto-install   # Auto-install all dependencies
hrisa check             # Verify all dependencies

# Development
make test               # Run tests
make test-cov           # Run tests with coverage report
make format             # Format with black
make lint               # Lint with ruff
make type-check         # Type check with mypy
make check              # Run all checks (format + lint + type-check + test)

# Usage
hrisa chat              # Start interactive chat (NOT hrisa-code)
hrisa models            # List available Ollama models
hrisa init              # Initialize config & generate HRISA.md
hrisa readme            # Generate README.md
hrisa contributing      # Generate CONTRIBUTING.md
hrisa api               # Generate API.md

# Docker
make docker-up          # Start Ollama service
make docker-chat        # Start chat in container
make docker-down        # Stop services
```

## Critical Implementation Notes

### Tool System Architecture

**Available Tools (29 total) by Category:**
- **File Operations (7)**: read_file, write_file, delete_file, list_directory, find_files, search_files, execute_command
- **Git Operations (8)**: git_status, git_diff, git_log, git_branch, git_commit, git_push, git_pull, git_stash
- **System Monitoring (5)**: get_system_info, check_resources, list_processes, check_port, get_env_vars
- **Docker Management (5)**: docker_ps, docker_inspect, docker_logs, docker_exec, docker_images
- **Network Testing (4)**: ping, http_request, dns_lookup, netstat

**CRITICAL: No Edit/Patch Tool**
- There is **NO edit_file or patch tool** in the system
- To modify files: **ALWAYS use write_file with complete content**
- Pattern: read_file → modify in memory → write_file
- Never attempt edit_file, patch_file, or similar (they don't exist)

### Cross-Platform Setup System

**New in v0.2.0**: Comprehensive setup wizard with platform detection

**Setup Manager** (`src/hrisa_code/core/validation/setup_manager.py`):
- Platform detection (macOS, Linux, Windows, Unknown)
- System dependency checks (Python, Git, Curl, Docker)
- Ollama installation and service verification
- Automated PDF library installation
- Model pulling with progress indicators
- Platform-specific fix commands

**Setup Scripts**:
- `scripts/setup-venv.sh` - Unix/Linux setup with venv
- `scripts/setup-uv.sh` - Unix/Linux setup with uv (faster)
- `scripts/setup-windows.ps1` - Windows PowerShell setup
- `scripts/setup-windows.bat` - Windows CMD wrapper

**CLI Commands**:
- `hrisa setup` - Interactive setup wizard
- `hrisa setup --auto-install` - Non-interactive mode
- `hrisa setup --models "model1,model2"` - Specify models
- `hrisa check` - Preflight checks only (no installation)

**What Gets Checked**:
- Python 3.10+ (critical)
- Ollama installation (critical)
- Ollama service running (critical)
- Git (optional)
- Curl (optional)
- Docker (optional)
- PDF libraries (optional, auto-installed)
- Required Ollama models (critical, auto-pulled)

See `docs/SETUP.md` for comprehensive setup guide.

### File Creation Conventions

**Database File Naming (For Generated Projects)**
When creating database layers for example projects:
- **MUST use `db.py`** (not database.py, not models.py)
- Location: Project root (same level as pyproject.toml)
- Content: SQLAlchemy models AND session management in ONE file
- **DO NOT** create separate models.py and database.py
- **DO NOT** create subdirectories like src/myapp/models.py unless explicitly requested

**Import Validation**
Before importing any module:
1. Verify the file exists (use find_files or list_directory)
2. Only import from files created in current session
3. Never import from hypothetical files

**pyproject.toml Structure Affects File Location**
- **Flat structure (recommended for simple projects)**:
  ```toml
  [project.scripts]
  myapp = "cli:app"  # Files created at project root
  ```
- **Package structure (for complex projects)**:
  ```toml
  [project.scripts]
  myapp = "myapp.cli:app"  # Creates myapp/ subdirectory
  ```
- **Default: Use flat structure** unless explicitly needed
- **DO NOT create src/ directory** unless user explicitly requests it
- Models prioritize structural signals (pyproject.toml) over documentation

### Code Style Rules

**Mandatory**:
- Black formatting (100 char line length)
- Ruff linting
- MyPy type hints (strict mode)
- Google-style docstrings for public functions
- **NO EMOJIS** in code or UI (documentation may use sparingly)

**Syntax Validation Before write_file**:
- Check import statements (no typos like `timport` instead of `import`)
- Verify type hint syntax (e.g., `Optional[str]` not `Optional`)
- Match all opening brackets with closing brackets
- Check commas in function arguments and dict literals

### Loop Prevention

If you encounter "Loop detected" or approach tool round limits:
- **File Search**: After 2 failed searches, STOP and CREATE the file
- **Reading Non-Existent Files**: Never repeatedly read files that don't exist
- **Verification**: Use find_files BEFORE read_file
- **Tool Round Limit**: Max 12 rounds per step
- **Progress Check**: After 3-4 calls with no progress, provide summary/answer

## Common Development Tasks

### Adding a New Tool

1. Add tool class to appropriate module (tools/file_operations.py, tools/git_operations.py, etc.):
```python
class MyTool:
    @staticmethod
    def get_definition() -> Dict[str, Any]:
        return {"type": "function", "function": {...}}

    @staticmethod
    def execute(**kwargs) -> str:
        # Implementation
```

2. Register in module's `TOOLS` dict
3. Import and merge into `AVAILABLE_TOOLS` in file_operations.py
4. Add tests in tests/test_*.py
5. Update documentation

### Adding a New Orchestrator

1. Create class inheriting from BaseOrchestrator or ProgressiveBaseOrchestrator
2. Define workflow_definition property with WorkflowDefinition
3. Specify steps with WorkflowStep (name, display_name, model_preference, prompt_template)
4. Add CLI command in cli.py
5. Follow prompt engineering best practices:
   - Use explicit find_files with actual paths
   - Instruct to read files directly (avoid complex regex)
   - Add fallback strategies for goal tracker warnings
6. Add tests

### Adding a New CLI Command

1. Add command in cli.py with @app.command() decorator
2. Use Typer types for arguments/options
3. Add tests in tests/test_cli.py
4. Update README.md and API.md

## Testing Strategy

- **Unit Tests**: Test individual functions/classes, mock external dependencies (Ollama)
- **Integration Tests**: Test component interaction, use real Ollama if available
- **Coverage Target**: >80% for core modules
- **Omitted from Coverage**: CLI, orchestrators, interactive UI (tested via smoke/manual tests)

Run tests with `make test` or `make test-cov` for coverage report.

## Key Configuration Files

- **pyproject.toml**: Project metadata, dependencies, tool config
- **Makefile**: Development commands
- **docker-compose.yml**: Docker orchestration
- **examples/config.example.yaml**: Configuration template

## Current Limitations & Future Work

- MCP integration is basic structure only (not fully implemented)
- Tool streaming works but not optimized
- Context management is basic (conversation history only)
- Performance not yet optimized (functionality-first phase)

See **FUTURE.md** for comprehensive roadmap including meta-orchestration system.

## Important Notes

- **Purpose**: This is a local, open-source reimplementation of Claude Code's functionality
- **Target Parity**: Aims to replicate Claude Code's behavior (tool calling, agents, planning) using local Ollama models
- CLI command is `hrisa` (NOT `hrisa-code`)
- This tool performs file operations - be careful with writes
- Always run tests after changes (`make test`)
- Keep documentation in sync with code
- No secrets in code, validate user input
- Async for I/O, efficient for large files
