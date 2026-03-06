"""Comprehensive setup manager for Hrisa Code across all platforms."""

import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt
from rich.table import Table


class Platform(Enum):
    """Supported platforms."""

    MACOS = "darwin"
    LINUX = "linux"
    WINDOWS = "windows"
    UNKNOWN = "unknown"


class SetupStatus(Enum):
    """Status of setup steps."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class SetupStep:
    """A step in the setup process."""

    name: str
    description: str
    status: SetupStatus = SetupStatus.PENDING
    error_message: Optional[str] = None
    fix_command: Optional[str] = None


class SetupManager:
    """Manages cross-platform setup and dependency installation."""

    def __init__(self, console: Optional[Console] = None, auto_install: bool = False):
        """Initialize the setup manager.

        Args:
            console: Rich console for output
            auto_install: Automatically install dependencies without prompting
        """
        self.console = console or Console()
        self.auto_install = auto_install
        self.platform = self._detect_platform()
        self.steps: List[SetupStep] = []

    def _detect_platform(self) -> Platform:
        """Detect the current platform.

        Returns:
            Platform enum value
        """
        system = platform.system().lower()
        if system == "darwin":
            return Platform.MACOS
        elif system == "linux":
            return Platform.LINUX
        elif system == "windows":
            return Platform.WINDOWS
        else:
            return Platform.UNKNOWN

    def _run_command(
        self, cmd: List[str], timeout: int = 30, shell: bool = False
    ) -> Tuple[bool, str, str]:
        """Run a command and return success status and output.

        Args:
            cmd: Command to run as list
            timeout: Timeout in seconds
            shell: Run in shell mode

        Returns:
            Tuple of (success, stdout, stderr)
        """
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=shell,
            )
            return (
                result.returncode == 0,
                result.stdout.strip(),
                result.stderr.strip(),
            )
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)

    def check_python_version(self) -> SetupStep:
        """Check if Python version meets requirements.

        Returns:
            SetupStep with result
        """
        step = SetupStep(
            name="Python Version",
            description="Checking Python 3.10+ requirement",
        )

        version = sys.version_info
        required = (3, 10)

        if version >= required:
            step.status = SetupStatus.SUCCESS
        else:
            step.status = SetupStatus.FAILED
            step.error_message = (
                f"Python {version.major}.{version.minor} < 3.10 required"
            )
            step.fix_command = "Install Python 3.10+ from https://python.org"

        return step

    def check_git_installed(self) -> SetupStep:
        """Check if git is installed.

        Returns:
            SetupStep with result
        """
        step = SetupStep(
            name="Git",
            description="Checking git installation",
        )

        git_path = shutil.which("git")

        if git_path:
            success, version, _ = self._run_command(["git", "--version"])
            if success:
                step.status = SetupStatus.SUCCESS
            else:
                step.status = SetupStatus.FAILED
                step.error_message = "Git found but version check failed"
        else:
            step.status = SetupStatus.FAILED
            step.error_message = "Git not found"

            if self.platform == Platform.MACOS:
                step.fix_command = "brew install git"
            elif self.platform == Platform.LINUX:
                step.fix_command = "sudo apt-get install git  # or yum install git"
            elif self.platform == Platform.WINDOWS:
                step.fix_command = (
                    "Download from https://git-scm.com/download/windows"
                )

        return step

    def check_curl_installed(self) -> SetupStep:
        """Check if curl is installed.

        Returns:
            SetupStep with result
        """
        step = SetupStep(
            name="Curl",
            description="Checking curl installation",
        )

        curl_path = shutil.which("curl")

        if curl_path:
            step.status = SetupStatus.SUCCESS
        else:
            step.status = SetupStatus.FAILED
            step.error_message = "Curl not found"

            if self.platform == Platform.MACOS:
                step.fix_command = "brew install curl"
            elif self.platform == Platform.LINUX:
                step.fix_command = "sudo apt-get install curl"
            elif self.platform == Platform.WINDOWS:
                step.fix_command = "curl is included in Windows 10+ by default"

        return step

    def check_docker_installed(self) -> SetupStep:
        """Check if Docker is installed.

        Returns:
            SetupStep with result
        """
        step = SetupStep(
            name="Docker (Optional)",
            description="Checking Docker installation",
        )

        docker_path = shutil.which("docker")

        if docker_path:
            success, version, _ = self._run_command(["docker", "--version"])
            if success:
                step.status = SetupStatus.SUCCESS
            else:
                step.status = SetupStatus.SKIPPED
                step.error_message = "Docker found but not working"
        else:
            step.status = SetupStatus.SKIPPED
            step.error_message = "Docker not found (optional for container deployment)"

            if self.platform == Platform.MACOS:
                step.fix_command = "Install Docker Desktop from https://docker.com"
            elif self.platform == Platform.LINUX:
                step.fix_command = "curl -fsSL https://get.docker.com | sh"
            elif self.platform == Platform.WINDOWS:
                step.fix_command = "Install Docker Desktop from https://docker.com"

        return step

    def check_ollama_installed(self) -> SetupStep:
        """Check if Ollama is installed.

        Returns:
            SetupStep with result
        """
        step = SetupStep(
            name="Ollama",
            description="Checking Ollama installation",
        )

        ollama_path = shutil.which("ollama")

        if ollama_path:
            success, version, _ = self._run_command(["ollama", "--version"])
            if success:
                step.status = SetupStatus.SUCCESS
            else:
                step.status = SetupStatus.FAILED
                step.error_message = "Ollama found but version check failed"
        else:
            step.status = SetupStatus.FAILED
            step.error_message = "Ollama not found"

            if self.platform == Platform.MACOS:
                step.fix_command = "brew install ollama  # or download from ollama.ai"
            elif self.platform == Platform.LINUX:
                step.fix_command = "curl https://ollama.ai/install.sh | sh"
            elif self.platform == Platform.WINDOWS:
                step.fix_command = "Download installer from https://ollama.ai/"

        return step

    def check_ollama_running(self) -> SetupStep:
        """Check if Ollama service is running.

        Returns:
            SetupStep with result
        """
        step = SetupStep(
            name="Ollama Service",
            description="Checking if Ollama is running",
        )

        if not shutil.which("ollama"):
            step.status = SetupStatus.SKIPPED
            step.error_message = "Ollama not installed"
            return step

        success, stdout, stderr = self._run_command(["ollama", "list"], timeout=5)

        if success:
            step.status = SetupStatus.SUCCESS
        else:
            step.status = SetupStatus.FAILED
            step.error_message = "Ollama not responding"

            if self.platform == Platform.MACOS:
                step.fix_command = "ollama serve  # Run in background"
            elif self.platform == Platform.LINUX:
                step.fix_command = (
                    "systemctl start ollama  # or: ollama serve (in background)"
                )
            elif self.platform == Platform.WINDOWS:
                step.fix_command = "ollama serve  # Run in separate terminal"

        return step

    def install_pdf_libraries(self) -> SetupStep:
        """Install PDF libraries for the current platform.

        Returns:
            SetupStep with result
        """
        step = SetupStep(
            name="PDF Libraries",
            description="Installing PDF support libraries",
        )

        # Check if already installed
        try:
            import pypdf  # type: ignore

            step.status = SetupStatus.SUCCESS
            step.error_message = "Already installed"
            return step
        except ImportError:
            pass

        if not self.auto_install:
            install = Confirm.ask(
                "Install PDF libraries (pypdf) for document support?",
                default=True,
                console=self.console,
            )
            if not install:
                step.status = SetupStatus.SKIPPED
                step.error_message = "User declined installation"
                return step

        # Install using pip
        success, stdout, stderr = self._run_command(
            [sys.executable, "-m", "pip", "install", "pypdf", "-q"],
            timeout=60,
        )

        if success:
            step.status = SetupStatus.SUCCESS
        else:
            step.status = SetupStatus.FAILED
            step.error_message = f"Installation failed: {stderr}"
            step.fix_command = "pip install pypdf"

        return step

    def pull_required_models(
        self, models: Optional[List[str]] = None
    ) -> SetupStep:
        """Pull required Ollama models.

        Args:
            models: List of models to pull (uses defaults if None)

        Returns:
            SetupStep with result
        """
        step = SetupStep(
            name="Ollama Models",
            description="Pulling required models",
        )

        if models is None:
            models = ["qwen2.5-coder:7b"]  # Start with smaller default model

        if not shutil.which("ollama"):
            step.status = SetupStatus.SKIPPED
            step.error_message = "Ollama not installed"
            return step

        # Check if Ollama is running
        success, _, _ = self._run_command(["ollama", "list"], timeout=5)
        if not success:
            step.status = SetupStatus.FAILED
            step.error_message = "Ollama service not running"
            step.fix_command = "ollama serve"
            return step

        # Get list of installed models
        success, stdout, _ = self._run_command(["ollama", "list"])
        if not success:
            step.status = SetupStatus.FAILED
            step.error_message = "Could not list models"
            return step

        installed_models = [
            line.split()[0] for line in stdout.split("\n")[1:] if line.strip()
        ]

        # Check which models need to be pulled
        missing_models = [m for m in models if m not in installed_models]

        if not missing_models:
            step.status = SetupStatus.SUCCESS
            step.error_message = f"All {len(models)} model(s) already available"
            return step

        if not self.auto_install:
            install = Confirm.ask(
                f"Pull {len(missing_models)} missing model(s): {', '.join(missing_models)}?",
                default=True,
                console=self.console,
            )
            if not install:
                step.status = SetupStatus.SKIPPED
                step.error_message = "User declined model installation"
                return step

        # Pull each missing model
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            for model in missing_models:
                task = progress.add_task(f"Pulling {model}...", total=None)

                success, stdout, stderr = self._run_command(
                    ["ollama", "pull", model],
                    timeout=3600,  # 1 hour for large models
                )

                progress.remove_task(task)

                if not success:
                    step.status = SetupStatus.FAILED
                    step.error_message = f"Failed to pull {model}: {stderr}"
                    return step

        step.status = SetupStatus.SUCCESS
        return step

    def run_full_setup(
        self, required_models: Optional[List[str]] = None
    ) -> Tuple[bool, List[SetupStep]]:
        """Run full setup process.

        Args:
            required_models: List of models to install

        Returns:
            Tuple of (success, steps)
        """
        self.steps = []

        self.console.print(
            Panel(
                f"[bold cyan]Hrisa Code Setup[/bold cyan]\n"
                f"Platform: {self.platform.value}\n"
                f"Mode: {'Auto-install' if self.auto_install else 'Interactive'}",
                title="Setup Manager",
            )
        )

        # System dependency checks
        self.console.print("\n[bold]Step 1: System Dependencies[/bold]")
        self.steps.append(self.check_python_version())
        self._display_step(self.steps[-1])

        self.steps.append(self.check_git_installed())
        self._display_step(self.steps[-1])

        self.steps.append(self.check_curl_installed())
        self._display_step(self.steps[-1])

        self.steps.append(self.check_docker_installed())
        self._display_step(self.steps[-1])

        # Ollama checks
        self.console.print("\n[bold]Step 2: Ollama Setup[/bold]")
        self.steps.append(self.check_ollama_installed())
        self._display_step(self.steps[-1])

        if self.steps[-1].status == SetupStatus.SUCCESS:
            self.steps.append(self.check_ollama_running())
            self._display_step(self.steps[-1])

        # Optional libraries
        self.console.print("\n[bold]Step 3: Optional Libraries[/bold]")
        self.steps.append(self.install_pdf_libraries())
        self._display_step(self.steps[-1])

        # Pull models if Ollama is running
        if any(
            s.name == "Ollama Service" and s.status == SetupStatus.SUCCESS
            for s in self.steps
        ):
            self.console.print("\n[bold]Step 4: Ollama Models[/bold]")
            self.steps.append(self.pull_required_models(required_models))
            self._display_step(self.steps[-1])

        # Determine overall success
        critical_failed = any(
            s.status == SetupStatus.FAILED
            for s in self.steps
            if s.name in ["Python Version", "Ollama", "Ollama Service"]
        )

        return not critical_failed, self.steps

    def _display_step(self, step: SetupStep) -> None:
        """Display a setup step result.

        Args:
            step: Setup step to display
        """
        status_icons = {
            SetupStatus.SUCCESS: "[green]✓[/green]",
            SetupStatus.FAILED: "[red]✗[/red]",
            SetupStatus.SKIPPED: "[yellow]○[/yellow]",
            SetupStatus.PENDING: "[dim]...[/dim]",
            SetupStatus.IN_PROGRESS: "[cyan]⟳[/cyan]",
        }

        icon = status_icons[step.status]
        message = f"  {icon} {step.name}"

        if step.error_message:
            message += f" - {step.error_message}"

        self.console.print(message)

        if step.fix_command and step.status == SetupStatus.FAILED:
            self.console.print(f"    [dim]Fix: {step.fix_command}[/dim]")

    def display_summary(self, steps: Optional[List[SetupStep]] = None) -> None:
        """Display summary table of setup results.

        Args:
            steps: List of setup steps (uses self.steps if None)
        """
        steps = steps or self.steps

        table = Table(title="Setup Summary", show_header=True)
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Notes", style="dim")

        status_styles = {
            SetupStatus.SUCCESS: "[green]✓ Success[/green]",
            SetupStatus.FAILED: "[red]✗ Failed[/red]",
            SetupStatus.SKIPPED: "[yellow]○ Skipped[/yellow]",
            SetupStatus.PENDING: "[dim]Pending[/dim]",
        }

        for step in steps:
            table.add_row(
                step.name,
                status_styles.get(step.status, str(step.status)),
                step.error_message or "",
            )

        self.console.print("\n")
        self.console.print(table)

        # Show critical failures
        critical_failures = [
            s
            for s in steps
            if s.status == SetupStatus.FAILED
            and s.name in ["Python Version", "Ollama", "Ollama Service"]
        ]

        if critical_failures:
            self.console.print(
                "\n[bold red]Critical components failed. Please fix before proceeding.[/bold red]"
            )
            for failure in critical_failures:
                if failure.fix_command:
                    self.console.print(
                        f"  [cyan]{failure.name}:[/cyan] {failure.fix_command}"
                    )
        else:
            self.console.print(
                "\n[bold green]Setup complete! Hrisa Code is ready to use.[/bold green]"
            )
            self.console.print(
                "\n[cyan]Next steps:[/cyan]\n"
                "  1. Run [bold]hrisa init[/bold] to generate configuration\n"
                "  2. Run [bold]hrisa chat[/bold] to start coding assistant\n"
                "  3. See [bold]hrisa --help[/bold] for all commands"
            )


def run_setup(
    auto_install: bool = False, required_models: Optional[List[str]] = None
) -> bool:
    """Run the setup wizard.

    Args:
        auto_install: Automatically install dependencies
        required_models: List of models to install

    Returns:
        True if setup succeeded, False otherwise
    """
    manager = SetupManager(auto_install=auto_install)
    success, steps = manager.run_full_setup(required_models)
    manager.display_summary(steps)
    return success
