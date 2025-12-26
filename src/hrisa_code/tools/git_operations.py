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


class GitCommitTool:
    """Tool for creating git commits.

    NOTE: This is a WRITE operation that requires user approval.
    """

    @staticmethod
    def get_definition() -> Dict[str, Any]:
        """Get the tool definition for Ollama function calling."""
        return {
            "type": "function",
            "function": {
                "name": "git_commit",
                "description": "Create a git commit with staged changes. IMPORTANT: This is a write operation that requires user approval. Use git_status and git_diff first to review changes before committing.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "The commit message describing the changes.",
                        },
                        "directory": {
                            "type": "string",
                            "description": "Directory of the git repository. Defaults to current working directory.",
                        },
                        "add_all": {
                            "type": "boolean",
                            "description": "Stage all modified and deleted files before committing (git add -A). Default is false.",
                        },
                    },
                    "required": ["message"],
                },
            },
        }

    @staticmethod
    def execute(
        message: str,
        directory: Optional[str] = None,
        add_all: bool = False,
    ) -> str:
        """Create a git commit.

        Args:
            message: Commit message
            directory: Directory of the git repository
            add_all: Stage all changes before committing

        Returns:
            Commit output or error message
        """
        try:
            cwd = Path(directory) if directory else None

            # Stage all changes if requested
            if add_all:
                add_result = subprocess.run(
                    ["git", "add", "-A"],
                    capture_output=True,
                    text=True,
                    cwd=cwd,
                    timeout=10,
                )
                if add_result.returncode != 0:
                    return f"Error staging files: {add_result.stderr.strip()}"

            # Create commit
            result = subprocess.run(
                ["git", "commit", "-m", message],
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=10,
            )

            if result.returncode != 0:
                stderr = result.stderr.strip()
                # Check for common issues
                if "nothing to commit" in stderr.lower():
                    return "No changes to commit. Use git_status to check repository state."
                return f"Error creating commit: {stderr}"

            return result.stdout.strip()

        except subprocess.TimeoutExpired:
            return "Error: Command timed out after 10 seconds"
        except Exception as e:
            return f"Error executing git commit: {str(e)}"


class GitPushTool:
    """Tool for pushing commits to remote repository.

    NOTE: This is a WRITE operation that requires user approval.
    """

    @staticmethod
    def get_definition() -> Dict[str, Any]:
        """Get the tool definition for Ollama function calling."""
        return {
            "type": "function",
            "function": {
                "name": "git_push",
                "description": "Push commits to remote repository. IMPORTANT: This is a write operation that makes changes visible to others and requires user approval. Review commits with git_log before pushing.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "directory": {
                            "type": "string",
                            "description": "Directory of the git repository. Defaults to current working directory.",
                        },
                        "remote": {
                            "type": "string",
                            "description": "Remote name to push to. Default is 'origin'.",
                        },
                        "branch": {
                            "type": "string",
                            "description": "Branch name to push. If not specified, pushes current branch.",
                        },
                        "set_upstream": {
                            "type": "boolean",
                            "description": "Set upstream tracking for the branch (-u flag). Useful for first push.",
                        },
                    },
                    "required": [],
                },
            },
        }

    @staticmethod
    def execute(
        directory: Optional[str] = None,
        remote: str = "origin",
        branch: Optional[str] = None,
        set_upstream: bool = False,
    ) -> str:
        """Push commits to remote repository.

        Args:
            directory: Directory of the git repository
            remote: Remote name (default: origin)
            branch: Branch name to push
            set_upstream: Set upstream tracking

        Returns:
            Push output or error message
        """
        try:
            cwd = Path(directory) if directory else None

            # Build git push command
            cmd = ["git", "push"]
            if set_upstream:
                cmd.append("-u")
            cmd.append(remote)
            if branch:
                cmd.append(branch)

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=60,  # Push can take longer
            )

            if result.returncode != 0:
                stderr = result.stderr.strip()
                # Provide helpful messages for common issues
                if "no upstream branch" in stderr.lower():
                    return f"Error: No upstream branch configured. Use set_upstream=true to configure.\n{stderr}"
                return f"Error pushing to remote: {stderr}"

            # Git push outputs to stderr even on success
            output = result.stderr.strip() if result.stderr else result.stdout.strip()
            return output if output else "Successfully pushed to remote"

        except subprocess.TimeoutExpired:
            return "Error: Command timed out after 60 seconds"
        except Exception as e:
            return f"Error executing git push: {str(e)}"


