"""Pre-flight checks for Hrisa Code dependencies and requirements."""

import platform
import shutil
import subprocess
import sys
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from rich.console import Console
from rich.panel import Panel
from rich.table import Table


class CheckStatus(Enum):
    """Status of a pre-flight check."""

    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    SKIP = "skip"


@dataclass
class CheckResult:
    """Result of a pre-flight check."""

    name: str
    status: CheckStatus
    message: str
    details: Optional[str] = None
    fix_command: Optional[str] = None


class PreflightChecker:
    """Comprehensive pre-flight checks for Hrisa Code."""

    def __init__(self, console: Optional[Console] = None, auto_fix: bool = False):
        """Initialize the preflight checker.

        Args:
            console: Rich console for output (creates new one if None)
            auto_fix: Automatically attempt to fix issues if possible
        """
        self.console = console or Console()
        self.auto_fix = auto_fix
        self.results: List[CheckResult] = []

    def check_python_version(self) -> CheckResult:
        """Check if Python version meets requirements."""
        version = sys.version_info
        required = (3, 10)

        if version >= required:
            return CheckResult(
                name="Python Version",
                status=CheckStatus.PASS,
                message=f"Python {version.major}.{version.minor}.{version.micro}",
            )
        else:
            return CheckResult(
                name="Python Version",
                status=CheckStatus.FAIL,
                message=f"Python {version.major}.{version.minor} < 3.10",
                details="Hrisa Code requires Python 3.10 or higher",
            )

    def check_ollama_installed(self) -> CheckResult:
        """Check if Ollama is installed."""
        ollama_path = shutil.which("ollama")

        if ollama_path:
            try:
                result = subprocess.run(
                    ["ollama", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                version = result.stdout.strip() if result.returncode == 0 else "unknown"
                return CheckResult(
                    name="Ollama Installation",
                    status=CheckStatus.PASS,
                    message=f"Installed at {ollama_path}",
                    details=f"Version: {version}",
                )
            except Exception as e:
                return CheckResult(
                    name="Ollama Installation",
                    status=CheckStatus.WARN,
                    message="Installed but version check failed",
                    details=str(e),
                )
        else:
            return CheckResult(
                name="Ollama Installation",
                status=CheckStatus.FAIL,
                message="Ollama not found",
                details="Install from https://ollama.ai/",
                fix_command="Visit https://ollama.ai/ for installation instructions",
            )

    def check_ollama_running(self) -> CheckResult:
        """Check if Ollama service is running."""
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                models = [
                    line.split()[0]
                    for line in result.stdout.strip().split("\n")[1:]
                    if line.strip()
                ]
                return CheckResult(
                    name="Ollama Service",
                    status=CheckStatus.PASS,
                    message="Running",
                    details=f"Found {len(models)} model(s)",
                )
            else:
                return CheckResult(
                    name="Ollama Service",
                    status=CheckStatus.FAIL,
                    message="Not responding",
                    details=result.stderr.strip(),
                    fix_command="ollama serve",
                )
        except subprocess.TimeoutExpired:
            return CheckResult(
                name="Ollama Service",
                status=CheckStatus.FAIL,
                message="Timeout",
                details="Ollama service not responding",
                fix_command="ollama serve",
            )
        except FileNotFoundError:
            return CheckResult(
                name="Ollama Service",
                status=CheckStatus.SKIP,
                message="Skipped",
                details="Ollama not installed",
            )
        except Exception as e:
            return CheckResult(
                name="Ollama Service",
                status=CheckStatus.WARN,
                message="Check failed",
                details=str(e),
            )

    def check_required_models(
        self, required_models: Optional[List[str]] = None
    ) -> CheckResult:
        """Check if required models are available.

        Args:
            required_models: List of model names to check (checks common models if None)
        """
        if required_models is None:
            # Default models to check
            required_models = ["qwen2.5-coder:32b", "qwen2.5:72b"]

        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode != 0:
                return CheckResult(
                    name="Required Models",
                    status=CheckStatus.SKIP,
                    message="Skipped",
                    details="Could not list models",
                )

            available_models = [
                line.split()[0]
                for line in result.stdout.strip().split("\n")[1:]
                if line.strip()
            ]

            missing = [m for m in required_models if m not in available_models]

            if not missing:
                return CheckResult(
                    name="Required Models",
                    status=CheckStatus.PASS,
                    message=f"All {len(required_models)} model(s) available",
                    details=", ".join(required_models),
                )
            else:
                fix_commands = [f"ollama pull {m}" for m in missing]
                return CheckResult(
                    name="Required Models",
                    status=CheckStatus.WARN,
                    message=f"{len(missing)} model(s) missing",
                    details=f"Missing: {', '.join(missing)}",
                    fix_command="\n".join(fix_commands),
                )
        except FileNotFoundError:
            return CheckResult(
                name="Required Models",
                status=CheckStatus.SKIP,
                message="Skipped",
                details="Ollama not installed",
            )
        except Exception as e:
            return CheckResult(
                name="Required Models",
                status=CheckStatus.WARN,
                message="Check failed",
                details=str(e),
            )

    def check_pdf_libraries(self) -> CheckResult:
        """Check for PDF library availability."""
        pdf_libraries = []
        system = platform.system()

        # Try to import common PDF libraries
        try:
            import PyPDF2  # type: ignore

            pdf_libraries.append("PyPDF2")
        except ImportError:
            pass

        try:
            import pdfplumber  # type: ignore

            pdf_libraries.append("pdfplumber")
        except ImportError:
            pass

        try:
            import pypdf  # type: ignore

            pdf_libraries.append("pypdf")
        except ImportError:
            pass

        if pdf_libraries:
            return CheckResult(
                name="PDF Libraries",
                status=CheckStatus.PASS,
                message=f"Found {len(pdf_libraries)} library(ies)",
                details=", ".join(pdf_libraries),
            )
        else:
            return CheckResult(
                name="PDF Libraries",
                status=CheckStatus.WARN,
                message="No PDF libraries found",
                details=f"Optional for PDF support on {system}",
                fix_command="pip install pypdf",
            )

    def check_git_available(self) -> CheckResult:
        """Check if git is available for version control operations."""
        git_path = shutil.which("git")

        if git_path:
            try:
                result = subprocess.run(
                    ["git", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                version = result.stdout.strip() if result.returncode == 0 else "unknown"
                return CheckResult(
                    name="Git",
                    status=CheckStatus.PASS,
                    message=f"Installed at {git_path}",
                    details=version,
                )
            except Exception as e:
                return CheckResult(
                    name="Git",
                    status=CheckStatus.WARN,
                    message="Installed but version check failed",
                    details=str(e),
                )
        else:
            return CheckResult(
                name="Git",
                status=CheckStatus.WARN,
                message="Not found",
                details="Git operations will not be available",
                fix_command="Install git from https://git-scm.com/",
            )

    def run_all_checks(
        self, required_models: Optional[List[str]] = None
    ) -> Tuple[bool, List[CheckResult]]:
        """Run all pre-flight checks.

        Args:
            required_models: List of model names to check

        Returns:
            Tuple of (all_passed, results)
        """
        self.results = []

        # Core checks
        self.results.append(self.check_python_version())
        self.results.append(self.check_ollama_installed())
        self.results.append(self.check_ollama_running())
        self.results.append(self.check_required_models(required_models))

        # Optional checks
        self.results.append(self.check_git_available())
        self.results.append(self.check_pdf_libraries())

        # Determine if all critical checks passed
        critical_failed = any(
            r.status == CheckStatus.FAIL
            for r in self.results
            if r.name in ["Python Version", "Ollama Installation", "Ollama Service"]
        )

        return not critical_failed, self.results

    def display_results(self, results: Optional[List[CheckResult]] = None) -> None:
        """Display check results in a formatted table.

        Args:
            results: List of check results (uses self.results if None)
        """
        results = results or self.results

        table = Table(title="Pre-flight Check Results", show_header=True)
        table.add_column("Check", style="cyan", no_wrap=True)
        table.add_column("Status", style="bold")
        table.add_column("Message", style="white")
        table.add_column("Details", style="dim")

        status_styles = {
            CheckStatus.PASS: "[green]✓ PASS[/green]",
            CheckStatus.WARN: "[yellow]⚠ WARN[/yellow]",
            CheckStatus.FAIL: "[red]✗ FAIL[/red]",
            CheckStatus.SKIP: "[dim]○ SKIP[/dim]",
        }

        for result in results:
            table.add_row(
                result.name,
                status_styles[result.status],
                result.message,
                result.details or "",
            )

        self.console.print(table)

        # Show fix commands for failed/warned checks
        fixes = [r for r in results if r.fix_command and r.status != CheckStatus.PASS]
        if fixes:
            self.console.print("\n[bold yellow]Suggested Fixes:[/bold yellow]")
            for fix in fixes:
                self.console.print(f"  [cyan]{fix.name}:[/cyan] {fix.fix_command}")

    def auto_fix_issues(self, results: Optional[List[CheckResult]] = None) -> None:
        """Attempt to automatically fix issues.

        Args:
            results: List of check results (uses self.results if None)
        """
        results = results or self.results

        fixable = [
            r
            for r in results
            if r.fix_command
            and r.status in [CheckStatus.FAIL, CheckStatus.WARN]
            and r.name == "Required Models"
        ]

        if not fixable:
            self.console.print("[green]No auto-fixable issues found[/green]")
            return

        for result in fixable:
            self.console.print(
                f"\n[bold]Attempting to fix: {result.name}[/bold]"
            )
            if result.name == "Required Models" and result.fix_command:
                for cmd in result.fix_command.split("\n"):
                    self.console.print(f"  Running: {cmd}")
                    try:
                        subprocess.run(
                            cmd.split(),
                            check=True,
                            capture_output=False,
                        )
                        self.console.print(f"  [green]✓ Fixed[/green]")
                    except subprocess.CalledProcessError as e:
                        self.console.print(f"  [red]✗ Failed: {e}[/red]")


def run_preflight_checks(
    auto_fix: bool = False,
    required_models: Optional[List[str]] = None,
    display: bool = True,
) -> bool:
    """Run pre-flight checks and optionally display results.

    Args:
        auto_fix: Automatically attempt to fix issues
        required_models: List of model names to check
        display: Display results in console

    Returns:
        True if all critical checks passed, False otherwise
    """
    checker = PreflightChecker(auto_fix=auto_fix)
    all_passed, results = checker.run_all_checks(required_models)

    if display:
        checker.display_results(results)

        if not all_passed:
            Console().print(
                "\n[bold red]Critical checks failed. Please fix issues before proceeding.[/bold red]"
            )
        else:
            Console().print(
                "\n[bold green]All critical checks passed! Hrisa Code is ready.[/bold green]"
            )

    if auto_fix:
        checker.auto_fix_issues(results)

    return all_passed
