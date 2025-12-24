# Contributing to Hrisa Code

Thank you for considering contributing to Hrisa Code! This document provides guidelines and instructions for contributing.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Ollama installed and running
- Git for version control

### Development Setup

1. Fork and clone the repository:
```bash
git clone https://github.com/yourusername/Hrisa-Code.git
cd Hrisa-Code
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install in development mode:
```bash
pip install -e ".[dev]"
```

4. Run tests to verify setup:
```bash
pytest
```

## Development Workflow

### 1. Create a Branch

Create a feature branch for your changes:
```bash
git checkout -b feature/your-feature-name
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Test additions or modifications

### 2. Make Changes

Follow the project's coding standards:
- Use type hints for function parameters and return values
- Write docstrings for all public functions and classes
- Follow PEP 8 style guidelines
- Keep functions focused and modular

### 3. Test Your Changes

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=hrisa_code

# Run specific test file
pytest tests/test_ollama_client.py

# Run with verbose output
pytest -v
```

### 4. Format and Lint

```bash
# Format code
black src/ tests/

# Check code quality
ruff check src/ tests/

# Type checking
mypy src/
```

### 5. Commit Changes

Write clear, descriptive commit messages:
```bash
git add .
git commit -m "Add feature: brief description

- Detailed point 1
- Detailed point 2"
```

Commit message guidelines:
- Use present tense ("Add feature" not "Added feature")
- First line should be 50 characters or less
- Add detailed description after a blank line if needed

### 6. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub with:
- Clear title describing the change
- Description of what changed and why
- Any related issue numbers
- Screenshots if applicable (for UI changes)

## Code Style

### Python Style Guide

We follow PEP 8 with some modifications:
- Line length: 100 characters (configured in pyproject.toml)
- Use type hints
- Use f-strings for string formatting
- Prefer `Path` from `pathlib` over `os.path`

### Example

```python
from pathlib import Path
from typing import Optional

def read_file_content(
    file_path: Path,
    encoding: str = "utf-8",
) -> Optional[str]:
    """Read and return file contents.

    Args:
        file_path: Path to the file to read
        encoding: File encoding (default: utf-8)

    Returns:
        File contents as string, or None if file doesn't exist

    Raises:
        IOError: If file cannot be read
    """
    if not file_path.exists():
        return None

    with open(file_path, "r", encoding=encoding) as f:
        return f.read()
```

## Project Structure

```
Hrisa-Code/
├── src/hrisa_code/       # Main source code
│   ├── cli.py           # CLI entry point
│   ├── core/            # Core functionality
│   ├── tools/           # Tool implementations
│   └── mcp/             # MCP integration
├── tests/               # Test files
├── docs/                # Documentation
├── examples/            # Example scripts
└── pyproject.toml       # Project configuration
```

## Adding New Features

### Adding a New Tool

1. Create tool class in `src/hrisa_code/tools/`:

```python
class MyNewTool:
    @staticmethod
    def get_definition() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "my_tool",
                "description": "What this tool does",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "param1": {
                            "type": "string",
                            "description": "Description of param1",
                        },
                    },
                    "required": ["param1"],
                },
            },
        }

    @staticmethod
    def execute(param1: str) -> str:
        """Execute the tool.

        Args:
            param1: First parameter

        Returns:
            Tool execution result
        """
        # Implementation here
        return f"Result: {param1}"
```

2. Register in `AVAILABLE_TOOLS` dictionary
3. Add tests in `tests/test_tools.py`
4. Update documentation

### Adding a New CLI Command

1. Add command function in `src/hrisa_code/cli.py`:

```python
@app.command()
def mycommand(
    arg: str = typer.Argument(..., help="Argument description"),
    option: bool = typer.Option(False, "--flag", help="Option description"),
) -> None:
    """Command description."""
    # Implementation
```

2. Add tests
3. Update README with new command usage

## Testing Guidelines

### Writing Tests

- Place tests in `tests/` directory
- Name test files `test_*.py`
- Name test functions `test_*`
- Use descriptive test names
- Test both success and error cases

### Test Structure

```python
def test_feature_name():
    """Test description."""
    # Arrange
    setup_data = "test"

    # Act
    result = function_to_test(setup_data)

    # Assert
    assert result == expected_value
```

### Running Specific Tests

```bash
# Run one test file
pytest tests/test_ollama_client.py

# Run one test function
pytest tests/test_ollama_client.py::test_ollama_config_defaults

# Run tests matching pattern
pytest -k "config"
```

## Documentation

### Code Documentation

- Add docstrings to all public functions and classes
- Use Google-style docstrings
- Include type hints in function signatures
- Document exceptions that can be raised

### User Documentation

Update documentation when adding features:
- README.md - Overview and quick start
- docs/QUICKSTART.md - Detailed getting started
- docs/ARCHITECTURE.md - Architecture details
- Code comments for complex logic

## Pull Request Process

1. Update documentation for new features
2. Add tests for new functionality
3. Ensure all tests pass
4. Update CHANGELOG.md (if applicable)
5. Request review from maintainers
6. Address review feedback
7. Maintainer will merge when approved

## Code Review

Reviewers will check:
- Code quality and style
- Test coverage
- Documentation completeness
- Performance implications
- Security considerations

## Questions?

- Open an issue for bugs or feature requests
- Start a discussion for questions
- Check existing issues before creating new ones

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Code of Conduct

Be respectful and constructive:
- Welcome newcomers
- Be patient with questions
- Provide constructive feedback
- Focus on what is best for the project

Thank you for contributing to Hrisa Code!
