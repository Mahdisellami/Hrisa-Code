"""Approval manager for handling user confirmation of write operations."""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Set
from pathlib import Path
import difflib
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style as PTStyle
import questionary
from questionary import Choice


class ApprovalType(Enum):
    """Types of operations requiring approval."""
    FILE_WRITE = "file_write"
    FILE_DELETE = "file_delete"
    GIT_COMMIT = "git_commit"
    GIT_PUSH = "git_push"
    GIT_PULL = "git_pull"
    GIT_STASH = "git_stash"
    COMMAND_DESTRUCTIVE = "command_destructive"


class ApprovalDecision(Enum):
    """User's approval decision."""
    YES = "yes"           # Approve this operation
    NO = "no"             # Deny this operation
    ALWAYS = "always"     # Always approve this type (for session)
    NEVER = "never"       # Never approve this type (for session)


@dataclass
class ApprovalRequest:
    """Details about an operation requiring approval."""
    operation_type: ApprovalType
    description: str
    details: Dict[str, str]  # Operation-specific details

    # Optional fields for different operation types
    file_path: Optional[str] = None
    old_content: Optional[str] = None  # For file overwrites
    new_content: Optional[str] = None  # For file overwrites
    command: Optional[str] = None      # For commands


class ApprovalManager:
    """Manages user approval for write operations.

    Features:
    - Interactive prompts with rich formatting
    - Diff preview for file overwrites
    - Session-based approval memory (always/never)
    - Clear operation descriptions
    """

    def __init__(self, auto_approve: bool = False):
        """Initialize approval manager.

        Args:
            auto_approve: If True, automatically approve all operations (for testing)
        """
        self.console = Console()
        self.auto_approve = auto_approve

        # Session-based approval memory
        self._always_approve: Set[ApprovalType] = set()
        self._never_approve: Set[ApprovalType] = set()

    async def request_approval(self, request: ApprovalRequest) -> ApprovalDecision:
        """Request user approval for an operation (async).

        Args:
            request: Details about the operation

        Returns:
            ApprovalDecision indicating user's choice
        """
        # Auto-approve mode (for testing)
        if self.auto_approve:
            return ApprovalDecision.YES

        # Check session memory
        if request.operation_type in self._always_approve:
            return ApprovalDecision.YES

        if request.operation_type in self._never_approve:
            return ApprovalDecision.NO

        # Display operation details
        self._display_approval_request(request)

        # Get user decision (async)
        decision = await self._prompt_user_async(request)

        # Update session memory if always/never chosen
        if decision == ApprovalDecision.ALWAYS:
            self._always_approve.add(request.operation_type)
            return ApprovalDecision.YES
        elif decision == ApprovalDecision.NEVER:
            self._never_approve.add(request.operation_type)
            return ApprovalDecision.NO

        return decision

    def _display_approval_request(self, request: ApprovalRequest) -> None:
        """Display details about the operation requiring approval."""
        # Title based on operation type
        title_map = {
            ApprovalType.FILE_WRITE: "File Write Operation",
            ApprovalType.FILE_DELETE: "File Delete Operation",
            ApprovalType.GIT_COMMIT: "Git Commit Operation",
            ApprovalType.GIT_PUSH: "Git Push Operation",
            ApprovalType.GIT_PULL: "Git Pull Operation",
            ApprovalType.GIT_STASH: "Git Stash Operation",
            ApprovalType.COMMAND_DESTRUCTIVE: "Destructive Command",
        }

        title = title_map.get(request.operation_type, "Operation Requires Approval")

        # Build content
        content_lines = [f"[bold]{request.description}[/bold]", ""]

        # Add operation-specific details
        for key, value in request.details.items():
            content_lines.append(f"[cyan]{key}:[/cyan] {value}")

        # Display panel with basic info
        self.console.print()
        self.console.print(
            Panel(
                "\n".join(content_lines),
                title=title,
                border_style="yellow",
                padding=(1, 2)
            )
        )

        # Show diff for file overwrites in separate panel
        if request.old_content is not None and request.new_content is not None:
            diff = self._generate_diff(
                request.old_content,
                request.new_content,
                request.file_path or "file"
            )
            self.console.print()
            self.console.print(
                Panel(
                    diff,  # This is now a Text object
                    title="[yellow]Changes:[/yellow]",
                    border_style="cyan",
                    padding=(1, 2)
                )
            )

    def _generate_diff(self, old_content: str, new_content: str, file_name: str) -> Text:
        """Generate a colorized diff preview (Claude Code style).

        Args:
            old_content: Original file content
            new_content: New file content
            file_name: Name of the file

        Returns:
            Rich Text object with colorized diff
        """
        old_lines = old_content.splitlines(keepends=False)
        new_lines = new_content.splitlines(keepends=False)

        diff_lines = list(difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{file_name}",
            tofile=f"b/{file_name}",
            lineterm=""
        ))

        if not diff_lines:
            return Text("No changes detected", style="dim")

        # Create colorized diff text
        diff_text = Text()
        max_lines = 30

        for i, line in enumerate(diff_lines):
            if i >= max_lines:
                diff_text.append(f"\n... ({len(diff_lines) - max_lines} more lines)", style="yellow dim")
                break

            if line.startswith('---') or line.startswith('+++'):
                # File headers in bold cyan
                diff_text.append(line + '\n', style="bold cyan")
            elif line.startswith('@@'):
                # Hunk headers in cyan with background
                diff_text.append(line + '\n', style="bold cyan on #1a1a1a")
            elif line.startswith('-'):
                # Removed lines in bold red
                diff_text.append(line + '\n', style="bold red")
            elif line.startswith('+'):
                # Added lines in bold green
                diff_text.append(line + '\n', style="bold green")
            else:
                # Context lines dimmed
                diff_text.append(line + '\n', style="dim")

        return diff_text

    async def _prompt_user_async(self, request: ApprovalRequest) -> ApprovalDecision:
        """Prompt user for approval decision using interactive menu (async version).

        Uses plain input() wrapped in executor for compatibility with running event loop.

        Args:
            request: Details about the operation

        Returns:
            User's decision
        """
        import asyncio

        self.console.print()

        try:
            # Print options clearly
            self.console.print("[bold yellow]Options:[/bold yellow]")
            self.console.print("  [cyan]y[/cyan] - Yes: Approve this operation")
            self.console.print("  [cyan]n[/cyan] - No: Deny this operation")
            self.console.print("  [cyan]a[/cyan] - Always: Approve this type (for this session)")
            self.console.print("  [cyan]v[/cyan] - Never: Never approve this type (for this session)")
            self.console.print()

            # Use questionary select menu for arrow key navigation
            try:
                # Create menu choices
                choices = [
                    Choice(title="Yes - Approve this operation", value="y"),
                    Choice(title="No - Deny this operation", value="n"),
                    Choice(title="Always - Approve this type (for this session)", value="a"),
                    Choice(title="Never - Never approve this type (for this session)", value="v"),
                ]

                # Use questionary select with async
                choice = await questionary.select(
                    "Select your choice:",
                    choices=choices,
                    default="n",
                    style=questionary.Style([
                        ('question', 'fg:#ffff00 bold'),
                        ('highlighted', 'fg:#00ff00 bold'),
                        ('selected', 'fg:#00ff00 bold'),
                    ])
                ).ask_async()

                # Handle cancellation
                if choice is None:
                    self.console.print("\n[yellow]Operation cancelled[/yellow]")
                    return ApprovalDecision.NO

            except (EOFError, KeyboardInterrupt):
                # User pressed Ctrl+C or Ctrl+D
                self.console.print("\n[yellow]Operation cancelled[/yellow]")
                return ApprovalDecision.NO

            # Map choice to decision
            if choice == "y":
                return ApprovalDecision.YES
            elif choice == "n":
                return ApprovalDecision.NO
            elif choice == "a":
                return ApprovalDecision.ALWAYS
            elif choice == "v":
                return ApprovalDecision.NEVER
            else:
                return ApprovalDecision.NO

        except (EOFError, KeyboardInterrupt):
            # User pressed Ctrl+C or Ctrl+D - default to deny
            self.console.print("\n[yellow]Operation cancelled[/yellow]")
            return ApprovalDecision.NO
        except Exception as e:
            # Unexpected error - default to deny
            self.console.print(f"\n[red]Error during approval: {str(e)}[/red]")
            return ApprovalDecision.NO

    async def is_approved(self, request: ApprovalRequest) -> bool:
        """Check if an operation is approved (convenience method, async).

        Args:
            request: Details about the operation

        Returns:
            True if approved, False otherwise
        """
        decision = await self.request_approval(request)
        return decision in (ApprovalDecision.YES, ApprovalDecision.ALWAYS)

    def reset_session_memory(self) -> None:
        """Reset session-based approval memory.

        Useful for starting a fresh session or testing.
        """
        self._always_approve.clear()
        self._never_approve.clear()

    def get_session_approvals(self) -> Dict[str, Set[str]]:
        """Get current session approval state.

        Returns:
            Dictionary with 'always' and 'never' sets
        """
        return {
            "always": {op_type.value for op_type in self._always_approve},
            "never": {op_type.value for op_type in self._never_approve}
        }


