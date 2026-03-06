"""Main CLI interface for Hrisa Code."""

import asyncio
import typer
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from typing import Optional
from pathlib import Path

from hrisa_code import __version__
from hrisa_code.core.config import Config
from hrisa_code.core.interface import InteractiveSession
from hrisa_code.core.conversation import OllamaClient, OllamaConfig, ConversationManager

app = typer.Typer(
    name="hrisa",
    help="A CLI coding assistant powered by local LLMs via Ollama",
    add_completion=False,
)
console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"[bold blue]Hrisa Code[/bold blue] version [green]{__version__}[/green]")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
) -> None:
    """Hrisa Code - Your local AI coding assistant."""
    pass


@app.command()
def chat(
    model: Optional[str] = typer.Option(
        None,
        "--model",
        "-m",
        help="Ollama model to use (overrides config)",
    ),
    working_dir: Path = typer.Option(
        Path.cwd(),
        "--working-dir",
        "-w",
        help="Working directory for the assistant",
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file",
    ),
) -> None:
    """Start an interactive chat session with the coding assistant."""
    try:
        # Load configuration
        if config_file:
            config = Config.load(config_file)
        else:
            config = Config.load_with_fallback(working_dir)

        # Override model if specified
        if model:
            config.model.name = model

        # Create and run interactive session
        session = InteractiveSession(config=config, working_directory=working_dir)
        asyncio.run(session.run())

    except KeyboardInterrupt:
        console.print("\n[yellow]Session interrupted[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        console.print("\n[yellow]Make sure Ollama is running:[/yellow]")
        console.print("  ollama serve")
        raise typer.Exit(1)


@app.command()
def models(
    host: str = typer.Option(
        "http://localhost:11434",
        "--host",
        "-h",
        help="Ollama server host",
    ),
) -> None:
    """List available Ollama models."""
    try:
        config = OllamaConfig(host=host)
        client = OllamaClient(config)

        console.print("[bold]Fetching available models...[/bold]\n")
        model_list = asyncio.run(client.list_models())

        if not model_list:
            console.print("[yellow]No models found.[/yellow]")
            console.print("\nPull a model with:")
            console.print("  [cyan]ollama pull codellama[/cyan]")
        else:
            table = Table(title="Available Ollama Models")
            table.add_column("Model Name", style="green")

            for model_name in model_list:
                table.add_row(model_name)

            console.print(table)

    except Exception as e:
        console.print(f"[red]Error connecting to Ollama: {str(e)}[/red]")
        console.print("\n[yellow]Make sure Ollama is running:[/yellow]")
        console.print("  ollama serve")
        raise typer.Exit(1)


@app.command()
def check(
    auto_fix: bool = typer.Option(
        False,
        "--auto-fix",
        "-f",
        help="Automatically attempt to fix issues (e.g., pull missing models)",
    ),
    models: Optional[str] = typer.Option(
        None,
        "--models",
        "-m",
        help="Comma-separated list of required models to check",
    ),
) -> None:
    """Run pre-flight checks to verify Hrisa Code dependencies and requirements.

    Checks for:
    - Python version (3.10+)
    - Ollama installation and service status
    - Required models availability
    - Git installation (optional)
    - PDF libraries (optional)

    Example:
        hrisa check
        hrisa check --auto-fix
        hrisa check --models "qwen2.5-coder:32b,qwen2.5:72b"
    """
    from hrisa_code.core.validation import run_preflight_checks

    # Parse models list if provided
    required_models = None
    if models:
        required_models = [m.strip() for m in models.split(",")]

    # Run checks
    all_passed = run_preflight_checks(
        auto_fix=auto_fix,
        required_models=required_models,
        display=True,
    )

    if not all_passed:
        raise typer.Exit(1)


@app.command()
def setup(
    auto_install: bool = typer.Option(
        False,
        "--auto-install",
        "-y",
        help="Automatically install dependencies without prompting",
    ),
    models: Optional[str] = typer.Option(
        None,
        "--models",
        "-m",
        help="Comma-separated list of models to install",
    ),
) -> None:
    """Run the comprehensive setup wizard for Hrisa Code.

    This wizard will:
    - Check system dependencies (Python, Git, Curl, Docker)
    - Verify Ollama installation and service status
    - Install PDF libraries for document support
    - Pull required Ollama models
    - Provide platform-specific guidance for missing dependencies

    Example:
        hrisa setup                                    # Interactive setup
        hrisa setup --auto-install                     # Auto-install everything
        hrisa setup --models "qwen2.5-coder:7b"        # Specify models to install
    """
    from hrisa_code.core.validation.setup_manager import run_setup

    # Parse models list if provided
    required_models = None
    if models:
        required_models = [m.strip() for m in models.split(",")]

    # Run setup wizard
    success = run_setup(
        auto_install=auto_install,
        required_models=required_models,
    )

    if not success:
        raise typer.Exit(1)


@app.command()
def init(
    path: Path = typer.Argument(
        Path.cwd(),
        help="Directory to initialize configuration in",
    ),
    global_config: bool = typer.Option(
        False,
        "--global",
        "-g",
        help="Initialize global configuration instead of project-specific",
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        "-m",
        help="Ollama model to use for HRISA.md generation",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force overwrite without confirmation",
    ),
    comprehensive: bool = typer.Option(
        False,
        "--comprehensive",
        help="Generate comprehensive HRISA.md using multi-step orchestration",
    ),
    multi_model: bool = typer.Option(
        False,
        "--multi-model",
        help="Use multiple models for different orchestration steps (requires --comprehensive)",
    ),
    skip_hrisa: bool = typer.Option(
        False,
        "--skip-hrisa",
        help="Skip HRISA.md generation (only create config)",
    ),
) -> None:
    """Initialize Hrisa Code configuration and generate HRISA.md documentation."""
    if global_config:
        config_path = Config.get_default_config_path()
    else:
        config_path = Config.get_project_config_path(path)

    # Check if config exists
    if config_path.exists() and not force:
        console.print(f"[yellow]Configuration already exists at {config_path}[/yellow]")
        overwrite = typer.confirm("Overwrite?")
        if not overwrite:
            raise typer.Exit()

    # Create default configuration
    config = Config()

    # Override model if specified
    if model:
        config.model.name = model

    config.save(config_path)

    console.print(f"[green]Configuration initialized at {config_path}[/green]")
    console.print()

    # Generate HRISA.md if not skipped
    if not skip_hrisa:
        hrisa_path = path / "HRISA.md"

        # Check if HRISA.md exists
        if hrisa_path.exists() and not force:
            console.print(f"[yellow]HRISA.md already exists at {hrisa_path}[/yellow]")
            overwrite_hrisa = typer.confirm("Overwrite HRISA.md?")
            if not overwrite_hrisa:
                console.print("\n[bold]Next steps:[/bold]")
                console.print("1. Edit the configuration file to customize settings")
                console.print(f"2. Make sure Ollama is running: [cyan]ollama serve[/cyan]")
                console.print(f"3. Pull a model: [cyan]ollama pull {config.model.name}[/cyan]")
                console.print(f"4. Start chatting: [cyan]hrisa chat[/cyan]")
                return

        try:
            # Generate HRISA.md
            from hrisa_code.core.conversation import ConversationManager
            from hrisa_code.core.conversation import OllamaConfig
            from hrisa_code.core.orchestrators import HrisaOrchestrator

            # Create OllamaConfig from Config
            ollama_config = OllamaConfig(
                model=config.model.name,
                host=config.ollama.host,
                temperature=config.model.temperature,
                top_p=config.model.top_p,
                top_k=config.model.top_k,
            )

            if comprehensive:
                console.print("[bold cyan]Generating comprehensive HRISA.md...[/bold cyan]")
                if multi_model:
                    console.print("[dim]This will use multi-model orchestration with specialized models for each step.[/dim]\n")
                else:
                    console.print("[dim]This will use multi-step orchestration for thorough analysis.[/dim]")
                    console.print("[dim]Tip: Use --multi-model to use different models for different steps.[/dim]\n")

                # Create conversation manager for orchestration
                conversation = ConversationManager(
                    ollama_config=ollama_config,
                    system_prompt="You are an expert software architect and documentation specialist.",
                    enable_tools=True,
                    working_directory=path,
                )

                # Set up model router if multi-model is enabled
                model_router = None
                if multi_model:
                    from hrisa_code.core.model_router import ModelRouter, ModelSelectionStrategy
                    from hrisa_code.core.conversation import OllamaClient

                    # Create Ollama client to query available models
                    temp_client = OllamaClient(ollama_config)
                    available_models = asyncio.run(temp_client.list_models())

                    # Create model router with available models
                    strategy = ModelSelectionStrategy(
                        prefer_quality=True,
                        available_models=set(available_models),
                        default_model=config.model.name
                    )
                    model_router = ModelRouter(strategy=strategy)

                    console.print(f"[dim]→ Found {len(available_models)} available models[/dim]")
                    console.print()

                # Create and run orchestrator
                orchestrator = HrisaOrchestrator(
                    conversation=conversation,
                    project_path=path,
                    console=console,
                    model_router=model_router,
                    enable_multi_model=multi_model,
                )

                hrisa_content = asyncio.run(orchestrator.generate_comprehensive_hrisa())
            else:
                console.print("[bold cyan]Generating HRISA.md...[/bold cyan]")
                console.print("[dim]Tip: Use --comprehensive for thorough multi-step analysis.[/dim]\n")

                # Simple single-prompt generation
                conversation = ConversationManager(
                    ollama_config=ollama_config,
                    system_prompt="You are an expert software architect and documentation specialist.",
                    enable_tools=True,
                    working_directory=path,
                )

                prompt = f"""Generate a comprehensive HRISA.md file for this project at {path}.

HRISA.md is a repository context document that helps AI assistants understand the project structure, architecture, and development practices.

Your task:
1. Explore the codebase using available tools (read files, search, etc.)
2. Understand the project structure, components, and features
3. Generate a well-structured HRISA.md with these sections:
   - Project Overview
   - Tech Stack
   - Project Structure
   - Key Components
   - Development Practices
   - Common Tasks
   - Important Files
   - Code Patterns
   - Notes for AI Assistants
   - Version Information

Be thorough and use tools to explore the codebase before writing the documentation.
Generate the complete HRISA.md content now:"""

                hrisa_content = asyncio.run(conversation.process_message(prompt))

            # Write HRISA.md
            if hrisa_content:
                hrisa_path.write_text(hrisa_content)
                console.print(f"[green]HRISA.md created at {hrisa_path}[/green]")
            else:
                console.print("[yellow]Warning: HRISA.md generation produced no content[/yellow]")

        except Exception as e:
            # Use markup=False to prevent Rich from parsing error messages as markup
            console.print(f"[red]Error generating HRISA.md:[/red]", markup=True)
            console.print(str(e), markup=False)
            console.print("[yellow]Configuration was created successfully, but HRISA.md generation failed.[/yellow]")
            console.print("\n[yellow]Make sure Ollama is running:[/yellow]")
            console.print("  ollama serve")

    console.print("\n[bold]Next steps:[/bold]")
    console.print("1. Review the generated HRISA.md file")
    console.print("2. Edit the configuration file to customize settings")
    console.print(f"3. Make sure Ollama is running: [cyan]ollama serve[/cyan]")
    console.print(f"4. Pull a model: [cyan]ollama pull {config.model.name}[/cyan]")
    console.print(f"5. Start chatting: [cyan]hrisa chat[/cyan]")


@app.command()
def readme(
    path: Path = typer.Argument(
        Path.cwd(),
        help="Project directory to generate README for",
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        "-m",
        help="Ollama model to use for README generation",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force overwrite without confirmation",
    ),
    multi_model: bool = typer.Option(
        False,
        "--multi-model",
        help="Use multiple specialized models for different steps",
    ),
) -> None:
    """Generate user-friendly README.md documentation.

    Uses multi-step orchestration to analyze the project and generate
    comprehensive README.md documentation targeted at human users.

    The orchestrator will:
    1. Discover the project purpose and value proposition
    2. Highlight key features and benefits
    3. Determine installation requirements
    4. Create practical usage examples
    5. Synthesize comprehensive README.md

    Example:
        hrisa readme
        hrisa readme --multi-model
        hrisa readme --model qwen2.5:72b --force
    """
    # Load config (use default if not found)
    try:
        config_path = Config.get_project_config_path(path)
        if config_path.exists():
            config = Config.load(config_path)
        else:
            config = Config()
            console.print("[yellow]No config found, using defaults[/yellow]")
            console.print(f"[dim]Tip: Run 'hrisa init' to create config at {config_path}[/dim]\n")
    except Exception:
        config = Config()

    # Override model if specified
    if model:
        config.model.name = model

    readme_path = path / "README.md"

    # Check if README.md exists
    if readme_path.exists() and not force:
        console.print(f"[yellow]README.md already exists at {readme_path}[/yellow]")
        overwrite = typer.confirm("Overwrite?")
        if not overwrite:
            raise typer.Exit()

    try:
        console.print("[bold cyan]Generating README.md...[/bold cyan]")
        if multi_model:
            console.print("[dim]Using multi-model orchestration with specialized models for each step.[/dim]\n")
        else:
            console.print("[dim]Tip: Use --multi-model for better quality with multiple specialized models.[/dim]\n")

        # Create necessary components
        from hrisa_code.core.conversation import ConversationManager
        from hrisa_code.core.conversation import OllamaConfig
        from hrisa_code.core.orchestrators import ReadmeOrchestrator

        # Create OllamaConfig
        ollama_config = OllamaConfig(
            model=config.model.name,
            host=config.ollama.host,
            temperature=config.model.temperature,
            top_p=config.model.top_p,
            top_k=config.model.top_k,
        )

        # Create conversation manager
        conversation = ConversationManager(
            ollama_config=ollama_config,
            system_prompt="You are a technical writer specializing in clear, user-friendly documentation.",
            enable_tools=True,
            working_directory=path,
        )

        # Set up model router if multi-model is enabled
        model_router = None
        if multi_model:
            from hrisa_code.core.model_router import ModelRouter, ModelSelectionStrategy
            from hrisa_code.core.conversation import OllamaClient

            # Create Ollama client to query available models
            temp_client = OllamaClient(ollama_config)
            available_models = asyncio.run(temp_client.list_models())

            # Create model router
            strategy = ModelSelectionStrategy(
                prefer_quality=True,
                available_models=set(available_models),
                default_model=config.model.name
            )
            model_router = ModelRouter(strategy=strategy)

            console.print(f"[dim]→ Found {len(available_models)} available models[/dim]")
            console.print()

        # Create and run orchestrator
        orchestrator = ReadmeOrchestrator(
            conversation=conversation,
            project_path=path,
            console=console,
            model_router=model_router,
            enable_multi_model=multi_model,
        )

        readme_content = asyncio.run(orchestrator.generate_readme())

        # Write README.md
        if readme_content:
            readme_path.write_text(readme_content)
            console.print(f"[green]README.md created at {readme_path}[/green]")
            console.print("\n[bold]Next steps:[/bold]")
            console.print("1. Review the generated README.md")
            console.print("2. Customize sections as needed")
            console.print("3. Add project-specific screenshots or examples")
            console.print("4. Commit to your repository")
        else:
            console.print("[yellow]Warning: README generation produced no content[/yellow]")

    except Exception as e:
        console.print(f"[red]Error generating README.md:[/red]", markup=True)
        console.print(str(e), markup=False)
        console.print("\n[yellow]Make sure Ollama is running:[/yellow]")
        console.print("  ollama serve")
        console.print(f"\nAnd that you have the model: [cyan]ollama pull {config.model.name}[/cyan]")
        raise typer.Exit(1)


@app.command()
def contributing(
    path: Path = typer.Argument(
        Path.cwd(),
        help="Project directory to generate CONTRIBUTING.md for",
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        "-m",
        help="Ollama model to use for CONTRIBUTING.md generation",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force overwrite without confirmation",
    ),
    multi_model: bool = typer.Option(
        False,
        "--multi-model",
        help="Use multiple specialized models for different steps",
    ),
) -> None:
    """Generate comprehensive CONTRIBUTING.md contributor guidelines.

    Uses multi-step orchestration to analyze the project and generate
    contributor guidelines covering setup, workflow, standards, and architecture.

    The orchestrator will:
    1. Discover project setup requirements
    2. Identify code standards and quality expectations
    3. Understand contribution workflow and git practices
    4. Map architecture and common patterns
    5. Synthesize comprehensive CONTRIBUTING.md

    Example:
        hrisa contributing
        hrisa contributing --multi-model
        hrisa contributing --model qwen2.5:72b --force
    """
    # Load config (use default if not found)
    try:
        config_path = Config.get_project_config_path(path)
        if config_path.exists():
            config = Config.load(config_path)
        else:
            config = Config()
            console.print("[yellow]No config found, using defaults[/yellow]")
            console.print(f"[dim]Tip: Run 'hrisa init' to create config at {config_path}[/dim]\n")
    except Exception:
        config = Config()

    # Override model if specified
    if model:
        config.model.name = model

    contributing_path = path / "CONTRIBUTING.md"

    # Check if CONTRIBUTING.md exists
    if contributing_path.exists() and not force:
        console.print(f"[yellow]CONTRIBUTING.md already exists at {contributing_path}[/yellow]")
        overwrite = typer.confirm("Overwrite?")
        if not overwrite:
            raise typer.Exit()

    try:
        console.print("[bold cyan]Generating CONTRIBUTING.md...[/bold cyan]")
        if multi_model:
            console.print("[dim]Using multi-model orchestration with specialized models for each step.[/dim]\n")
        else:
            console.print("[dim]Tip: Use --multi-model for better quality with multiple specialized models.[/dim]\n")

        # Create necessary components
        from hrisa_code.core.conversation import ConversationManager
        from hrisa_code.core.conversation import OllamaConfig
        from hrisa_code.core.orchestrators import ContributingOrchestrator

        # Create OllamaConfig
        ollama_config = OllamaConfig(
            model=config.model.name,
            host=config.ollama.host,
            temperature=config.model.temperature,
            top_p=config.model.top_p,
            top_k=config.model.top_k,
        )

        # Create conversation manager
        conversation = ConversationManager(
            ollama_config=ollama_config,
            system_prompt="You are a technical writer specializing in contributor documentation and open-source best practices.",
            enable_tools=True,
            working_directory=path,
        )

        # Set up model router if multi-model is enabled
        model_router = None
        if multi_model:
            from hrisa_code.core.model_router import ModelRouter, ModelSelectionStrategy
            from hrisa_code.core.conversation import OllamaClient

            # Create Ollama client to query available models
            temp_client = OllamaClient(ollama_config)
            available_models = asyncio.run(temp_client.list_models())

            # Create model router
            strategy = ModelSelectionStrategy(
                prefer_quality=True,
                available_models=set(available_models),
                default_model=config.model.name
            )
            model_router = ModelRouter(strategy=strategy)

            console.print(f"[dim]→ Found {len(available_models)} available models[/dim]")
            console.print()

        # Create and run orchestrator
        orchestrator = ContributingOrchestrator(
            conversation=conversation,
            project_path=path,
            console=console,
            model_router=model_router,
            enable_multi_model=multi_model,
        )

        contributing_content = asyncio.run(orchestrator.generate_contributing())

        # Write CONTRIBUTING.md
        if contributing_content:
            contributing_path.write_text(contributing_content)
            console.print(f"[green]CONTRIBUTING.md created at {contributing_path}[/green]")
            console.print("\n[bold]Next steps:[/bold]")
            console.print("1. Review the generated CONTRIBUTING.md")
            console.print("2. Customize sections for your project specifics")
            console.print("3. Add CODE_OF_CONDUCT.md if you don't have one")
            console.print("4. Update PR and issue templates to reference this guide")
            console.print("5. Commit to your repository")
        else:
            console.print("[yellow]Warning: CONTRIBUTING generation produced no content[/yellow]")

    except Exception as e:
        console.print(f"[red]Error generating CONTRIBUTING.md:[/red]", markup=True)
        console.print(str(e), markup=False)
        console.print("\n[yellow]Make sure Ollama is running:[/yellow]")
        console.print("  ollama serve")
        console.print(f"\nAnd that you have the model: [cyan]ollama pull {config.model.name}[/cyan]")
        raise typer.Exit(1)


@app.command()
def readme_progressive(
    path: Path = typer.Argument(
        Path.cwd(),
        help="Project directory to generate README.md for",
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        "-m",
        help="Ollama model to use for README.md generation",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force overwrite without confirmation",
    ),
) -> None:
    """Generate README.md using progressive context-building (NEW APPROACH).

    This command uses a fundamentally different strategy than 'hrisa readme':
    - Extract ground-truth facts first (validated)
    - Build each section incrementally (validated)
    - Assemble final document (no synthesis hallucination)

    This approach prevents the model from inventing project names or features.
    """
    from hrisa_code.core.orchestrators import ProgressiveReadmeOrchestrator

    try:
        config = Config.load_with_fallback(project_dir=path)
        if model:
            config.model.name = model

        console.print(Panel(
            f"[bold]Progressive README Generation[/bold]\n\n"
            f"Project: {path}\n"
            f"Model: {config.model.name}\n"
            f"Strategy: Extract → Build → Validate → Assemble",
            border_style="cyan"
        ))

        # Check for existing README
        readme_path = path / "README.md"
        if readme_path.exists() and not force:
            console.print(f"\n[yellow]README.md already exists at {readme_path}[/yellow]")
            console.print("Use --force to overwrite")
            raise typer.Exit(1)

        # Create conversation manager
        ollama_config = OllamaConfig(
            model=config.model.name,
            host=config.ollama.host,
            temperature=config.model.temperature,
            top_p=config.model.top_p,
            top_k=config.model.top_k,
        )
        conversation = ConversationManager(
            ollama_config=ollama_config,
            working_directory=path,
            enable_tools=True,
        )

        # Create progressive orchestrator
        orchestrator = ProgressiveReadmeOrchestrator(
            conversation=conversation,
            project_path=path,
            console=console,
        )

        # Generate README
        console.print()
        readme_content = asyncio.run(orchestrator.generate())

        if readme_content:
            console.print(f"\n[green]README.md created at {readme_path}[/green]")
            console.print("\nNext steps:")
            console.print("1. Review the generated README.md")
            console.print("2. Compare with old 'hrisa readme' output")
            console.print("3. Verify project name and features are correct")
        else:
            console.print("[yellow]Warning: Progressive generation produced no content[/yellow]")

    except Exception as e:
        console.print(f"[red]Error in progressive README generation:[/red]", markup=True)
        console.print(str(e), markup=False)
        console.print("\n[yellow]Make sure Ollama is running:[/yellow]")
        console.print("  ollama serve")
        console.print(f"\nAnd that you have the model: [cyan]ollama pull {config.model.name}[/cyan]")
        raise typer.Exit(1)


@app.command()
def api_progressive(
    path: Path = typer.Argument(
        Path.cwd(),
        help="Project directory to generate API.md for",
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        "-m",
        help="Ollama model to use for API.md generation",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force overwrite without confirmation",
    ),
) -> None:
    """Generate API.md using progressive context-building (NEW APPROACH).

    This command uses the proven progressive strategy:
    - Extract ground-truth facts first (validated)
    - Build each section incrementally (validated)
    - Assemble final document (no synthesis hallucination)

    Prevents the model from inventing project names or API endpoints.
    """
    from hrisa_code.core.orchestrators import ProgressiveApiOrchestrator

    try:
        config = Config.load_with_fallback(project_dir=path)
        if model:
            config.model.name = model

        console.print(Panel(
            f"[bold]Progressive API Documentation Generation[/bold]\n\n"
            f"Project: {path}\n"
            f"Model: {config.model.name}\n"
            f"Strategy: Extract → Build → Validate → Assemble",
            border_style="cyan"
        ))

        # Check for existing API.md
        api_path = path / "API.md"
        if api_path.exists() and not force:
            console.print(f"\n[yellow]API.md already exists at {api_path}[/yellow]")
            console.print("Use --force to overwrite")
            raise typer.Exit(1)

        # Create conversation manager
        ollama_config = OllamaConfig(
            model=config.model.name,
            host=config.ollama.host,
            temperature=config.model.temperature,
            top_p=config.model.top_p,
            top_k=config.model.top_k,
        )
        conversation = ConversationManager(
            ollama_config=ollama_config,
            working_directory=path,
            enable_tools=True,
        )

        # Create progressive orchestrator
        orchestrator = ProgressiveApiOrchestrator(
            conversation=conversation,
            project_path=path,
            console=console,
        )

        # Generate API.md
        console.print()
        api_content = asyncio.run(orchestrator.generate())

        if api_content:
            console.print(f"\n[green]API.md created at {api_path}[/green]")
            console.print("\nNext steps:")
            console.print("1. Review the generated API.md")
            console.print("2. Verify CLI commands and tools are documented")
            console.print("3. Check that all sections are complete")
        else:
            console.print("[yellow]Warning: Progressive generation produced no content[/yellow]")

    except Exception as e:
        console.print(f"[red]Error in progressive API generation:[/red]", markup=True)
        console.print(str(e), markup=False)
        console.print("\n[yellow]Make sure Ollama is running:[/yellow]")
        console.print("  ollama serve")
        console.print(f"\nAnd that you have the model: [cyan]ollama pull {config.model.name}[/cyan]")
        raise typer.Exit(1)


@app.command()
def contributing_progressive(
    path: Path = typer.Argument(
        Path.cwd(),
        help="Project directory to generate CONTRIBUTING.md for",
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        "-m",
        help="Ollama model to use for CONTRIBUTING.md generation",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force overwrite without confirmation",
    ),
) -> None:
    """Generate CONTRIBUTING.md using progressive context-building (NEW APPROACH).

    This command uses the proven progressive strategy:
    - Extract ground-truth facts first (validated)
    - Build each section incrementally (validated)
    - Assemble final document (no synthesis hallucination)

    Prevents the model from inventing project names or workflows.
    """
    from hrisa_code.core.orchestrators import ProgressiveContributingOrchestrator

    try:
        config = Config.load_with_fallback(project_dir=path)
        if model:
            config.model.name = model

        console.print(Panel(
            f"[bold]Progressive CONTRIBUTING Documentation Generation[/bold]\n\n"
            f"Project: {path}\n"
            f"Model: {config.model.name}\n"
            f"Strategy: Extract → Build → Validate → Assemble",
            border_style="cyan"
        ))

        # Check for existing CONTRIBUTING.md
        contributing_path = path / "CONTRIBUTING.md"
        if contributing_path.exists() and not force:
            console.print(f"\n[yellow]CONTRIBUTING.md already exists at {contributing_path}[/yellow]")
            console.print("Use --force to overwrite")
            raise typer.Exit(1)

        # Create conversation manager
        ollama_config = OllamaConfig(
            model=config.model.name,
            host=config.ollama.host,
            temperature=config.model.temperature,
            top_p=config.model.top_p,
            top_k=config.model.top_k,
        )
        conversation = ConversationManager(
            ollama_config=ollama_config,
            working_directory=path,
            enable_tools=True,
        )

        # Create progressive orchestrator
        orchestrator = ProgressiveContributingOrchestrator(
            conversation=conversation,
            project_path=path,
            console=console,
        )

        # Generate CONTRIBUTING.md
        console.print()
        contributing_content = asyncio.run(orchestrator.generate())

        if contributing_content:
            console.print(f"\n[green]CONTRIBUTING.md created at {contributing_path}[/green]")
            console.print("\nNext steps:")
            console.print("1. Review the generated CONTRIBUTING.md")
            console.print("2. Verify setup instructions and workflow are correct")
            console.print("3. Check that all sections are complete")
        else:
            console.print("[yellow]Warning: Progressive generation produced no content[/yellow]")

    except Exception as e:
        console.print(f"[red]Error in progressive CONTRIBUTING generation:[/red]", markup=True)
        console.print(str(e), markup=False)
        console.print("\n[yellow]Make sure Ollama is running:[/yellow]")
        console.print("  ollama serve")
        console.print(f"\nAnd that you have the model: [cyan]ollama pull {config.model.name}[/cyan]")
        raise typer.Exit(1)


@app.command()
def hrisa_progressive(
    path: Path = typer.Argument(
        Path.cwd(),
        help="Project directory to generate HRISA.md for",
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        "-m",
        help="Ollama model to use for HRISA.md generation",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force overwrite without confirmation",
    ),
) -> None:
    """Generate HRISA.md using progressive context-building (NEW APPROACH).

    This command uses the proven progressive strategy:
    - Extract ground-truth facts first (validated)
    - Build each section incrementally (validated)
    - Assemble final document (no synthesis hallucination)

    Prevents the model from inventing project names or architecture details.
    """
    from hrisa_code.core.orchestrators import ProgressiveHrisaOrchestrator

    try:
        config = Config.load_with_fallback(project_dir=path)
        if model:
            config.model.name = model

        console.print(Panel(
            f"[bold]Progressive HRISA Documentation Generation[/bold]\n\n"
            f"Project: {path}\n"
            f"Model: {config.model.name}\n"
            f"Strategy: Extract → Build → Validate → Assemble",
            border_style="cyan"
        ))

        # Check for existing HRISA.md
        hrisa_path = path / "HRISA.md"
        if hrisa_path.exists() and not force:
            console.print(f"\n[yellow]HRISA.md already exists at {hrisa_path}[/yellow]")
            console.print("Use --force to overwrite")
            raise typer.Exit(1)

        # Create conversation manager
        ollama_config = OllamaConfig(
            model=config.model.name,
            host=config.ollama.host,
            temperature=config.model.temperature,
            top_p=config.model.top_p,
            top_k=config.model.top_k,
        )
        conversation = ConversationManager(
            ollama_config=ollama_config,
            working_directory=path,
            enable_tools=True,
        )

        # Create progressive orchestrator
        orchestrator = ProgressiveHrisaOrchestrator(
            conversation=conversation,
            project_path=path,
            console=console,
        )

        # Generate HRISA.md
        console.print()
        hrisa_content = asyncio.run(orchestrator.generate())

        if hrisa_content:
            console.print(f"\n[green]HRISA.md created at {hrisa_path}[/green]")
            console.print("\nNext steps:")
            console.print("1. Review the generated HRISA.md")
            console.print("2. Verify architecture and components are documented")
            console.print("3. Check that all sections are complete")
        else:
            console.print("[yellow]Warning: Progressive generation produced no content[/yellow]")

    except Exception as e:
        console.print(f"[red]Error in progressive HRISA generation:[/red]", markup=True)
        console.print(str(e), markup=False)
        console.print("\n[yellow]Make sure Ollama is running:[/yellow]")
        console.print("  ollama serve")
        console.print(f"\nAnd that you have the model: [cyan]ollama pull {config.model.name}[/cyan]")
        raise typer.Exit(1)


@app.command()
def api(
    path: Path = typer.Argument(
        Path.cwd(),
        help="Project directory to generate API.md for",
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        "-m",
        help="Ollama model to use for API.md generation",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force overwrite without confirmation",
    ),
    multi_model: bool = typer.Option(
        False,
        "--multi-model",
        help="Use multiple specialized models for different steps",
    ),
) -> None:
    """Generate comprehensive API.md reference documentation (OLD APPROACH).

    Uses multi-step orchestration to analyze the project and generate
    complete API reference covering CLI commands, tools, core APIs, and configuration.

    NOTE: Consider using 'api-progressive' for better accuracy.

    The orchestrator will:
    1. Discover all CLI commands and their usage
    2. Find all available tools and their schemas
    3. Analyze public classes, methods, and functions
    4. Document configuration options
    5. Synthesize comprehensive API.md

    Example:
        hrisa api
        hrisa api --multi-model
        hrisa api --model qwen2.5:72b --force
    """
    # Load config (use default if not found)
    try:
        config_path = Config.get_project_config_path(path)
        if config_path.exists():
            config = Config.load(config_path)
        else:
            config = Config()
            console.print("[yellow]No config found, using defaults[/yellow]")
            console.print(f"[dim]Tip: Run 'hrisa init' to create config at {config_path}[/dim]\n")
    except Exception:
        config = Config()

    # Override model if specified
    if model:
        config.model.name = model

    api_path = path / "API.md"

    # Check if API.md exists
    if api_path.exists() and not force:
        console.print(f"[yellow]API.md already exists at {api_path}[/yellow]")
        overwrite = typer.confirm("Overwrite?")
        if not overwrite:
            raise typer.Exit()

    try:
        console.print("[bold cyan]Generating API.md...[/bold cyan]")
        if multi_model:
            console.print("[dim]Using multi-model orchestration with specialized models for each step.[/dim]\n")
        else:
            console.print("[dim]Tip: Use --multi-model for better quality with multiple specialized models.[/dim]\n")

        # Create necessary components
        from hrisa_code.core.conversation import ConversationManager
        from hrisa_code.core.conversation import OllamaConfig
        from hrisa_code.core.orchestrators import ApiOrchestrator

        # Create OllamaConfig
        ollama_config = OllamaConfig(
            model=config.model.name,
            host=config.ollama.host,
            temperature=config.model.temperature,
            top_p=config.model.top_p,
            top_k=config.model.top_k,
        )

        # Create conversation manager
        conversation = ConversationManager(
            ollama_config=ollama_config,
            system_prompt="You are a technical writer specializing in API documentation and developer references.",
            enable_tools=True,
            working_directory=path,
        )

        # Set up model router if multi-model is enabled
        model_router = None
        if multi_model:
            from hrisa_code.core.model_router import ModelRouter, ModelSelectionStrategy
            from hrisa_code.core.conversation import OllamaClient

            # Create Ollama client to query available models
            temp_client = OllamaClient(ollama_config)
            available_models = asyncio.run(temp_client.list_models())

            # Create model router
            strategy = ModelSelectionStrategy(
                prefer_quality=True,
                available_models=set(available_models),
                default_model=config.model.name
            )
            model_router = ModelRouter(strategy=strategy)

            console.print(f"[dim]→ Found {len(available_models)} available models[/dim]")
            console.print()

        # Create and run orchestrator
        orchestrator = ApiOrchestrator(
            conversation=conversation,
            project_path=path,
            console=console,
            model_router=model_router,
            enable_multi_model=multi_model,
        )

        api_content = asyncio.run(orchestrator.generate_api())

        # Write API.md
        if api_content:
            api_path.write_text(api_content)
            console.print(f"[green]API.md created at {api_path}[/green]")
            console.print("\n[bold]Next steps:[/bold]")
            console.print("1. Review the generated API.md")
            console.print("2. Verify all APIs are documented correctly")
            console.print("3. Add examples for complex APIs")
            console.print("4. Link from README.md to API.md")
            console.print("5. Commit to your repository")
        else:
            console.print("[yellow]Warning: API generation produced no content[/yellow]")

    except Exception as e:
        console.print(f"[red]Error generating API.md:[/red]", markup=True)
        console.print(str(e), markup=False)
        console.print("\n[yellow]Make sure Ollama is running:[/yellow]")
        console.print("  ollama serve")
        console.print(f"\nAnd that you have the model: [cyan]ollama pull {config.model.name}[/cyan]")
        raise typer.Exit(1)


@app.command()
def web(
    host: str = typer.Option(
        "0.0.0.0",
        "--host",
        "-h",
        help="Host to bind to",
    ),
    port: int = typer.Option(
        8000,
        "--port",
        "-p",
        help="Port to listen on",
    ),
    reload: bool = typer.Option(
        False,
        "--reload",
        "-r",
        help="Enable auto-reload for development",
    ),
) -> None:
    """Start the web UI server for managing GenAI agents.

    The web UI provides:
    - Visual dashboard for all agents
    - Real-time progress tracking
    - Stuck detection and intervention
    - User instruction interface
    - Agent output visualization

    Example:
        hrisa web                          # Start on http://0.0.0.0:8000
        hrisa web --port 3000              # Start on port 3000
        hrisa web --reload                 # Development mode with auto-reload
    """
    try:
        from hrisa_code.web import run_server

        console.print(Panel(
            "[bold cyan]Hrisa Code Web UI[/bold cyan]\n\n"
            f"Starting server on http://{host}:{port}\n\n"
            "[green]Features:[/green]\n"
            "  • Create and manage multiple agents\n"
            "  • Real-time progress tracking\n"
            "  • Automatic stuck detection\n"
            "  • Send instructions to agents\n"
            "  • View agent outputs and messages\n\n"
            "[yellow]Press Ctrl+C to stop[/yellow]",
            title="Web UI Server",
            border_style="cyan",
        ))

        console.print(f"\n[bold]Opening web UI at:[/bold] http://{host}:{port}")
        console.print(f"[dim]API documentation:[/dim] http://{host}:{port}/docs\n")

        run_server(host=host, port=port, reload=reload)

    except ImportError:
        console.print("[red]Error: Web UI dependencies not installed[/red]")
        console.print("\nInstall with:")
        console.print("  pip install 'hrisa-code[web]'")
        console.print("\nOr install all dependencies:")
        console.print("  pip install -e '.[dev]'")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped[/yellow]")
    except Exception as e:
        console.print(f"[red]Error starting web server:[/red] {str(e)}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
