"""File operation tools for the coding assistant."""

import os
import re
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class FileOperation(BaseModel):
    """Base class for file operations."""

    name: str
    description: str


class ReadFileTool:
    """Tool for reading file contents."""

    @staticmethod
    def get_definition() -> Dict[str, Any]:
        """Get the tool definition for Ollama function calling."""
        return {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read the contents of a file. Use when you need to view file contents. For finding files by name, use execute_command with find/ls instead.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file to read",
                        },
                        "start_line": {
                            "type": "integer",
                            "description": "Optional starting line number (1-indexed)",
                        },
                        "end_line": {
                            "type": "integer",
                            "description": "Optional ending line number (1-indexed)",
                        },
                    },
                    "required": ["file_path"],
                },
            },
        }

    @staticmethod
    def execute(
        file_path: str, start_line: Optional[int] = None, end_line: Optional[int] = None
    ) -> str:
        """Read file contents.

        Args:
            file_path: Path to the file
            start_line: Optional starting line (1-indexed)
            end_line: Optional ending line (1-indexed)

        Returns:
            File contents
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return f"Error: File not found: {file_path}"

            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            if start_line is not None or end_line is not None:
                start = (start_line - 1) if start_line else 0
                end = end_line if end_line else len(lines)
                lines = lines[start:end]

            return "".join(lines)
        except Exception as e:
            return f"Error reading file: {str(e)}"


class WriteFileTool:
    """Tool for writing to files."""

    @staticmethod
    def get_definition() -> Dict[str, Any]:
        """Get the tool definition for Ollama function calling."""
        return {
            "type": "function",
            "function": {
                "name": "write_file",
                "description": "Write content to a file. Use when creating new files or overwriting existing ones. The system will prompt for confirmation if file exists.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file to write",
                        },
                        "content": {
                            "type": "string",
                            "description": "Content to write to the file",
                        },
                    },
                    "required": ["file_path", "content"],
                },
            },
        }

    @staticmethod
    def execute(file_path: str, content: str) -> str:
        """Write content to a file.

        Args:
            file_path: Path to the file
            content: Content to write

        Returns:
            Success or error message
        """
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

            return f"Successfully wrote to {file_path}"
        except Exception as e:
            return f"Error writing file: {str(e)}"


class ListDirectoryTool:
    """Tool for listing directory contents."""

    @staticmethod
    def get_definition() -> Dict[str, Any]:
        """Get the tool definition for Ollama function calling."""
        return {
            "type": "function",
            "function": {
                "name": "list_directory",
                "description": "List ALL files and directories in a directory. Does NOT support filtering by pattern or extension. Use execute_command with 'ls *.py' or 'find' for pattern-based listing.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "directory_path": {
                            "type": "string",
                            "description": "Path to the directory to list",
                        },
                        "recursive": {
                            "type": "boolean",
                            "description": "Whether to list recursively",
                        },
                    },
                    "required": ["directory_path"],
                },
            },
        }

    @staticmethod
    def execute(directory_path: str, recursive: bool = False) -> str:
        """List directory contents.

        Args:
            directory_path: Path to the directory
            recursive: Whether to list recursively

        Returns:
            Directory listing
        """
        try:
            path = Path(directory_path)
            if not path.exists():
                return f"Error: Directory not found: {directory_path}"

            if not path.is_dir():
                return f"Error: Not a directory: {directory_path}"

            if recursive:
                files = []
                for item in path.rglob("*"):
                    if item.is_file():
                        files.append(str(item.relative_to(path)))
                return "\n".join(sorted(files))
            else:
                items = [item.name for item in path.iterdir()]
                return "\n".join(sorted(items))
        except Exception as e:
            return f"Error listing directory: {str(e)}"


class ExecuteCommandTool:
    """Tool for executing shell commands."""

    @staticmethod
    def get_definition() -> Dict[str, Any]:
        """Get the tool definition for Ollama function calling."""
        return {
            "type": "function",
            "function": {
                "name": "execute_command",
                "description": "Execute a shell command. Use for pattern-based file listing (ls *.py, find), running build tools, git operations, etc. Prefer this over list_directory when filtering files by extension/pattern. For long-running commands (tests, builds, servers), set background=true to run asynchronously.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The command to execute",
                        },
                        "working_directory": {
                            "type": "string",
                            "description": "Working directory for the command",
                        },
                        "background": {
                            "type": "boolean",
                            "description": "Run command in background for long-running operations (tests, builds, servers). Returns task ID immediately.",
                        },
                    },
                    "required": ["command"],
                },
            },
        }

    @staticmethod
    def execute(command: str, working_directory: Optional[str] = None) -> str:
        """Execute a shell command.

        Args:
            command: Command to execute
            working_directory: Optional working directory

        Returns:
            Command output
        """
        try:
            cwd = Path(working_directory) if working_directory else None

            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=30,
            )

            output = result.stdout
            if result.stderr:
                output += f"\nSTDERR:\n{result.stderr}"

            if result.returncode != 0:
                output += f"\nCommand exited with code {result.returncode}"

            return output
        except subprocess.TimeoutExpired:
            return "Error: Command timed out after 30 seconds"
        except Exception as e:
            return f"Error executing command: {str(e)}"


class SearchFilesTool:
    """Tool for searching files using grep."""

    @staticmethod
    def get_definition() -> Dict[str, Any]:
        """Get the tool definition for Ollama function calling."""
        return {
            "type": "function",
            "function": {
                "name": "search_files",
                "description": "Search for regex patterns INSIDE files (grep-like). Supports regular expressions by default. IMPORTANT: Searches line-by-line, so patterns CANNOT match across multiple lines. Use when looking for code/text patterns within files. For listing files by name, use execute_command instead.\n\nLIMITATION: Each line is searched independently. Patterns expecting to match across lines will fail.\n\nGOOD patterns (single-line):\n- '@app\\.command' - finds decorators\n- 'def \\w+\\(' - finds function definitions\n- 'class \\w+:' - finds class definitions\n- 'import .* from' - finds imports\n\nBAD patterns (multi-line, won't work):\n- '@app\\.command\\(.*?def \\w+' - spans decorator and function (different lines)\n- 'if.*:\\n.*return' - expects newline in pattern\n\nWORKAROUND: Use separate simple patterns instead of one multi-line pattern.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "pattern": {
                            "type": "string",
                            "description": "Regex pattern to search for. Examples: '@app\\.command', 'def\\s+\\w+\\(', 'class\\s+ModelCatalog', 'import|from'. For literal strings, set use_regex=false.",
                        },
                        "directory": {
                            "type": "string",
                            "description": "Directory to search in",
                        },
                        "file_pattern": {
                            "type": "string",
                            "description": "File pattern to match. Use '**/*.py' for recursive search (recommended), '*.py' for current directory only. Default: '**/*' (all files recursively).",
                        },
                        "use_regex": {
                            "type": "boolean",
                            "description": "Use regex matching (default: true). Set to false for literal string search.",
                        },
                        "working_directory": {
                            "type": "string",
                            "description": "Alias for 'directory' parameter. Either 'directory' or 'working_directory' can be used.",
                        },
                    },
                    "required": ["pattern"],
                },
            },
        }

    @staticmethod
    def execute(
        pattern: str,
        directory: Optional[str] = None,
        file_pattern: Optional[str] = None,
        use_regex: bool = True,
        working_directory: Optional[str] = None,  # Alias for compatibility
    ) -> str:
        """Search for a pattern in files.

        Args:
            pattern: Pattern to search for (regex if use_regex=True, literal otherwise)
            directory: Directory to search in
            file_pattern: Optional file pattern filter (e.g., '**/*.py')
            use_regex: Whether to use regex matching (default: True)
            working_directory: Alias for directory (for model compatibility)

        Returns:
            Search results
        """
        try:
            # Support both parameter names for compatibility
            dir_path = directory or working_directory
            if not dir_path:
                return "Error: Either 'directory' or 'working_directory' parameter is required"

            path = Path(dir_path)
            if not path.exists():
                return f"Error: Directory not found: {dir_path}"

            # Compile regex pattern if enabled
            regex_compiled = None
            if use_regex:
                try:
                    regex_compiled = re.compile(pattern)
                except re.error as e:
                    return f"Error: Invalid regex pattern '{pattern}': {e}"

            results = []

            # Make file_pattern recursive by default
            if file_pattern:
                # If pattern doesn't start with **, make it recursive
                if not file_pattern.startswith("**"):
                    glob_pattern = f"**/{file_pattern}"
                else:
                    glob_pattern = file_pattern
            else:
                glob_pattern = "**/*"

            for file_path in path.glob(glob_pattern):
                if file_path.is_file():
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            for line_num, line in enumerate(f, 1):
                                # Use regex or literal matching
                                if use_regex:
                                    if regex_compiled.search(line):
                                        results.append(
                                            f"{file_path}:{line_num}: {line.strip()}"
                                        )
                                else:
                                    if pattern in line:
                                        results.append(
                                            f"{file_path}:{line_num}: {line.strip()}"
                                        )
                    except (UnicodeDecodeError, PermissionError):
                        continue

            if not results:
                match_type = "regex" if use_regex else "literal"
                return f"No matches found for {match_type} pattern: {pattern}"

            return "\n".join(results[:100])  # Limit to 100 results
        except Exception as e:
            return f"Error searching files: {str(e)}"


# Tool registry
AVAILABLE_TOOLS = {
    "read_file": ReadFileTool,
    "write_file": WriteFileTool,
    "list_directory": ListDirectoryTool,
    "execute_command": ExecuteCommandTool,
    "search_files": SearchFilesTool,
}


def get_all_tool_definitions() -> List[Dict[str, Any]]:
    """Get all tool definitions for Ollama function calling.

    Returns:
        List of tool definitions
    """
    return [tool_class.get_definition() for tool_class in AVAILABLE_TOOLS.values()]
