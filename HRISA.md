## HRISA.md - Project Guide for AI Assistants

## 1. Project Overview
**IMPORTANT**: If README.md exists in Key Configuration Files above, use it HEAVILY:

Hrisa Code is a CLI coding assistant powered by local LLMs via Ollama. It provides an interactive way to write code and get suggestions on the fly.

### Tech Stack

* Python 3.10+
* Typer for command-line interface
* OllamaClient for interacting with Ollama API
* Rich for terminal rendering
* Markdown for documentation
* Pytest for testing
* Black, Ruff, MyPy for code quality and type checking
* Pyyaml for configuration management

## 2. Project Structure
```markdown
.
├── src/
│   ├── hrisa_code/
│   │   ├── __init__.py
│   │   ├── cli.py
│   │   └── ...
│   ├── tests/
│   │   ├── test_cli.py
│   │   └── ...
│   └── utils/
│       ├── constants.py
│       └── ...
├── Makefile
├── README.md
└── requirements.txt
```

## 3. Key Components

### A. CLI (`src/hrisa_code/cli.py`)
Main entry point for the Hrisa Code application.

### B. OllamaClient (`src/hrisa_code/core/ollama_client.py`)
Handles interactions with the Ollama API.

### C. InteractiveSession (`src/hrisa_code/core/interactive_session.py`)
Manages the interactive session between user and Ollama.

## 4. Development Practices

### Code Style
* Formatting: Black (configured in Makefile)
* Linting: Ruff (configured in Makefile)
* Type Checking: MyPy (configured in Makefile)

### Testing
* Framework: Pytest (configured in Makefile)
* Run: `make test` or `pytest`

## 5. Common Tasks

### Adding a New Feature
1. Create a new file in the `src/hrisa_code/features/` directory.
2. Implement the feature logic and tests accordingly.

### A. Code Quality (`Makefile`)
```bash
# Format code with Black
make format

# Lint code with Ruff
make lint

# Type check code with MyPy
make type-check
```

## 6. Important Files
* `src/hrisa_code/cli.py`: Main CLI entry point.
* `src/hrisa_code/core/ollama_client.py`: Handles Ollama API interactions.
* `Makefile`: Configuration file for Make commands.

## 7. Quick Commands

### A. Setup (`Makefile`)
```bash
# Set up venv and install dependencies
make setup

# Set up with uv (faster)
make setup-uv
```

### B. Development (`Makefile`)
```bash
# Run tests
make test

# Format code
make format

# Lint code
make lint

# Type check code
make type-check
```

## 8. Dependencies

### A. Core Dependencies

* `python` - Python 3.10+
* `typer` - Typer for command-line interface
* `ollama-client` - OllamaClient for interacting with Ollama API
* `rich` - Rich for terminal rendering
* `markdown` - Markdown for documentation

### B. Dev Dependencies

* `pytest` - Pytest for testing
* `black` - Black for code formatting
* `ruff` - Ruff for code linting
* `mypy` - MyPy for type checking
* `pyyaml` - PyYAML for configuration management

## 9. Code Patterns
```python
# Pattern: Async functions
async def get_code_suggestions(self):
    # Code here...
```

```python
# Pattern: Type hints and docstrings
def greet(name: str) -> None:
    """Print a personalized greeting message."""
    print(f"Hello, {name}!")
```

## 10. Notes for AI Assistants

* File Operations: The application handles file operations in the `src/hrisa_code/utils/constants.py` file.
* Testing: Always run tests after making changes to ensure code quality and functionality.
* Architecture: The application follows a modular architecture with separate components for CLI, OllamaClient, and InteractiveSession.

## 11. Version Information

* Current Version: 0.1.0
* Python: 3.10+
* Status: Development