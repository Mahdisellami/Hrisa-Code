"""Tests for CLI introspection utilities."""

import pytest
from pathlib import Path
from hrisa_code.tools.cli_introspection import (
    extract_cli_commands_from_ast,
    extract_pyproject_metadata,
    validate_content_quality,
)


def test_extract_cli_commands_from_ast():
    """Test extracting CLI commands from cli.py via AST parsing."""
    # Get the actual cli.py file
    cli_file = Path(__file__).parent.parent / "src" / "hrisa_code" / "cli.py"

    commands = extract_cli_commands_from_ast(cli_file)

    # We should find at least the core commands
    assert len(commands) > 0
    command_names = [cmd["name"] for cmd in commands]

    # Check for known commands
    assert "chat" in command_names
    assert "models" in command_names


def test_extract_pyproject_metadata():
    """Test extracting metadata from pyproject.toml."""
    # Get the actual pyproject.toml file
    pyproject_file = Path(__file__).parent.parent / "pyproject.toml"

    metadata = extract_pyproject_metadata(pyproject_file)

    # Should extract basic project info
    assert metadata.get("name") != "UNKNOWN"
    assert "version" in metadata
    assert "description" in metadata


def test_validate_content_quality_good():
    """Test validation passes for clean documentation."""
    good_content = """
# My Project

This is a great project.

## Features

- Feature 1: Does something
- Feature 2: Does another thing

## Installation

Install it with pip.
"""

    is_valid, errors = validate_content_quality(good_content)
    assert is_valid
    assert len(errors) == 0


def test_validate_content_quality_conversational():
    """Test validation catches conversational phrases."""
    bad_content = """
# My Project

It looks like this is a great project. Here are some features:

- Feature 1
- Feature 2

Let me show you how to install it.
"""

    is_valid, errors = validate_content_quality(bad_content)
    assert not is_valid
    assert len(errors) > 0
    assert any("conversational" in error.lower() for error in errors)


def test_validate_content_quality_questions():
    """Test validation catches questions."""
    bad_content = """
# My Project

Could you please provide more information about how to use this?
"""

    is_valid, errors = validate_content_quality(bad_content)
    assert not is_valid
    assert len(errors) > 0
    assert any("question" in error.lower() for error in errors)


def test_validate_content_quality_tool_leak():
    """Test validation catches tool call JSON."""
    bad_content = """
# My Project

Features:

```json
{
    "tool": "read_file",
    "params": {}
}
```
"""

    is_valid, errors = validate_content_quality(bad_content)
    assert not is_valid
    assert len(errors) > 0
    assert any("tool call" in error.lower() for error in errors)
