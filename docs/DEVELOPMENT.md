# Development Guide

Complete guide for developing Hrisa Code locally or with Docker.

## Table of Contents

- [Setup Options](#setup-options)
- [Local Development](#local-development)
- [Docker Development](#docker-development)
- [Testing](#testing)
- [Code Quality](#code-quality)
- [Project Structure](#project-structure)
- [Adding Features](#adding-features)

## Setup Options

Choose the setup method that works best for you:

### Option 1: Make (Recommended)

If you have `make` installed:

```bash
# For local development
make setup          # Using venv
make setup-uv       # Using uv (faster)

# For Docker
make docker-up
make docker-pull
make docker-chat
```

### Option 2: Scripts

```bash
# For local development
./scripts/setup-venv.sh      # Using venv
./scripts/setup-uv.sh        # Using uv (faster)

# For Docker
./scripts/docker-start.sh
./scripts/docker-pull-models.sh
./scripts/docker-chat.sh
```

### Option 3: Manual

See sections below for manual setup steps.

## Local Development

### Prerequisites

- Python 3.10 or higher
- Ollama installed locally
- Git

### Method 1: Using venv (Standard)

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -e ".[dev]"

# Verify installation
hrisa --version
```

### Method 2: Using uv (Fast and Modern)

[uv](https://github.com/astral-sh/uv) is a modern, fast Python package manager.

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Or use uv run (no activation needed)
uv run hrisa --version
```

### Start Ollama

```bash
# Start Ollama server
ollama serve

# In another terminal, pull a model
ollama pull codellama
ollama pull deepseek-coder
```

### Development Workflow

```bash
# 1. Activate environment (venv)
source venv/bin/activate

# Or for uv
source .venv/bin/activate

# 2. Make your changes to code

# 3. Run tests
pytest

# 4. Format code
black src/ tests/

# 5. Lint code
ruff check src/ tests/

# 6. Type check
mypy src/

# 7. Test the CLI
hrisa chat
```

## Docker Development

See [DOCKER.md](DOCKER.md) for complete Docker guide.

### Quick Start

```bash
# Start services
make docker-up

# Pull models
make docker-pull MODEL=codellama

# Start chatting
make docker-chat
```

### Development with Docker

When developing with Docker, you can mount your local source code:

```bash
# Edit docker-compose.yml to add source mount
services:
  hrisa:
    volumes:
      - ./src:/app/src  # Mount source code

# Rebuild after changes
make docker-build

# Or use for live reloading during development
docker compose run --rm \
  -v $(pwd)/src:/app/src \
  -v $(pwd)/workspace:/workspace \
  hrisa hrisa chat
```

## Testing

### Running Tests

```bash
# Run all tests
make test
# or
pytest

# Run with coverage
make test-cov
# or
pytest --cov=hrisa_code --cov-report=term-missing

# Run specific test file
pytest tests/test_config.py

# Run specific test
pytest tests/test_config.py::test_config_defaults

# Run with verbose output
pytest -v

# Run and show print statements
pytest -s
```

### Writing Tests

Place tests in `tests/` directory:

```python
# tests/test_my_feature.py
import pytest
from hrisa_code.my_module import my_function


def test_my_function():
    """Test my feature."""
    result = my_function("input")
    assert result == "expected"


def test_my_function_error():
    """Test error handling."""
    with pytest.raises(ValueError):
        my_function("invalid")
```

### Test Coverage

View coverage report:

```bash
# Generate HTML report
pytest --cov=hrisa_code --cov-report=html

# Open in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## Code Quality

### Formatting with Black

```bash
# Format all code
make format
# or
black src/ tests/

# Check without formatting
black --check src/ tests/

# Format single file
black src/hrisa_code/cli.py
```

### Linting with Ruff

```bash
# Lint all code
make lint
# or
ruff check src/ tests/

# Auto-fix issues
ruff check --fix src/ tests/

# Lint single file
ruff check src/hrisa_code/cli.py
```

### Type Checking with MyPy

```bash
# Type check all code
make type-check
# or
mypy src/

# Type check single file
mypy src/hrisa_code/cli.py

# Generate type coverage report
mypy --html-report mypy-report src/
```

### Pre-commit Checks

Run all checks before committing:

```bash
# Run everything
make check

# This runs: format, lint, type-check, test
```

## Project Structure

```
Hrisa-Code/
├── src/hrisa_code/           # Main package
│   ├── __init__.py
│   ├── cli.py               # CLI entry point
│   ├── core/                # Core functionality
│   │   ├── config.py        # Configuration
│   │   ├── conversation.py  # Conversation manager
│   │   ├── interactive.py   # Interactive session
│   │   └── ollama_client.py # Ollama client
│   ├── tools/               # Tool implementations
│   │   └── file_operations.py
│   └── mcp/                 # MCP integration
│
├── tests/                   # Test files
│   ├── test_config.py
│   └── test_ollama_client.py
│
├── docs/                    # Documentation
│   ├── ARCHITECTURE.md
│   ├── DOCKER.md
│   ├── QUICKSTART.md
│   └── DEVELOPMENT.md
│
├── scripts/                 # Helper scripts
│   ├── docker-*.sh         # Docker scripts
│   ├── setup-*.sh          # Setup scripts
│   └── dev.sh              # Dev helper
│
├── examples/                # Examples
│   ├── basic_usage.py
│   └── config.example.yaml
│
├── workspace/              # Workspace for Docker
│
├── Dockerfile              # Docker image
├── docker-compose.yml      # Docker services
├── Makefile               # Make commands
├── pyproject.toml         # Project config
└── README.md              # Main docs
```

## Adding Features

### Adding a New CLI Command

1. Edit `src/hrisa_code/cli.py`:

```python
@app.command()
def mycommand(
    arg: str = typer.Argument(..., help="Description"),
    option: bool = typer.Option(False, "--flag", help="Flag"),
) -> None:
    """Command description."""
    # Implementation
    console.print(f"Running mycommand with {arg}")
```

2. Add tests in `tests/test_cli.py`

3. Update documentation

### Adding a New Tool

1. Create tool class in `src/hrisa_code/tools/file_operations.py`:

```python
class MyNewTool:
    @staticmethod
    def get_definition() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "my_tool",
                "description": "What it does",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "param": {
                            "type": "string",
                            "description": "Parameter description"
                        }
                    },
                    "required": ["param"]
                }
            }
        }

    @staticmethod
    def execute(param: str) -> str:
        # Implementation
        return f"Result: {param}"
```

2. Register in `AVAILABLE_TOOLS` dictionary

3. Add tests

4. Update documentation

### Adding Configuration Options

1. Edit `src/hrisa_code/core/config.py`:

```python
class MyConfig(BaseModel):
    """My configuration section."""
    my_option: str = "default"
    my_flag: bool = True

class Config(BaseModel):
    """Main configuration."""
    # ... existing fields ...
    my_config: MyConfig = Field(default_factory=MyConfig)
```

2. Update example config in `examples/config.example.yaml`

3. Add tests

## Development Tips

### Hot Reloading

For quick iteration during development:

```bash
# Run with auto-reload (for CLI testing)
while true; do
    clear
    python -m hrisa_code.cli --help
    sleep 1
done
```

### Debugging

```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Or use built-in breakpoint()
breakpoint()

# Run with debugger
python -m pdb -m hrisa_code.cli chat
```

### Environment Variables

```bash
# Set custom Ollama host
export OLLAMA_HOST=http://localhost:11434

# Enable debug logging
export HRISA_DEBUG=1

# Use custom config
export HRISA_CONFIG=~/.config/hrisa-code/config.yaml
```

## Common Issues

### Import Errors

```bash
# Reinstall in editable mode
pip install -e ".[dev]"
```

### Tests Failing

```bash
# Clear cache and rerun
pytest --cache-clear
```

### Type Check Errors

```bash
# Install type stubs
pip install types-PyYAML types-requests
```

## Resources

- [Python Packaging Guide](https://packaging.python.org/)
- [pytest Documentation](https://docs.pytest.org/)
- [Black Documentation](https://black.readthedocs.io/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [MyPy Documentation](https://mypy.readthedocs.io/)
- [uv Documentation](https://github.com/astral-sh/uv)

## Getting Help

- Check existing [issues](https://github.com/yourusername/Hrisa-Code/issues)
- Read the [documentation](../README.md)
- Ask in discussions

Happy developing! 🚀
