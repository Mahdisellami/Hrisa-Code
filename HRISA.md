# HRISA.md - Project Guide for AI Assistants

## 1. Project Overview

**Hrisa Code** is a CLI coding assistant powered by local LLMs via Ollama. It aims to provide an interactive and efficient way for developers to leverage AI in their coding process. Key features include:

- **Interactive Chat**: Start an interactive session with the AI model.
- **Local Model Support**: Utilize locally hosted LLMs for faster response times.
- **Rich Interface**: Leverage Rich library for enhanced command-line interface.

### Tech Stack
- Python 3.10+
- Typer - CLI framework
- Rich - Enhanced command-line text and layout rendering
- Prompt Toolkit - Building interactive command-line applications
- Questionary - Interactive prompts in the console
- Pydantic - Data validation and settings management using Python type annotations
- PyYAML - YAML parser and emitter for Python
- Pygments - Syntax highlighting

## 2. Project Structure
```
.
├── scripts/
│   ├── setup-venv.sh     # Script to set up virtual environment with venv
│   └── setup-uv.sh       # Script to set up virtual environment using uv (faster)
├── src/
│   └── hrisa_code/
│       ├── __init__.py   # Package initializer, sets version and imports submodules
│       ├── cli.py        # Main CLI interface for Hrisa Code, defines Typer commands
│       ├── core/         # Core modules of the application
│       │   ├── config.py # Configuration management for Hrisa Code
│       │   ├── interactive.py # Handles interactive sessions with the AI model
│       │   └── ollama_client.py # Client to interact with Ollama models, includes configuration and client classes
├── tests/                # Unit tests for the application
│   ├── test_*.py         # Test files following pytest conventions
├── Makefile              # Commands for building, testing, and managing development environment
└── README.md             # Project overview, setup instructions, and usage examples
```

## 3. Key Components

### 1. CLI Entry Point (`src/hrisa_code/cli.py`)
- **Responsibility**: Defines the main entry point for the Hrisa Code CLI using Typer. Handles commands like starting an interactive chat session.

### 2. Configuration Management (`src/hrisa_code/core/config.py`)
- **Responsibility**: Manages configuration settings for the application, ensuring consistent behavior across different environments and sessions.

### 3. Interactive Session Handler (`src/hrisa_code/core/interactive.py`)
- **Responsibility**: Handles interactions between the user and the AI model during an interactive session, managing prompts, responses, and maintaining session state.

### 4. Ollama Client (`src/hrisa_code/core/ollama_client.py`)
- **Responsibility**: Provides a client interface to interact with Ollama models, including configuration setup and request handling for generating model outputs.

## 4. Development Practices

### Code Style
- **Formatting**: Black - Enforces consistent code formatting.
- **Linting**: Ruff - Checks code for style issues and potential bugs.
- **Type Checking**: Mypy - Ensures type consistency and catches type-related errors.

### Testing
- **Framework**: Pytest - Used for writing and running tests.
- **Run**: `pytest` or check Makefile for test command (`make test`).

## 5. Common Tasks

### Adding a New Feature (Command)
1. **Define the Command in `cli.py`**:
   ```python
   @app.command()
   def new_feature():
       """Description of the new feature."""
       console.print("New feature is active!")
   ```
2. **Implement Logic**: Add necessary logic and dependencies in relevant modules under `src/hrisa_code/core/`.
3. **Write Tests**: Create test cases in `tests/test_new_feature.py` using pytest conventions.
4. **Run Tests**: Use `make test` to ensure everything works as expected.

## 6. Important Files
- `README.md` - Project overview, setup instructions, and usage examples.
- `Makefile` - Commands for building, testing, and managing development environment.
- `src/hrisa_code/cli.py` - CLI entry point with Typer commands.
- `src/hrisa_code/core/config.py` - Configuration management for the application.
- `tests/test_*.py` - Unit tests for the application.

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
- **Typer** - CLI framework.
- **Rich** - Enhanced command-line text and layout rendering.
- **Prompt Toolkit** - Building interactive command-line applications.
- **Questionary** - Interactive prompts in the console.
- **Pydantic** - Data validation and settings management using Python type annotations.
- **PyYAML** - YAML parser and emitter for Python.
- **Pygments** - Syntax highlighting.

### Dev Dependencies
- **pytest** - Testing framework.
- **pytest-cov** - Coverage reporting for pytest.
- **black** - Code formatter.
- **ruff** - Linter.
- **mypy** - Type checker.

## 9. Code Patterns

```python
# Pattern: Typer Command Definition
@app.command()
def chat(
    model: Optional[str] = typer.Option(None, help="Specify the AI model to use"),
):
    """Start an interactive chat session with the specified AI model."""
    config = Config(model=model)
    client = OllamaClient(config=config)
    session = InteractiveSession(client=client)
    asyncio.run(session.start())
```

## 10. Notes for AI Assistants
- **File Operations**: The application interacts with files through configuration management and potentially during interactive sessions.
- **Testing**: Always run tests after making changes using `make test`.
- **Architecture**: Modular design with clear separation of concerns, leveraging asynchronous programming (asyncio) for handling user interactions.

## 11. Version Information
- Current Version: 0.1.0
- Python: 3.10+
- Status: Early Development