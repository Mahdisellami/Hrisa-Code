"""Interactive chat session handler."""

import asyncio
from pathlib import Path
from typing import Optional
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from rich.console import Console
from rich.panel import Panel

from hrisa_code.core.conversation import ConversationManager
from hrisa_code.core.ollama_client import OllamaConfig
from hrisa_code.core.config import Config
from hrisa_code.core.repo_context import RepoContext
from hrisa_code.core.task_manager import TaskManager
from rich.columns import Columns


def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate Levenshtein distance between two strings.

    Args:
        s1: First string
        s2: Second string

    Returns:
        Edit distance between strings
    """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def is_exit_command(user_input: str) -> bool:
    """Check if user input is an exit-like command (with typo tolerance).

    Args:
        user_input: User's input string

    Returns:
        True if input looks like an exit command
    """
    user_input = user_input.strip().lower()

    # Exact matches for common exit synonyms
    exit_synonyms = {"exit", "quit", "q", "bye", "leave", "close", "stop"}
    if user_input in exit_synonyms:
        return True

    # Check for typos with edit distance <= 2
    for synonym in exit_synonyms:
        if len(user_input) > 1 and levenshtein_distance(user_input, synonym) <= 2:
            return True

    return False


class InteractiveSession:
    """Manages an interactive chat session."""

    def __init__(
        self,
        config: Config,
        working_directory: Path,
    ):
        """Initialize the interactive session.

        Args:
            config: Application configuration
            working_directory: Working directory for operations
        """
        self.config = config
        self.working_directory = working_directory
        self.console = Console()

        # Set up Ollama configuration
        ollama_config = OllamaConfig(
            model=config.model.name,
            host=config.ollama.host,
            temperature=config.model.temperature,
            top_p=config.model.top_p,
            top_k=config.model.top_k,
        )

        # Set up task manager for background tasks
        self.task_manager = TaskManager(working_directory)

        # Create conversation manager (needed for RepoContext)
        self.conversation = ConversationManager(
            ollama_config=ollama_config,
            working_directory=working_directory,
            system_prompt=config.system_prompt,
            enable_tools=config.tools.enabled,
            task_manager=self.task_manager,
        )

        # Set up repo context with ollama client
        self.repo_context = RepoContext(working_directory, self.conversation.ollama_client)

        # Load HRISA.md if it exists and augment system prompt
        hrisa_content = self.repo_context.load()
        if hrisa_content:
            if config.system_prompt:
                self.conversation.system_prompt += f"\n\n## Repository Context\n\n{hrisa_content}"
            else:
                self.conversation.system_prompt = f"## Repository Context\n\n{hrisa_content}"

        # Set up prompt session with history
        history_file = Path.home() / ".hrisa" / "history.txt"
        history_file.parent.mkdir(exist_ok=True)

        self.prompt_session: PromptSession[str] = PromptSession(
            history=FileHistory(str(history_file)),
            auto_suggest=AutoSuggestFromHistory(),
        )

    def _display_welcome(self) -> None:
        """Display welcome message with ASCII art."""
        hrisa_status = (
            "[green]HRISA.md loaded[/green]"
            if self.repo_context.exists()
            else "[yellow]No HRISA.md (use /init to create)[/yellow]"
        )

        # ASCII art - simple and clean
        ascii_art = """
  [bold red]██╗  ██╗██████╗ ██╗███████╗ █████╗[/bold red]
  [bold red]██║  ██║██╔══██╗██║██╔════╝██╔══██╗[/bold red]
  [bold red]███████║██████╔╝██║███████╗███████║[/bold red]
  [bold red]██╔══██║██╔══██╗██║╚════██║██╔══██║[/bold red]
  [bold red]██║  ██║██║  ██║██║███████║██║  ██║[/bold red]
  [bold red]╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚══════╝╚═╝  ╚═╝[/bold red]

     [dim]Local AI Coding Assistant[/dim]