class GitPullTool:
    """Tool for pulling changes from remote repository.

    NOTE: This is a WRITE operation that modifies local repository and requires user approval.
    """

    @staticmethod
    def get_definition() -> Dict[str, Any]:
        """Get the tool definition for Ollama function calling."""
        return {
            "type": "function",
            "function": {
                "name": "git_pull",
                "description": "Pull changes from remote repository and merge into current branch. IMPORTANT: This is a write operation that modifies your local repository and requires user approval. Check git_status first to ensure clean working directory.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "directory": {
                            "type": "string",
                            "description": "Directory of the git repository. Defaults to current working directory.",
                        },
                        "remote": {
                            "type": "string",
                            "description": "Remote name to pull from. Default is 'origin'.",
                        },
                        "branch": {
                            "type": "string",
                            "description": "Branch name to pull. If not specified, pulls current branch.",
                        },
                        "rebase": {
                            "type": "boolean",
                            "description": "Use rebase instead of merge when pulling. Default is false.",
                        },
                    },
                    "required": [],
                },
            },
        }

    @staticmethod
    def execute(
        directory: Optional[str] = None,
        remote: str = "origin",
        branch: Optional[str] = None,
        rebase: bool = False,
    ) -> str:
        """Pull changes from remote repository.

        Args:
            directory: Directory of the git repository
            remote: Remote name (default: origin)
            branch: Branch name to pull
            rebase: Use rebase instead of merge

        Returns:
            Pull output or error message
        """
        try:
            cwd = Path(directory) if directory else None

            # Build git pull command
            cmd = ["git", "pull"]
            if rebase:
                cmd.append("--rebase")
            cmd.append(remote)
            if branch:
                cmd.append(branch)

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=60,  # Pull can take longer
            )

            if result.returncode != 0:
                stderr = result.stderr.strip()
                # Provide helpful messages for common issues
                if "merge conflict" in stderr.lower() or "conflict" in stderr.lower():
                    return f"Error: Merge conflict detected. Resolve conflicts manually.\n{stderr}"
                if "uncommitted changes" in stderr.lower():
                    return f"Error: Uncommitted changes would be overwritten. Commit or stash them first.\n{stderr}"
                return f"Error pulling from remote: {stderr}"

            return result.stdout.strip()

        except subprocess.TimeoutExpired:
            return "Error: Command timed out after 60 seconds"
        except Exception as e:
            return f"Error executing git pull: {str(e)}"


class GitStashTool:
    """Tool for stashing uncommitted changes.

    NOTE: This is a WRITE operation that modifies working directory and requires user approval.
    """

    @staticmethod
    def get_definition() -> Dict[str, Any]:
        """Get the tool definition for Ollama function calling."""
        return {
            "type": "function",
            "function": {
                "name": "git_stash",
                "description": "Stash uncommitted changes to save them temporarily. IMPORTANT: This is a write operation that clears your working directory and requires user approval. Use to save work-in-progress before switching branches or pulling changes.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "directory": {
                            "type": "string",
                            "description": "Directory of the git repository. Defaults to current working directory.",
                        },
                        "message": {
                            "type": "string",
                            "description": "Message describing the stashed changes. Helps identify stash later.",
                        },
                        "include_untracked": {
                            "type": "boolean",
                            "description": "Include untracked files in stash (-u flag). Default is false.",
                        },
                        "action": {
                            "type": "string",
                            "description": "Stash action: 'save' (default), 'list', 'pop', 'apply', or 'drop'. Use 'list' to see all stashes.",
                        },
                        "stash_index": {
                            "type": "integer",
                            "description": "Index of stash to pop/apply/drop (0 is most recent). Only used with pop/apply/drop actions.",
                        },
                    },
                    "required": [],
                },
            },
        }

    @staticmethod
    def execute(
        directory: Optional[str] = None,
        message: Optional[str] = None,
        include_untracked: bool = False,
        action: str = "save",
        stash_index: Optional[int] = None,
    ) -> str:
        """Stash uncommitted changes.

        Args:
            directory: Directory of the git repository
            message: Message describing the stash
            include_untracked: Include untracked files
            action: Stash action (save/list/pop/apply/drop)
            stash_index: Index for pop/apply/drop operations

        Returns:
            Stash output or error message
        """
        try:
            cwd = Path(directory) if directory else None

            # Build git stash command based on action
            if action == "list":
                cmd = ["git", "stash", "list"]
            elif action == "pop":
                cmd = ["git", "stash", "pop"]
                if stash_index is not None:
                    cmd.append(f"stash@{{{stash_index}}}")
            elif action == "apply":
                cmd = ["git", "stash", "apply"]
                if stash_index is not None:
                    cmd.append(f"stash@{{{stash_index}}}")
            elif action == "drop":
                cmd = ["git", "stash", "drop"]
                if stash_index is not None:
                    cmd.append(f"stash@{{{stash_index}}}")
            else:  # save (default)
                cmd = ["git", "stash", "push"]
                if include_untracked:
                    cmd.append("-u")
                if message:
                    cmd.extend(["-m", message])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=10,
            )

            if result.returncode != 0:
                stderr = result.stderr.strip()
                if "no local changes to save" in stderr.lower():
                    return "No local changes to stash"
                if "no stash entries" in stderr.lower():
                    return "No stash entries found"
                return f"Error executing git stash: {stderr}"

            output = result.stdout.strip()
            return output if output else f"Stash operation '{action}' completed successfully"

        except subprocess.TimeoutExpired:
            return "Error: Command timed out after 10 seconds"
        except Exception as e:
            return f"Error executing git stash: {str(e)}"


# Tool registry
GIT_TOOLS = {
    # Read-only operations
    "git_status": GitStatusTool,
    "git_diff": GitDiffTool,
    "git_log": GitLogTool,
    "git_branch": GitBranchTool,
    # Write operations (require approval)
    "git_commit": GitCommitTool,
    "git_push": GitPushTool,
    "git_pull": GitPullTool,
    "git_stash": GitStashTool,
}


def get_all_git_tool_definitions() -> list[Dict[str, Any]]:
    """Get all git tool definitions for Ollama function calling.

    Returns:
        List of tool definitions
    """
    return [tool_class.get_definition() for tool_class in GIT_TOOLS.values()]
