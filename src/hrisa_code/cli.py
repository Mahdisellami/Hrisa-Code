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
from hrisa_code.core.interactive import InteractiveSession
from hrisa_code.core.ollama_client import OllamaClient, OllamaConfig

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
) -> None:
    """Initialize Hrisa Code configuration."""
    if global_config:
        config_path = Config.get_default_config_path()
    else:
        config_path = Config.get_project_config_path(path)

    if config_path.exists():
        console.print(f"[yellow]Configuration already exists at {config_path}[/yellow]")
        overwrite = typer.confirm("Overwrite?")
        if not overwrite:
            raise typer.Exit()

    # Create default configuration
    config = Config()
    config.save(config_path)

    console.print(f"[green]Configuration initialized at {config_path}[/green]")
    console.print("\n[bold]Next steps:[/bold]")
    console.print("1. Edit the configuration file to customize settings")
    console.print(f"2. Make sure Ollama is running: [cyan]ollama serve[/cyan]")
    console.print(f"3. Pull a model: [cyan]ollama pull {config.model.name}[/cyan]")
    console.print(f"4. Start chatting: [cyan]hrisa chat[/cyan]")


if __name__ == "__main__":
    app()