def create_file_write_request(
    file_path: str,
    new_content: str,
    old_content: Optional[str] = None
) -> ApprovalRequest:
    """Helper to create a file write approval request.

    Args:
        file_path: Path to the file
        new_content: New content to write
        old_content: Existing content (if overwriting)

    Returns:
        ApprovalRequest for file write operation
    """
    path = Path(file_path)

    if old_content is not None:
        description = f"Overwrite existing file: {path.name}"
    else:
        description = f"Create new file: {path.name}"

    return ApprovalRequest(
        operation_type=ApprovalType.FILE_WRITE,
        description=description,
        details={
            "File": str(path),
            "Action": "Overwrite" if old_content else "Create",
            "Size": f"{len(new_content)} bytes"
        },
        file_path=str(path),
        old_content=old_content,
        new_content=new_content
    )


def create_file_delete_request(file_path: str) -> ApprovalRequest:
    """Helper to create a file delete approval request.

    Args:
        file_path: Path to the file to delete

    Returns:
        ApprovalRequest for file delete operation
    """
    path = Path(file_path)

    return ApprovalRequest(
        operation_type=ApprovalType.FILE_DELETE,
        description=f"Delete file: {path.name}",
        details={
            "File": str(path),
            "Action": "Delete",
            "Warning": "This operation cannot be undone!"
        },
        file_path=str(path)
    )


