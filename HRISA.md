# HRISA.md - Project Guide for AI Assistants

## 1. Project Overview
Hrisa Code is a CLI coding assistant powered by local LLMs via Ollama. It provides an interactive interface to assist with coding tasks using AI models. The key features of Hrisa Code include:
- Interactive chat interface for coding assistance.
- Support for various local LLM models.
- Integration with the Ollama platform for model management.

### Tech Stack
- **Python**: 3.10+
- **Typer**: Command-line interface framework.
- **Rich**: Rich text and beautiful formatting in the terminal.
- **Pytest**: Framework for writing simple and scalable test cases.
- **Black**: Uncompromising Python code formatter.
- **Ruff**: An extremely fast Python linter.
- **Mypy**: Optional static type checker for Python.

## 2. Project Structure
```
├── src/
│   ├── hrisa_code/
│   │   ├── __init__.py         # Package initialization with version info
│   │   ├── cli.py              # CLI entry point with Typer commands
│   │   └── core/               # Core components of the application
│   │       ├── config.py       # Configuration management
│   │       ├── interactive.py  # Interactive session handling
│   │       └── ollama_client.py # Ollama client for model interaction
├── tests/
│   ├── test_*.py               # Test files following the pytest naming convention
├── scripts/
│   ├── setup-venv.sh           # Script to set up a virtual environment and install dependencies
│   └── setup-uv.sh             # Script to set up using uv (faster)
├── Makefile                    # Contains build, test, and development commands
├── pyproject.toml              # Configuration file for project dependencies and tools
└── README.md                   # Project description and usage instructions
```

## 3. Key Components
### 1. CLI (`src/hrisa_code/cli.py`)
- The main entry point of the application.
- Uses Typer to handle command-line arguments and options.

### 2. Interactive Session (`src/hrisa_code/core/interactive.py`)
- Manages interactive sessions with the AI models.
- Handles user input and model responses in real-time.

### 3. Ollama Client (`src/hrisa_code/core/ollama_client.py`)
- Provides a client interface to interact with the Ollama platform.
- Includes methods for listing available models, pulling models, and sending requests to models.

## 4. Development Practices
### Code Style
- **Formatting**: Black is used to ensure consistent code formatting.
- **Linting**: Ruff is used for linting Python code.
- **Type Checking**: Mypy performs static type checking on the codebase.

### Testing
- **Framework**: Pytest is used as the testing framework.
- **Run**: `pytest` or check Makefile for test command (`make test`).

## 5. Common Tasks
### Adding a New Feature (e.g., Command)
1. Define the new command in `src/hrisa_code/cli.py`.
2. Implement the functionality in a separate module if necessary, e.g., `src/hrisa_code/core/new_feature.py`.
3. Write tests for the new feature in `tests/test_new_feature.py`.

**Example: Adding a New Command**
```python
# src/hrisa_code/cli.py
@app.command()
def new_command():
    """New command description."""
    console.print("Executing new command!")
```

## 6. Important Files
- `src/hrisa_code/__init__.py` - Package initialization with version info.
- `src/hrisa_code/cli.py` - CLI entry point with Typer commands.
- `tests/test_*.py` - Test files following the pytest naming convention.
- `Makefile` - Contains build, test, and development commands.
- `README.md` - Project description and usage instructions.

## 7. Quick Commands
```bash
# Setup
make setup

# Development
make test
make format
make lint
make type-check
```

## 8. Dependencies
### Core Dependencies
- **Pydantic**: Data validation and settings management using Python type annotations.
- **Questionary**: Interactive console prompts for user input.
- **Prompt Toolkit**: Building powerful interactive command line applications in Python.

### Dev Dependencies
- **Black**: Code formatter.
- **Ruff**: Linter.
- **Mypy**: Static type checker.
- **Pytest**: Testing framework.

## 9. Code Patterns
```python
# Pattern: Typer CLI Command Definition
@app.command()
def chat(
    model: Optional[str] = typer.Option(None, help="Specify the model to use"),
):
    """Start an interactive chat session with the specified model."""
    console.print(f"Starting chat with model: {model or 'default'}")
```

## 10. Notes for AI Assistants
- **File Operations**: Use `pathlib.Path` for file operations.
- **Testing**: Always run tests after changes (`make test`).
- **Architecture**: The application is modular, using Typer for CLI and separating concerns between core components.

## 11. Version Information
- Current Version: 0.1.0
- Python: 3.10+
- Status: Early development (Alpha)