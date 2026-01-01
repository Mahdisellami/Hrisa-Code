"""File operation tools for the coding assistant."""

import os
import re
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

# Import git tools
from hrisa_code.tools.git_operations import GIT_TOOLS

# Import code quality validator
from hrisa_code.core.validation.code_quality import CodeQualityValidator


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

            # Validate Python files before writing
            if file_path.endswith('.py'):
                validation_warnings = []

                # Check syntax
                syntax_ok, syntax_error = CodeQualityValidator.validate_python_syntax(content)
                if not syntax_ok:
                    return f"SYNTAX ERROR - File not written:\n{syntax_error}\n\nPlease fix the syntax error and try again."

                # Check imports
                imports_ok, import_issues = CodeQualityValidator.check_imports(content)
                if not imports_ok and import_issues:
                    validation_warnings.append(f"Import warnings:\n" + "\n".join(f"  - {issue}" for issue in import_issues))

                # Check type hints
                hints_ok, hint_issues = CodeQualityValidator.check_type_hints(content, require_hints=False)
                if not hints_ok and hint_issues:
                    validation_warnings.append(f"Type hint warnings:\n" + "\n".join(f"  - {issue}" for issue in hint_issues))

                # Check f-string syntax
                fstring_ok, fstring_issues = CodeQualityValidator.check_fstring_syntax(content)
                if not fstring_ok and fstring_issues:
                    validation_warnings.append(f"F-string warnings:\n" + "\n".join(f"  - {issue}" for issue in fstring_issues))

            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

            result = f"Successfully wrote to {file_path}"

            # Append validation warnings if any
            if file_path.endswith('.py') and validation_warnings:
                result += "\n\nCODE QUALITY WARNINGS:\n" + "\n".join(validation_warnings)
                result += "\n\nConsider fixing these issues in the next step."

            return result
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
                "description": "Search for patterns INSIDE files (grep-like). Use when looking for code/text patterns within files. For finding files by name, use find_files instead.\n\nCOMMON USE CASES:\n1. Find TODO comments: pattern='TODO', directory='.', file_pattern='**/*.py', use_regex=false\n2. Find function definitions: pattern='def\\s+\\w+\\(', directory='src/', use_regex=true\n3. Find class usage: pattern='ModelCatalog', directory='.', use_regex=false\n4. Find decorators: pattern='@app\\.command', directory='src/', use_regex=true\n\nIMPORTANT:\n- For literal strings (TODO, FIXME, class names), set use_regex=false\n- For patterns with special chars (def, \\s, \\w), keep use_regex=true (default)\n- Searches line-by-line only (cannot match across multiple lines)\n- Always provide 'directory' parameter (required)\n- file_pattern is optional (defaults to all files)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "pattern": {
                            "type": "string",
                            "description": "Regex pattern to search for. Examples: 'TODO' (literal), '@app\\.command' (decorator), 'def\\s+\\w+\\(' (functions), 'class\\s+\\w+' (classes). For literal strings like 'TODO' or 'FIXME', set use_regex=false.",
                        },
                        "directory": {
                            "type": "string",
                            "description": "REQUIRED. Directory to search in. Examples: '.' (current), 'src/', 'tests/', '../project/'",
                        },
                        "file_pattern": {
                            "type": "string",
                            "description": "Optional file glob pattern. Examples: '**/*.py' (all Python files recursively), '*.md' (markdown in current dir), '**/*.{js,ts}' (JS/TS files). Default: '**/*' (all files)",
                        },
                        "use_regex": {
                            "type": "boolean",
                            "description": "Use regex matching (default: true). Set to false for literal string search (recommended for simple text like 'TODO').",
                        },
                        "working_directory": {
                            "type": "string",
                            "description": "Alias for 'directory' parameter. Use 'directory' instead (preferred).",
                        },
                    },
                    "required": ["pattern", "directory"],
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


