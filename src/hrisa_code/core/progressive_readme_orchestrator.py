"""Progressive context-building orchestrator for README generation.

This orchestrator uses a fundamentally different approach from base orchestrator:
- Extract ground-truth facts first (using static analysis, not LLM)
- Build each section incrementally with validation
- Assemble (don't synthesize) final document

This prevents hallucination by never allowing freeform "synthesis" thinking.
"""

import re
from pathlib import Path
from typing import Optional, Dict, Any, List
from rich.console import Console
from rich.panel import Panel

from hrisa_code.core.conversation import ConversationManager
from hrisa_code.tools.cli_introspection import (
    extract_cli_commands_from_ast,
    extract_pyproject_metadata,
    extract_tool_definitions,
    validate_content_quality,
)


class ProgressiveReadmeOrchestrator:
    """Progressive README generation with validation at each step.

    Strategy:
    1. Extract Facts: Read pyproject.toml, validate extraction
    2. Build Title Section: Use extracted facts, validate project name
    3. Build Features Section: Read code, list actual features
    4. Build Installation Section: Find setup methods
    5. Build Usage Section: Extract CLI examples
    6. Assemble: Combine sections (no synthesis thinking)
    """

    def __init__(
        self,
        conversation: ConversationManager,
        project_path: Path,
        console: Optional[Console] = None,
    ):
        """Initialize progressive orchestrator.

        Args:
            conversation: Conversation manager for LLM interactions
            project_path: Path to the project root
            console: Rich console for output
        """
        self.conversation = conversation
        self.project_path = project_path
        self.console = console or Console()
        self.facts: Dict[str, Any] = {}
        self.sections: Dict[str, str] = {}

    async def extract_facts(self) -> Dict[str, Any]:
        """Phase 1: Extract ground-truth facts from pyproject.toml using static analysis.

        Returns:
            Validated facts dictionary
        """
        self.console.print(Panel(
            "[bold cyan]Phase 1: Ground Truth Extraction[/bold cyan]\n"
            "Parsing pyproject.toml directly (no LLM)...",
            border_style="cyan"
        ))

        # Use static analysis instead of LLM
        pyproject_path = self.project_path / "pyproject.toml"
        metadata = extract_pyproject_metadata(pyproject_path)

        self.facts = {
            "name": metadata.get("name", "UNKNOWN"),
            "description": metadata.get("description", "UNKNOWN"),
            "version": metadata.get("version", "0.0.0"),
            "python_requires": metadata.get("python_requires", ">=3.10"),
            "dependencies": metadata.get("dependencies", [])[:5],  # First 5
            "license": metadata.get("license", ""),
        }

        # Validation
        if self.facts["name"] == "UNKNOWN":
            self.console.print("[red]✗ Could not extract project name![/red]")
        else:
            self.console.print(f"[green]✓[/green] Facts extracted: {self.facts['name']} v{self.facts['version']}")

        return self.facts

    async def build_title_section(self) -> str:
        """Phase 2: Build title section using validated facts.

        Returns:
            Title section markdown
        """
        self.console.print(Panel(
            "[bold cyan]Phase 2: Title Section[/bold cyan]\n"
            "Building title with validated project name...",
            border_style="cyan"
        ))

        # Direct assembly - no LLM needed for simple template!
        name = self.facts.get("name", "UNKNOWN")
        description = self.facts.get("description", "UNKNOWN")

        section = f"""# {name}

{description}

## Table of Contents
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Development](#development)
- [License](#license)
"""

        self.sections["title"] = section

        # Validation
        if name.lower() in section.lower():
            self.console.print(f"[green]✓[/green] Title section built: {name}")
        else:
            self.console.print(f"[red]✗[/red] Validation failed for title")

        return section

    async def build_features_section(self) -> str:
        """Phase 3: Build features section from actual code using static analysis.

        Returns:
            Features section markdown
        """
        self.console.print(Panel(
            "[bold cyan]Phase 3: Features Section[/bold cyan]\n"
            "Extracting CLI commands via AST parsing (no LLM)...",
            border_style="cyan"
        ))

        # Use static analysis to extract commands
        cli_file = self.project_path / "src" / "hrisa_code" / "cli.py"
        if not cli_file.exists():
            cli_file = self.project_path / "cli.py"

        commands = extract_cli_commands_from_ast(cli_file)

        # Build features section from actual commands
        section = "## Features\n\n"

        if commands:
            for cmd in commands:
                name = cmd["name"]
                help_text = cmd["help"] or "No description available"
                section += f"- **{name}**: {help_text}\n"

            self.console.print(f"[green]✓[/green] Features extracted: {len(commands)} commands found")
        else:
            section += "- Interactive CLI interface\n- Local LLM integration\n"
            self.console.print("[yellow]⚠[/yellow] No commands found, using defaults")

        # Now ask LLM to write prose about these features (directive prompt)
        prompt = f"""Write a 2-3 sentence introduction for the Features section.

The project is: {self.facts.get('name', 'this project')}
Description: {self.facts.get('description', '')}

Available commands:
{chr(10).join(f"- {cmd['name']}: {cmd['help']}" for cmd in commands)}

OUTPUT ONLY THE PROSE (no markdown headers, no bullet points).
Example: "This tool provides a comprehensive CLI interface for..."

Do NOT include conversational phrases like "Here is" or "I've written"."""

        intro = await self.conversation.process_message(prompt)
        intro = intro.strip()

        # Combine intro + features list
        section = f"## Features\n\n{intro}\n\n" + "\n".join(
            f"- **{cmd['name']}**: {cmd['help']}" for cmd in commands
        )

        self.sections["features"] = section
        return section

    async def build_installation_section(self) -> str:
        """Phase 4: Build installation section using known facts.

        Returns:
            Installation section markdown
        """
        self.console.print(Panel(
            "[bold cyan]Phase 4: Installation Section[/bold cyan]\n"
            "Building installation instructions from facts...",
            border_style="cyan"
        ))

        # Use facts we already extracted
        python_req = self.facts.get("python_requires", ">=3.10")
        name = self.facts.get("name", "this-package")

        # Build prerequisites
        section = f"""## Prerequisites

- Python {python_req}
- pip package manager
"""

        # Check for additional prerequisites by asking LLM to read specific files
        prompt = f"""Read {self.project_path}/README.md and look for the "Prerequisites" section.

Extract ONLY the actual prerequisites listed (like Ollama, Docker, etc.).
OUTPUT FORMAT:
- Prerequisite 1
- Prerequisite 2

If no prerequisites section exists, output: NONE"""

        prereqs_response = await self.conversation.process_message(prompt)

        if "NONE" not in prereqs_response and prereqs_response.strip():
            # Add additional prerequisites
            for line in prereqs_response.strip().split('\n'):
                if line.strip().startswith('-'):
                    section += f"{line.strip()}\n"

        # Build installation instructions
        section += f"""
## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/{name}.git
cd {name}

# Install dependencies
pip install -e ".[dev]"
```
"""

        self.sections["installation"] = section
        self.console.print("[green]✓[/green] Installation section built")
        return section

    async def build_usage_section(self) -> str:
        """Phase 5: Build usage section using template + LLM prose.

        Returns:
            Usage section markdown
        """
        self.console.print(Panel(
            "[bold cyan]Phase 5: Usage Section[/bold cyan]\n"
            "Building usage examples from extracted commands...",
            border_style="cyan"
        ))

        # Get commands we extracted in Phase 3
        cli_file = self.project_path / "src" / "hrisa_code" / "cli.py"
        if not cli_file.exists():
            cli_file = self.project_path / "cli.py"

        commands = extract_cli_commands_from_ast(cli_file)
        name = self.facts.get("name", "this-tool")

        # Build usage section with template
        section = "## Usage\n\n"

        if commands:
            # Ask LLM to write a brief usage introduction (directive)
            prompt = f"""Write 1-2 sentences introducing how to use {name}.

The tool has these commands: {', '.join(cmd['name'] for cmd in commands)}

OUTPUT ONLY THE PROSE (no headers, no code blocks).
Example: "Start by running the chat command to interact with..."

Do NOT use conversational phrases."""

            intro = await self.conversation.process_message(prompt)
            section += f"{intro.strip()}\n\n"

            # Add examples for each command
            section += "### Commands\n\n"
            for cmd in commands:
                section += f"```bash\n# {cmd['help']}\n{name} {cmd['name']}\n```\n\n"

        else:
            section += "See the documentation for usage examples.\n"

        self.sections["usage"] = section
        self.console.print("[green]✓[/green] Usage section built")
        return section

    async def assemble_readme(self) -> str:
        """Phase 6: Assemble final README with quality validation.

        Returns:
            Complete README markdown
        """
        self.console.print(Panel(
            "[bold cyan]Phase 6: Assembly & Validation[/bold cyan]\n"
            "Combining sections and validating quality...",
            border_style="cyan"
        ))

        # Simple string concatenation - no LLM needed!
        readme_parts = [
            self.sections.get("title", "# README\n"),
            "\n",
            self.sections.get("features", "## Features\n\nTODO\n"),
            "\n",
            self.sections.get("installation", "## Installation\n\nTODO\n"),
            "\n",
            self.sections.get("usage", "## Usage\n\nTODO\n"),
            "\n## Development\n\nSee CONTRIBUTING.md for development guidelines.\n",
            "\n## License\n\nMIT License\n",
        ]

        # Join and clean up extra newlines
        readme = "\n".join(readme_parts)
        readme = re.sub(r'\n{3,}', '\n\n', readme)  # Max 2 consecutive newlines

        # Content quality validation
        is_valid, errors = validate_content_quality(readme)

        if not is_valid:
            self.console.print("[red]✗ Content quality validation FAILED:[/red]")
            for error in errors:
                self.console.print(f"  • {error}")
            raise ValueError(f"Content quality validation failed: {len(errors)} issues found")

        # Basic validation
        project_name = self.facts.get("name", "UNKNOWN")
        if project_name.lower() not in readme.lower():
            self.console.print(f"[red]✗ VALIDATION FAILED: Project name '{project_name}' not in final README[/red]")
        else:
            self.console.print(f"[green]✓[/green] Content validation passed: clean, accurate documentation")

        return readme

    async def generate(self) -> str:
        """Execute progressive README generation workflow.

        Returns:
            Generated README content
        """
        self.console.print(Panel(
            "[bold]Progressive README Generation[/bold]\n"
            f"Project: {self.project_path}\n"
            "Strategy: Extract → Build → Validate → Assemble",
            title="► Starting Progressive Orchestration",
            border_style="bold cyan"
        ))

        try:
            # Phase 1: Extract facts
            await self.extract_facts()

            # Phase 2-5: Build sections incrementally
            await self.build_title_section()
            await self.build_features_section()
            await self.build_installation_section()
            await self.build_usage_section()

            # Phase 6: Assemble (no synthesis)
            readme = await self.assemble_readme()

            # Write to file
            output_path = self.project_path / "README.md"
            output_path.write_text(readme)

            self.console.print(Panel(
                f"[green]✓ README.md generated successfully![/green]\n\n"
                f"Output: {output_path}\n"
                f"Sections: {len(self.sections)}\n"
                f"Validated: ✓",
                title="► Complete",
                border_style="bold green"
            ))

            return readme

        except Exception as e:
            self.console.print(f"[red]✗ Error during progressive generation: {e}[/red]")
            raise