def create_git_commit_request(message: str, files: list[str]) -> ApprovalRequest:
    """Helper to create a git commit approval request.

    Args:
        message: Commit message
        files: List of files to commit

    Returns:
        ApprovalRequest for git commit operation
    """
    file_list = "\n".join(f"  - {f}" for f in files[:10])
    if len(files) > 10:
        file_list += f"\n  ... and {len(files) - 10} more"

    return ApprovalRequest(
        operation_type=ApprovalType.GIT_COMMIT,
        description="Create git commit",
        details={
            "Message": message,
            "Files": file_list,
            "Count": f"{len(files)} file(s)"
        },
        command=f'git commit -m "{message}"'
    )


def create_git_push_request(branch: str, remote: str = "origin") -> ApprovalRequest:
    """Helper to create a git push approval request.

    Args:
        branch: Branch name to push
        remote: Remote name (default: origin)

    Returns:
        ApprovalRequest for git push operation
    """
    return ApprovalRequest(
        operation_type=ApprovalType.GIT_PUSH,
        description=f"Push commits to remote",
        details={
            "Remote": remote,
            "Branch": branch,
            "Warning": "This will make changes visible to others!"
        },
        command=f"git push {remote} {branch}"
    )


def create_command_request(command: str) -> ApprovalRequest:
    """Helper to create a destructive command approval request.

    Args:
        command: The command to execute

    Returns:
        ApprovalRequest for command execution
    """
    return ApprovalRequest(
        operation_type=ApprovalType.COMMAND_DESTRUCTIVE,
        description="Execute potentially destructive command",
        details={
            "Command": command,
            "Warning": "This command may modify or delete files!"
        },
        command=command
    )
