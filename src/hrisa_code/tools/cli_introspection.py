"""Static CLI command introspection utilities.

This module provides tools to extract CLI commands, tools, and other metadata
from the codebase WITHOUT using an LLM. This is for documentation generation
where we need ground-truth facts, not LLM-generated content.
"""

import ast
import inspect
from pathlib import Path
from typing import Any, Dict, List, Optional
import typer


def extract_cli_commands_from_app(app: typer.Typer) -> List[Dict[str, Any]]:
    """Extract CLI commands from a Typer app instance.

    Args:
        app: Typer application instance

    Returns:
        List of command metadata dictionaries
    """
    commands = []

    # Get registered commands from Typer
    if hasattr(app, 'registered_commands'):
        for command in app.registered_commands:
            cmd_info = {
                "name": command.name or command.callback.__name__,
                "help": command.help or "",
                "callback": command.callback.__name__,
            }

            # Extract docstring if help is empty
            if not cmd_info["help"] and command.callback.__doc__:
                cmd_info["help"] = command.callback.__doc__.strip().split('\n')[0]

            commands.append(cmd_info)

    return commands


def extract_cli_commands_from_ast(cli_file: Path) -> List[Dict[str, Any]]:
    """Extract CLI commands by parsing cli.py AST.

    This is more reliable than using LLM since it directly parses code structure.

    Args:
        cli_file: Path to cli.py file

    Returns:
        List of command metadata dictionaries
    """
    if not cli_file.exists():
        return []

    commands = []

    with open(cli_file, 'r') as f:
        tree = ast.parse(f.read())

    # Find all functions decorated with @app.command()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Check for @app.command() decorator
            has_command_decorator = False
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call):
                    if isinstance(decorator.func, ast.Attribute):
                        if (decorator.func.attr == 'command' and
                            isinstance(decorator.func.value, ast.Name) and
                            decorator.func.value.id == 'app'):
                            has_command_decorator = True
                            break

            if has_command_decorator:
                # Extract docstring
                docstring = ast.get_docstring(node) or ""
                first_line = docstring.strip().split('\n')[0] if docstring else ""

                commands.append({
                    "name": node.name,
                    "help": first_line,
                    "function": node.name,
                })

    return commands


def extract_tool_definitions(tools_dir: Path) -> List[Dict[str, Any]]:
    """Extract tool definitions from tools/ directory.

    Args:
        tools_dir: Path to tools directory

    Returns:
        List of tool metadata dictionaries
    """
    if not tools_dir.exists():
        return []

    tools = []

    for tool_file in tools_dir.glob("*.py"):
        if tool_file.name.startswith("_"):
            continue

        with open(tool_file, 'r') as f:
            tree = ast.parse(f.read())

        # Find all classes with get_definition() method
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                has_get_definition = any(
                    isinstance(item, ast.FunctionDef) and item.name == 'get_definition'
                    for item in node.body
                )

                if has_get_definition:
                    docstring = ast.get_docstring(node) or ""

                    tools.append({
                        "name": node.name,
                        "file": tool_file.name,
                        "description": docstring.strip().split('\n')[0] if docstring else "",
                    })

    return tools


def extract_pyproject_metadata(pyproject_path: Path) -> Dict[str, Any]:
    """Extract metadata from pyproject.toml.

    Args:
        pyproject_path: Path to pyproject.toml

    Returns:
        Dictionary of project metadata
    """
    if not pyproject_path.exists():
        return {}

    try:
        import tomli
    except ImportError:
        try:
            import tomllib as tomli  # Python 3.11+
        except ImportError:
            # Fallback to basic parsing
            return _parse_pyproject_basic(pyproject_path)

    with open(pyproject_path, 'rb') as f:
        data = tomli.load(f)

    project = data.get('project', {})

    return {
        "name": project.get('name', 'UNKNOWN'),
        "version": project.get('version', '0.0.0'),
        "description": project.get('description', ''),
        "python_requires": project.get('requires-python', '>=3.10'),
        "dependencies": project.get('dependencies', []),
        "authors": project.get('authors', []),
        "license": project.get('license', {}).get('text', ''),
    }


def _parse_pyproject_basic(pyproject_path: Path) -> Dict[str, Any]:
    """Fallback basic parsing of pyproject.toml without tomli.

    Args:
        pyproject_path: Path to pyproject.toml

    Returns:
        Dictionary of project metadata
    """
    import re

    with open(pyproject_path, 'r') as f:
        content = f.read()

    metadata = {}

    # Extract name
    name_match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
    if name_match:
        metadata['name'] = name_match.group(1)

    # Extract version
    version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
    if version_match:
        metadata['version'] = version_match.group(1)

    # Extract description
    desc_match = re.search(r'description\s*=\s*["\']([^"\']+)["\']', content)
    if desc_match:
        metadata['description'] = desc_match.group(1)

    # Extract python requires
    python_match = re.search(r'requires-python\s*=\s*["\']([^"\']+)["\']', content)
    if python_match:
        metadata['python_requires'] = python_match.group(1)

    return metadata


def validate_content_quality(content: str) -> tuple[bool, List[str]]:
    """Validate documentation content quality.

    Checks for common LLM-generated artifacts that shouldn't be in documentation:
    - Conversational phrases
    - Questions to the user
    - Meta-commentary about the task

    Args:
        content: Documentation content to validate

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    # Check for conversational artifacts
    conversational_phrases = [
        "It looks like",
        "Here are some",
        "Here's a",
        "Let me",
        "I'll",
        "I will",
        "Could you please",
        "I need to know",
        "I've provided",
        "I've included",
        "As you can see",
        "You can see",
    ]

    for phrase in conversational_phrases:
        if phrase in content:
            errors.append(f"Conversational phrase found: '{phrase}'")

    # Check for questions in documentation
    question_indicators = [
        "Could you",
        "Can you provide",
        "Please provide",
        "What would you like",
    ]

    for indicator in question_indicators:
        if indicator in content and "?" in content:
            errors.append(f"Documentation asks questions: '{indicator}'")

    # Check for tool call leakage (JSON artifacts)
    if "```json" in content and '"tool"' in content:
        errors.append("Tool call JSON leaked into documentation")

    # Check for meta-commentary
    meta_phrases = [
        "Based on the code",
        "After analyzing",
        "From what I can see",
        "Looking at the",
    ]

    for phrase in meta_phrases:
        if phrase in content:
            errors.append(f"Meta-commentary found: '{phrase}'")

    return len(errors) == 0, errors
