# HRISA.md - Project Guide for AI Assistants

## 1. Project Overview
**IMPORTANT**: If README.md exists in Key Configuration Files above, use it HEAVILY:
Hrisa Code is a CLI coding assistant powered by local LLMs via Ollama. It helps developers with code completion, debugging, and more.

- **Features:**
	+ Code completion
	+ Debugging
	+ Code formatting
	+ Type checking

## 2. Project Structure

```
# src/hrisa_code/cli.py - CLI entry point with Typer commands
src/
├── hrisa_code
│   ├── __init__.py
│   ├── cli.py
│   └── ...
└── ...

# tests/ - Testing files
tests/

# Makefile - Build and test scripts
Makefile

# README.md - Project description and instructions
README.md
```

## 3. Key Components

### A. Ollama Client (`src/hrisa_code/ollama_client.py`)

- Responsible for interacting with the local LLM (Large Language Model) via Ollama.
- Provides API to send requests and receive responses.

### B. Interactive Session (`src/hrisa_code/interactive.py`)

- Handles user input and output, providing an interactive experience.
- Integrates with Ollama Client to fetch results from the LLM.

## 4. Development Practices

### Code Style
- **Formatting:** Black (version 23.0.0) is used for code formatting.
- **Linting:** Ruff (version 0.1.0) is used for linting.
- **Type Checking:** Mypy (version 1.7.0) is used for type checking.

### Testing
- **Framework:** Pytest (version 7.4.0) is used for testing.
- Run: `make test` to run tests

## 5. Common Tasks

### Adding a New [Feature Type]
To add a new feature, follow these steps:

1. Create a new file in the `src/hrisa_code/` directory with a descriptive name (e.g., `new_feature.py`).
2. Import the necessary modules and define your feature's logic.
3. Integrate your feature with the existing codebase using dependency injection or other design patterns.

## 6. Important Files

### A. `src/hrisa_code/cli.py`
- Main entry point for the CLI application, handling user input and output.

### B. `Makefile`
- Build and test scripts used to automate development tasks.

## 7. Quick Commands
```bash
# Setup
make setup - Set up venv and install dependencies

# Development
make test - Run tests
make format - Format code with black
make lint - Lint code with ruff
...
```

## 8. Dependencies

### Core Dependencies
- `typer` (version 0.3.4) - CLI framework for building applications.
- `rich` (version 10.12.0) - Rich text and formatting library.

### Dev Dependencies
- `pytest` (version 7.4.0) - Testing framework for Python.
- `black` (version 23.0.0) - Code formatting tool.
- `ruff` (version 0.1.0) - Linting tool.
- `mypy` (version 1.7.0) - Type checking tool.

## 9. Code Patterns

### A. Asynchronous Programming (`src/hrisa_code/interactive.py`)
```python
async def fetch_results(self):
    # Fetch results from Ollama Client asynchronously
    pass
```

### B. Dependency Injection (`src/hrisa_code/cli.py`)
```python
def __init__(self, ollama_client: OllamaClient):
    self.ollama_client = ollama_client
    pass
```

## 10. Notes for AI Assistants

- **File Operations:** The project uses file operations to interact with the local LLM.
- **Testing:** Always run tests after making changes to ensure code quality and stability.
- **Architecture:** The project follows a modular architecture, separating concerns into distinct components.

## 11. Version Information
- **Current Version:** 0.1.0
- **Python:** 3.10+
- **Status:** Development