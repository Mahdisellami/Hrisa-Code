"""Git operation tools for the coding assistant."""

import subprocess
from pathlib import Path
from typing import Dict, Any, Optional


class GitStatusTool:
    """Tool for checking git repository status."""

    @staticmethod
    def get_definition() -> Dict[str, Any]:
        """Get the tool definition for Ollama function calling."""
        return {
            "type": "function",
            "function": {
                "name": "git_status",
                "description": "Check the current state of the git repository. Shows which files are modified, staged, untracked, and the current branch. Use this to understand repository state before making changes or commits.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "directory": {
                            "type": "string",
                            "description": "Directory of the git repository. Defaults to current working directory.",
                        },
                        "short": {
                            "type": "boolean",
                            "description": "Show output in short format (default: false for detailed output).",
                        },
                    },
                    "required": [],
                },
            },
        }

    @staticmethod
    def execute(directory: Optional[str] = None, short: bool = False) -> str:
        """Check git repository status.

        Args:
            directory: Directory of the git repository
            short: Show output in short format

        Returns:
            Git status output
        """
        try:
            cwd = Path(directory) if directory else None

            # Build git status command
            cmd = ["git", "status"]
            if short:
                cmd.append("--short")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=10,
            )

            if result.returncode != 0:
                return f"Error: {result.stderr.strip()}"

            return result.stdout.strip()

        except subprocess.TimeoutExpired:
            return "Error: Command timed out after 10 seconds"
        except Exception as e:
            return f"Error executing git status: {str(e)}"


class GitDiffTool:
    """Tool for showing git differences."""

    @staticmethod
    def get_definition() -> Dict[str, Any]:
        """Get the tool definition for Ollama function calling."""
        return {
            "type": "function",
            "function": {
                "name": "git_diff",
                "description": "Show differences in the git repository. Can show unstaged changes, staged changes (--cached), or differences between commits. Use this to review changes before committing or to understand what was modified.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "directory": {
                            "type": "string",
                            "description": "Directory of the git repository. Defaults to current working directory.",
                        },
                        "cached": {
                            "type": "boolean",
                            "description": "Show staged changes (--cached). Default is false (shows unstaged changes).",
                        },
                        "file_path": {
                            "type": "string",
                            "description": "Specific file to show diff for. If not provided, shows diff for all files.",
                        },
                        "name_only": {
                            "type": "boolean",
                            "description": "Show only names of changed files, not the actual diff content.",
                        },
                    },
                    "required": [],
                },
            },
        }

    @staticmethod
    def execute(
        directory: Optional[str] = None,
        cached: bool = False,
        file_path: Optional[str] = None,
        name_only: bool = False,
    ) -> str:
        """Show git differences.

        Args:
            directory: Directory of the git repository
            cached: Show staged changes
            file_path: Specific file to show diff for
            name_only: Show only file names

        Returns:
            Git diff output
        """
        try:
            cwd = Path(directory) if directory else None

            # Build git diff command
            cmd = ["git", "diff"]
            if cached:
                cmd.append("--cached")
            if name_only:
                cmd.append("--name-only")
            if file_path:
                cmd.append(file_path)

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=30,
            )

            if result.returncode != 0:
                return f"Error: {result.stderr.strip()}"

            output = result.stdout.strip()
            if not output:
                if cached:
                    return "No staged changes"
                elif file_path:
                    return f"No changes in {file_path}"
                else:
                    return "No unstaged changes"

            return output

        except subprocess.TimeoutExpired:
            return "Error: Command timed out after 30 seconds"
        except Exception as e:
            return f"Error executing git diff: {str(e)}"


class GitLogTool:
    """Tool for viewing git commit history."""

    @staticmethod
    def get_definition() -> Dict[str, Any]:
        """Get the tool definition for Ollama function calling."""
        return {
            "type": "function",
            "function": {
                "name": "git_log",
                "description": "View git commit history. Shows commit hashes, authors, dates, and messages. Use this to understand project history, find specific commits, or review recent changes.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "directory": {
                            "type": "string",
                            "description": "Directory of the git repository. Defaults to current working directory.",
                        },
                        "max_count": {
                            "type": "integer",
                            "description": "Maximum number of commits to show. Default is 10.",
                        },
                        "oneline": {
                            "type": "boolean",
                            "description": "Show each commit on a single line (compact format). Default is false.",
                        },
                        "file_path": {
                            "type": "string",
                            "description": "Show commits that affected a specific file.",
                        },
                    },
                    "required": [],
                },
            },
        }

    @staticmethod
    def execute(
        directory: Optional[str] = None,
        max_count: int = 10,
        oneline: bool = False,
        file_path: Optional[str] = None,
    ) -> str:
        """View git commit history.

        Args:
            directory: Directory of the git repository
            max_count: Maximum number of commits to show
            oneline: Show in compact one-line format
            file_path: Show commits for specific file

        Returns:
            Git log output
        """
        try:
            cwd = Path(directory) if directory else None

            # Build git log command
            cmd = ["git", "log", f"--max-count={max_count}"]
            if oneline:
                cmd.append("--oneline")
            if file_path:
                cmd.extend(["--", file_path])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=10,
            )

            if result.returncode != 0:
                return f"Error: {result.stderr.strip()}"

            output = result.stdout.strip()
            if not output:
                return "No commits found"

            return output

        except subprocess.TimeoutExpired:
            return "Error: Command timed out after 10 seconds"
        except Exception as e:
            return f"Error executing git log: {str(e)}"


class GitBranchTool:
    """Tool for managing git branches."""

    @staticmethod
    def get_definition() -> Dict[str, Any]:
        """Get the tool definition for Ollama function calling."""
        return {
            "type": "function",
            "function": {
                "name": "git_branch",
                "description": "List, create, or get information about git branches. Shows current branch and available branches. Use this to understand branch structure or check which branch you're on.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "directory": {
                            "type": "string",
                            "description": "Directory of the git repository. Defaults to current working directory.",
                        },
                        "list_all": {
                            "type": "boolean",
                            "description": "List all branches including remote branches. Default is false (local only).",
                        },
                        "verbose": {
                            "type": "boolean",
                            "description": "Show branch information with commit hashes and messages.",
                        },
                    },
                    "required": [],
                },
            },
        }

    @staticmethod
    def execute(
        directory: Optional[str] = None,
        list_all: bool = False,
        verbose: bool = False,
    ) -> str:
        """Manage git branches.

        Args:
            directory: Directory of the git repository
            list_all: List all branches including remote
            verbose: Show detailed information

        Returns:
            Git branch output
        """
        try:
            cwd = Path(directory) if directory else None

            # Build git branch command
            cmd = ["git", "branch"]
            if list_all:
                cmd.append("--all")
            if verbose:
                cmd.append("-v")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=10,
            )

            if result.returncode != 0:
                return f"Error: {result.stderr.strip()}"

            return result.stdout.strip()

        except subprocess.TimeoutExpired:
            return "Error: Command timed out after 10 seconds"
        except Exception as e:
            return f"Error executing git branch: {str(e)}"


# Tool registry
GIT_TOOLS = {
    "git_status": GitStatusTool,
    "git_diff": GitDiffTool,
    "git_log": GitLogTool,
    "git_branch": GitBranchTool,
}


def get_all_git_tool_definitions() -> list[Dict[str, Any]]:
    """Get all git tool definitions for Ollama function calling.

    Returns:
        List of tool definitions
    """
    return [tool_class.get_definition() for tool_class in GIT_TOOLS.values()]