"""

        info_text = (
            f"\n[bold]Configuration[/bold]\n"
            f"  Model: [green]{self.config.model.name}[/green]\n"
            f"  Directory: [cyan]{self.working_directory.name}/[/cyan]\n"
            f"  Context: {hrisa_status}\n\n"
            f"[bold]Quick Commands[/bold]\n"
            f"  [yellow]/help[/yellow]    - Show all commands\n"
            f"  [yellow]/init[/yellow]    - Initialize repo context\n"
            f"  [yellow]/clear[/yellow]   - Clear history\n"
            f"  [yellow]/exit[/yellow]    - Exit (or Ctrl+D)\n"
        )

        # Create columns layout - ASCII art on left, info panel on right
        info_panel = Panel.fit(info_text, border_style="red", padding=(0, 2))

        self.console.print()
        self.console.print(Columns([ascii_art, info_panel], equal=False, expand=False))
        self.console.print()

    async def _handle_command(self, command: str) -> bool:
        """Handle special commands.

        Args:
            command: The command to handle

        Returns:
            True if should continue, False if should exit
        """
        command_lower = command.strip().lower()

        if command_lower in ["/exit", "/quit", "/q"]:
            self.console.print("[yellow]Goodbye![/yellow]")
            return False

        elif command_lower == "/help":
            self.console.print(
                Panel(
                    "[bold]Available Commands:[/bold]\n\n"
                    "[yellow]/help[/yellow]      - Show this help message\n"
                    "[yellow]/init[/yellow]      - Initialize or update HRISA.md (repo context)\n"
                    "[yellow]/clear[/yellow]     - Clear conversation history\n"
                    "[yellow]/save[/yellow]      - Save conversation to file\n"
                    "[yellow]/load[/yellow]      - Load conversation from file\n"
                    "[yellow]/config[/yellow]    - Show current configuration\n"
                    "[yellow]/tasks[/yellow]     - List background tasks\n"
                    "[yellow]/task <id>[/yellow] - Show task output\n"
                    "[yellow]/task kill <id>[/yellow] - Kill a task\n"
                    "[yellow]/exit[/yellow]      - Exit the session",
                    title="Help",
                )
            )

        elif command_lower == "/init" or command_lower.startswith("/init "):
            # Initialize or update HRISA.md
            force = "--force" in command_lower or "-f" in command_lower
            self.console.print("\n[bold blue]Initializing repository context...[/bold blue]\n")
            await self.repo_context.inspect_and_generate(force=force)

        elif command_lower == "/clear":
            self.conversation.clear_history()

        elif command_lower == "/save":
            filename = f"conversation_{asyncio.get_event_loop().time():.0f}.json"
            save_path = self.working_directory / filename
            self.conversation.save_conversation(save_path)

        elif command_lower == "/config":
            self.console.print(
                Panel(
                    f"[bold]Current Configuration:[/bold]\n\n"
                    f"Model: [green]{self.config.model.name}[/green]\n"
                    f"Temperature: {self.config.model.temperature}\n"
                    f"Ollama Host: {self.config.ollama.host}\n"
                    f"Working Dir: [cyan]{self.working_directory}[/cyan]",
                    title="Configuration",
                )
            )

        elif command_lower == "/tasks":
            # List all background tasks
            self.task_manager.display_tasks()

        elif command_lower.startswith("/task "):
            # Handle task-specific commands
            parts = command_lower.split()
            if len(parts) == 2:
                # /task <id> - show task output
                task_id = parts[1]
                self.task_manager.display_task_output(task_id)
            elif len(parts) == 3 and parts[1] == "kill":
                # /task kill <id> - kill task
                task_id = parts[2]
                if self.task_manager.kill_task(task_id):
                    self.console.print(f"[green]Task '{task_id}' killed[/green]")
                else:
                    self.console.print(f"[red]Failed to kill task '{task_id}'[/red]")
            else:
                self.console.print("[red]Invalid /task command[/red]")
                self.console.print("Usage: [yellow]/task <id>[/yellow] or [yellow]/task kill <id>[/yellow]")

        else:
            self.console.print(f"[red]Unknown command: {command_lower}[/red]")
            self.console.print("Type [yellow]/help[/yellow] for available commands")

        return True

    async def run(self) -> None:
        """Run the interactive session."""
        self._display_welcome()

        while True:
            try:
                # Get user input
                user_input = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.prompt_session.prompt("\n> ")
                )

                if not user_input.strip():
                    continue

                # Check for exit-like commands (even without "/")
                if is_exit_command(user_input):
                    self.console.print("[yellow]Goodbye![/yellow]")
                    break

                # Handle commands
                if user_input.startswith("/"):
                    if not await self._handle_command(user_input):
                        break
                    continue

                # Process message
                self.console.print()
                await self.conversation.process_message_stream(user_input)

            except (EOFError, KeyboardInterrupt):
                self.console.print("\n[yellow]Goodbye![/yellow]")
                break
            except Exception as e:
                self.console.print(f"\n[red]Error: {str(e)}[/red]")
                self.console.print("[yellow]Type /help for available commands[/yellow]")
