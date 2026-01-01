"""Interactive chat session handler."""

import asyncio
from pathlib import Path
from typing import Optional, Callable
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import HTML
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from hrisa_code.core.conversation import ConversationManager
from hrisa_code.core.conversation import OllamaConfig
from hrisa_code.core.config import Config
from hrisa_code.core.memory import RepoContext
from hrisa_code.core.memory import TaskManager
from hrisa_code.core.planning import AgentLoop
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

        # Set up agent for autonomous task execution
        self.agent = AgentLoop(
            conversation_manager=self.conversation,
            max_iterations=10,
            enable_reflection=True,
            enable_planning=True,
        )

        # Execution mode: "normal", "agent", "plan"
        self.execution_mode = "normal"

        # Mode display names and colors
        self.mode_styles = {
            "normal": ("normal", "dim"),
            "agent": ("agent", "cyan"),
            "plan": ("plan", "magenta"),
        }

        # Load HRISA.md if it exists and augment system prompt
        hrisa_content = self.repo_context.load()
        if hrisa_content:
            if config.system_prompt:
                self.conversation.system_prompt += f"\n\n## Repository Context\n\n{hrisa_content}"
            else:
                self.conversation.system_prompt = f"## Repository Context\n\n{hrisa_content}"

        # Set up prompt session with history (project-local)
        history_file = working_directory / ".hrisa" / "history.txt"
        history_file.parent.mkdir(parents=True, exist_ok=True)

        # Set up key bindings for mode cycling
        kb = KeyBindings()

        @kb.add('s-tab')  # SHIFT+TAB
        def _(event):
            """Cycle execution modes with SHIFT+TAB."""
            # Cycle through modes
            mode_cycle = {"normal": "agent", "agent": "plan", "plan": "normal"}
            self.execution_mode = mode_cycle[self.execution_mode]

            # Show mode change feedback
            mode_info = {
                "normal": ("Normal Mode", "yellow"),
                "agent": ("Agent Mode", "cyan"),
                "plan": ("Plan Mode", "magenta")
            }
            title, color = mode_info[self.execution_mode]

            # Print feedback above the prompt
            self.console.print()
            self.console.print(f"[{color}]► Switched to {title}[/{color}]")

        self.prompt_session: PromptSession[str] = PromptSession(
            history=FileHistory(str(history_file)),
            auto_suggest=AutoSuggestFromHistory(),
            key_bindings=kb,
            bottom_toolbar=self._get_bottom_toolbar,
        )

    def _get_prompt(self) -> HTML:
        """Get the prompt with mode indicator.

        Returns:
            HTML formatted prompt that updates dynamically
        """
        mode_name, mode_color = self.mode_styles[self.execution_mode]
        if self.execution_mode == "normal":
            # Normal mode: simple prompt
            return HTML("\n> ")
        else:
            # Agent/Plan mode: show mode in brackets with color
            # Using prompt_toolkit HTML formatting for proper color support
            return HTML(f"\n<{mode_color}>[{mode_name}]</{mode_color}> > ")

    def _get_bottom_toolbar(self) -> HTML:
        """Get the bottom toolbar showing current mode.

        This function is called by prompt_toolkit on every render,
        providing a persistent status bar at the bottom of the screen.

        Returns:
            HTML formatted toolbar text
        """
        mode_name, mode_color = self.mode_styles[self.execution_mode]

        # Format: " Mode: [agent] " with appropriate color
        if self.execution_mode == "normal":
            return HTML(f" <b>Mode:</b> {mode_name} ")
        else:
            return HTML(f" <b>Mode:</b> <{mode_color}><b>{mode_name}</b></{mode_color}> ")

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

        # Mode display with color coding
        mode_display = {
            "normal": "[dim]normal[/dim]",
            "agent": "[cyan]agent[/cyan]",
            "plan": "[magenta]plan[/magenta]"
        }

        info_text = (
            f"\n[bold]Configuration[/bold]\n"
            f"  Model: [green]{self.config.model.name}[/green]\n"
            f"  Directory: [cyan]{self.working_directory.name}/[/cyan]\n"
            f"  Context: {hrisa_status}\n"
            f"  Mode: {mode_display[self.execution_mode]}\n\n"
            f"[bold]Quick Commands[/bold]\n"
            f"  [yellow]/help[/yellow]    - Show all commands\n"
            f"  [yellow]/agent[/yellow]   - Cycle mode (normal → agent → plan)\n"
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
            mode_display = {
                "normal": "[yellow]normal[/yellow]",
                "agent": "[cyan]agent[/cyan]",
                "plan": "[magenta]plan[/magenta]"
            }
            current_mode_display = mode_display[self.execution_mode]

            self.console.print(
                Panel(
                    "[bold]Available Commands:[/bold]\n\n"
                    "[yellow]/help[/yellow]      - Show this help message\n"
                    "[yellow]/init[/yellow]      - Initialize or update HRISA.md (repo context)\n"
                    "[yellow]/agent[/yellow]     - Cycle execution mode (normal → agent → plan)\n"
                    f"                Current mode: {current_mode_display}\n"
                    "                [dim]normal: standard chat | agent: autonomous | plan: intelligent planning[/dim]\n"
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

        elif command_lower == "/agent":
            # Cycle through execution modes: normal → agent → plan → normal
            mode_cycle = {"normal": "agent", "agent": "plan", "plan": "normal"}
            next_mode = mode_cycle[self.execution_mode]

            # For Plan Mode, require confirmation to prevent accidental activation
            if next_mode == "plan":
                self.console.print()
                self.console.print(
                    Panel(
                        "[bold magenta]⚠ Entering Plan Mode[/bold magenta]\n\n"
                        "Plan Mode generates a multi-step execution plan for your next task.\n\n"
                        "[bold]The system will:[/bold]\n"
                        "  1. Analyze task complexity (SIMPLE/MODERATE/COMPLEX)\n"
                        "  2. Generate 4-15 step execution plan\n"
                        "  3. Execute each step with visual progress\n"
                        "  4. Use previous step results to avoid redundancy\n\n"
                        "[dim]This is the recommended mode for complex multi-feature tasks.[/dim]",
                        title="Plan Mode Activation",
                        border_style="magenta",
                        padding=(1, 2),
                    )
                )
                self.console.print()

                # Ask for confirmation
                confirm = self.prompt_session.prompt(
                    HTML("<b>Enter Plan Mode?</b> (y/n): "),
                    default="y"
                )

                if confirm.lower() not in ["y", "yes"]:
                    self.console.print("[yellow]Staying in current mode.[/yellow]")
                    return True

                # Show large confirmation banner
                self.console.print()
                self.console.print(
                    Panel(
                        "[bold magenta]YOU ARE NOW IN PLAN MODE[/bold magenta]\n\n"
                        "Your next task will be planned and executed step-by-step.\n"
                        "Watch the bottom toolbar for persistent mode indicator.",
                        border_style="magenta",
                        padding=(1, 2),
                        title="✓ Plan Mode Active",
                    )
                )
                self.console.print()

            # Set the mode
            self.execution_mode = next_mode

            # Mode-specific descriptions
            mode_info = {
                "normal": {
                    "title": "Normal Mode",
                    "color": "yellow",
                    "description": "[yellow]Standard interactive mode[/yellow]\n\n"
                                 "Standard conversation with the LLM.\n"
                                 "Tools are available but no autonomous behavior.\n\n"
                                 "[dim]Use /agent to switch to agent mode[/dim]"
                },
                "agent": {
                    "title": "Agent Mode",
                    "color": "cyan",
                    "description": "[cyan]Autonomous multi-step execution[/cyan]\n\n"
                                 "Your next message will be executed autonomously.\n"
                                 "The agent will:\n"
                                 "  • Break down complex tasks automatically\n"
                                 "  • Explore the codebase proactively\n"
                                 "  • Execute multiple steps until completion\n"
                                 "  • Self-reflect and adapt\n\n"
                                 "[dim]Use /agent to switch to plan mode[/dim]"
                },
                "plan": {
                    "title": "Plan Mode",
                    "color": "magenta",
                    "description": "[magenta]Plan-driven execution with progress tracking[/magenta]\n\n"
                                 "Your next message will use intelligent planning.\n"
                                 "The system will:\n"
                                 "  • Analyze task complexity\n"
                                 "  • Generate a step-by-step execution plan\n"
                                 "  • Execute steps with progress feedback\n"
                                 "  • Adapt plan based on discoveries\n\n"
                                 "[dim]Use /agent to return to normal mode[/dim]"
                }
            }

            # Skip showing panel for plan mode (already shown confirmation banner)
            if next_mode != "plan":
                info = mode_info[self.execution_mode]
                self.console.print(
                    Panel(
                        info["description"],
                        title=f"► {info['title']}",
                        border_style=info["color"],
                    )
                )

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
                # Get user input with mode-aware prompt (fetched fresh each time)
                user_input = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.prompt_session.prompt(self._get_prompt())
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

                # Execute based on current mode
                if self.execution_mode == "agent":
                    await self.agent.execute_task(user_input)
                    # Mode persists - stays in agent mode until user switches
                elif self.execution_mode == "plan":
                    await self.agent.execute_with_plan(user_input)
                    # Mode persists - stays in plan mode until user switches
                else:
                    # Normal mode - standard conversation
                    await self.conversation.process_message_stream(user_input)

            except (EOFError, KeyboardInterrupt):
                self.console.print("\n[yellow]Goodbye![/yellow]")
                break
            except Exception as e:
                self.console.print(f"\n[red]Error: {str(e)}[/red]")
                self.console.print("[yellow]Type /help for available commands[/yellow]")