class FindFilesTool:
    """Tool for finding files by name pattern (not content)."""

    @staticmethod
    def get_definition() -> Dict[str, Any]:
        """Get the tool definition for Ollama function calling."""
        return {
            "type": "function",
            "function": {
                "name": "find_files",
                "description": "Find files by NAME pattern (glob-style). Use when looking for files by filename/extension (e.g., '*.log', '*.py', 'test_*.py'). This searches for FILE NAMES, NOT file contents. For searching inside files, use search_files instead.\n\nExamples:\n- Find log files: pattern='*.log'\n- Find Python test files: pattern='test_*.py'\n- Find all markdown files recursively: pattern='**/*.md'\n- Find config files: pattern='*config*'\n\nReturns list of matching file paths.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "pattern": {
                            "type": "string",
                            "description": "Glob pattern to match file names. Use '*' for any characters, '?' for single character, '**/' for recursive search. Examples: '*.log', '**/*.py', 'test_*.txt'",
                        },
                        "directory": {
                            "type": "string",
                            "description": "Directory to search in (default: current directory)",
                        },
                    },
                    "required": ["pattern"],
                },
            },
        }

    @staticmethod
    def execute(pattern: str, directory: Optional[str] = None) -> str:
        """Find files by name pattern.

        Args:
            pattern: Glob pattern to match file names
            directory: Directory to search in (default: current directory)

        Returns:
            List of matching file paths
        """
        try:
            # Use current directory if not specified
            search_dir = Path(directory) if directory else Path.cwd()

            if not search_dir.exists():
                return f"Error: Directory not found: {directory}"

            if not search_dir.is_dir():
                return f"Error: Not a directory: {directory}"

            # Make pattern recursive by default if not already
            glob_pattern = pattern
            if not pattern.startswith("**") and "/" not in pattern:
                # Simple pattern like "*.log" - search recursively
                glob_pattern = f"**/{pattern}"

            # Find matching files
            matches = []
            for file_path in search_dir.glob(glob_pattern):
                if file_path.is_file():
                    # Return relative path for readability
                    try:
                        rel_path = file_path.relative_to(search_dir)
                        matches.append(str(rel_path))
                    except ValueError:
                        # If relative_to fails, use absolute path
                        matches.append(str(file_path))

            if not matches:
                return f"No files found matching pattern: {pattern}"

            # Sort and return (limit to 100 files)
            matches.sort()
            if len(matches) > 100:
                result = "\n".join(matches[:100])
                result += f"\n... and {len(matches) - 100} more files"
                return result

            return "\n".join(matches)

        except Exception as e:
            return f"Error finding files: {str(e)}"


class DeleteFileTool:
    """Tool for deleting files.

    NOTE: This is a WRITE operation that requires user approval.
    """

    @staticmethod
    def get_definition() -> Dict[str, Any]:
        """Get the tool definition for Ollama function calling."""
        return {
            "type": "function",
            "function": {
                "name": "delete_file",
                "description": "Delete a SINGLE file from the filesystem. IMPORTANT: This is a destructive write operation that cannot be undone and requires user approval. Use with extreme caution.\n\nLIMITATION: Only accepts EXACT file paths, NOT glob patterns.\n- WRONG: delete_file(file_path=\"*.log\") - glob patterns not supported!\n- RIGHT: Use find_files(pattern=\"*.log\") first, then delete_file(file_path=\"app.log\") for each file\n\nTo delete multiple files: (1) find_files to get list, (2) delete_file for each",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "EXACT path to a single file to delete. Must be a specific file, NOT a glob pattern like '*.log'. For multiple files, use find_files first to get the list of files.",
                        },
                    },
                    "required": ["file_path"],
                },
            },
        }

    @staticmethod
    def execute(file_path: str) -> str:
        """Delete a file.

        Args:
            file_path: Path to the file to delete

        Returns:
            Success message or error
        """
        try:
            # Check for glob patterns (wildcards)
            if any(char in file_path for char in ['*', '?', '[', ']']):
                return (
                    f"Error: delete_file does not support glob patterns like '{file_path}'.\n"
                    f"To delete multiple files:\n"
                    f"1. First use find_files(pattern=\"{file_path}\") to find matching files\n"
                    f"2. Then delete each file individually using delete_file(file_path=\"exact/path/to/file\")\n"
                    f"Example: find_files(pattern=\"*.log\") → then delete_file(file_path=\"app.log\")"
                )

            path = Path(file_path)

            # Check if file exists
            if not path.exists():
                return f"Error: File not found: {file_path}"

            # Check if it's a file (not a directory)
            if not path.is_file():
                return f"Error: Path is not a file: {file_path}. Use remove_directory for directories."

            # Delete the file
            path.unlink()

            return f"Successfully deleted file: {file_path}"

        except PermissionError:
            return f"Error: Permission denied to delete: {file_path}"
        except Exception as e:
            return f"Error deleting file: {str(e)}"


# Tool registry
AVAILABLE_TOOLS = {
    "read_file": ReadFileTool,
    "write_file": WriteFileTool,
    "list_directory": ListDirectoryTool,
    "execute_command": ExecuteCommandTool,
    "search_files": SearchFilesTool,
    "find_files": FindFilesTool,
    "delete_file": DeleteFileTool,
    **GIT_TOOLS,  # Add git tools
}


def get_all_tool_definitions() -> List[Dict[str, Any]]:
    """Get all tool definitions for Ollama function calling.

    Returns:
        List of tool definitions
    """
    return [tool_class.get_definition() for tool_class in AVAILABLE_TOOLS.values()]
