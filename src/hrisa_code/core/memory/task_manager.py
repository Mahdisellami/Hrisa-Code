"""Background task management for Hrisa Code."""

import json
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel


class BackgroundTask:
    """Represents a background task."""

    def __init__(
        self,
        task_id: str,
        command: str,
        process: subprocess.Popen,
        log_file: Path,
    ):
        """Initialize a background task.

        Args:
            task_id: Unique task identifier
            command: Command being executed
            process: Subprocess handle
            log_file: Path to log file for output
        """
        self.task_id = task_id
        self.command = command
        self.process = process
        self.log_file = log_file
        self.started = datetime.now()
        self.exit_code: Optional[int] = None

    @property
    def pid(self) -> int:
        """Get process ID."""
        return self.process.pid

    @property
    def status(self) -> str:
        """Get current task status."""
        if self.exit_code is not None:
            return "completed" if self.exit_code == 0 else "failed"

        # Check if process is still running
        poll_result = self.process.poll()
        if poll_result is None:
            return "running"
        else:
            self.exit_code = poll_result
            return "completed" if poll_result == 0 else "failed"

    @property
    def elapsed_time(self) -> float:
        """Get elapsed time in seconds."""
        return (datetime.now() - self.started).total_seconds()

    def get_output(self) -> str:
        """Read output from log file.

        Returns:
            Task output as string
        """
        try:
            if self.log_file.exists():
                return self.log_file.read_text()
            return ""
        except Exception as e:
            return f"Error reading output: {str(e)}"

    def kill(self) -> bool:
        """Kill the background task.

        Returns:
            True if killed successfully
        """
        try:
            self.process.terminate()
            time.sleep(0.5)
            if self.process.poll() is None:
                self.process.kill()
            return True
        except Exception:
            return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "id": self.task_id,
            "command": self.command,
            "pid": self.pid,
            "status": self.status,
            "started": self.started.isoformat(),
            "elapsed": f"{self.elapsed_time:.1f}s",
            "exit_code": self.exit_code,
            "log_file": str(self.log_file),
        }


class TaskManager:
    """Manages background tasks."""

    def __init__(self, working_directory: Path):
        """Initialize task manager.

        Args:
            working_directory: Working directory for tasks
        """
        self.working_directory = working_directory
        self.console = Console()

        # Setup task storage
        self.task_dir = Path.home() / ".hrisa" / "tasks"
        self.log_dir = self.task_dir / "logs"
        self.task_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(exist_ok=True)

        # Active tasks
        self.tasks: Dict[str, BackgroundTask] = {}
        self._task_counter = 0

    def create_task(self, command: str) -> BackgroundTask:
        """Create and start a background task.

        Args:
            command: Shell command to execute

        Returns:
            BackgroundTask instance
        """
        self._task_counter += 1
        task_id = f"task-{self._task_counter}"
        log_file = self.log_dir / f"{task_id}.log"

        # Start process with output redirection
        with open(log_file, "w") as log:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=log,
                stderr=subprocess.STDOUT,
                cwd=self.working_directory,
                text=True,
            )

        task = BackgroundTask(task_id, command, process, log_file)
        self.tasks[task_id] = task

        return task

    def get_task(self, task_id: str) -> Optional[BackgroundTask]:
        """Get task by ID.

        Args:
            task_id: Task identifier

        Returns:
            BackgroundTask if found, None otherwise
        """
        return self.tasks.get(task_id)

    def list_tasks(self) -> List[BackgroundTask]:
        """List all tasks.

        Returns:
            List of all tasks
        """
        return list(self.tasks.values())

    def kill_task(self, task_id: str) -> bool:
        """Kill a task by ID.

        Args:
            task_id: Task identifier

        Returns:
            True if killed successfully
        """
        task = self.get_task(task_id)
        if task:
            return task.kill()
        return False

    def cleanup_completed(self) -> int:
        """Remove completed tasks from active list.

        Returns:
            Number of tasks cleaned up
        """
        completed = [
            task_id for task_id, task in self.tasks.items()
            if task.status in ["completed", "failed"]
        ]
        for task_id in completed:
            del self.tasks[task_id]
        return len(completed)

    def display_tasks(self) -> None:
        """Display all tasks in a formatted table."""
        if not self.tasks:
            self.console.print("[yellow]No background tasks running[/yellow]")
            return

        table = Table(title="Background Tasks", show_header=True, header_style="bold cyan")
        table.add_column("ID", style="cyan")
        table.add_column("Command", style="white")
        table.add_column("Status", style="green")
        table.add_column("PID", style="dim")
        table.add_column("Elapsed", style="dim")

        for task in self.tasks.values():
            status_style = {
                "running": "bold green",
                "completed": "bold blue",
                "failed": "bold red",
            }.get(task.status, "white")

            table.add_row(
                task.task_id,
                task.command[:50] + ("..." if len(task.command) > 50 else ""),
                f"[{status_style}]{task.status}[/{status_style}]",
                str(task.pid),
                f"{task.elapsed_time:.1f}s",
            )

        self.console.print(table)

    def display_task_output(self, task_id: str) -> None:
        """Display output for a specific task.

        Args:
            task_id: Task identifier
        """
        task = self.get_task(task_id)
        if not task:
            self.console.print(f"[red]Task '{task_id}' not found[/red]")
            return

        output = task.get_output()

        status_color = {
            "running": "yellow",
            "completed": "green",
            "failed": "red",
        }.get(task.status, "white")

        self.console.print(
            Panel(
                output if output else "[dim]No output yet[/dim]",
                title=f"Task {task_id} - {task.status} ({task.elapsed_time:.1f}s)",
                border_style=status_color,
            )
        )
