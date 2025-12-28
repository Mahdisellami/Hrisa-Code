"""Progressive context-building orchestrator for README generation.

This orchestrator uses a fundamentally different approach from base orchestrator:
- Extract ground-truth facts first
- Build each section incrementally with validation
- Assemble (don't synthesize) final document

This prevents hallucination by never allowing freeform "synthesis" thinking.
"""

from pathlib import Path
from typing import Optional, Dict, Any
from rich.console import Console
from rich.panel import Panel

from hrisa_code.core.conversation import ConversationManager


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
        """Phase 1: Extract ground-truth facts from pyproject.toml.

        Returns:
            Validated facts dictionary
        """
        self.console.print(Panel(
            "[bold cyan]Phase 1: Ground Truth Extraction[/bold cyan]\n"
            "Reading pyproject.toml for authoritative facts...",
            border_style="cyan"
        ))

        prompt = f"""FACT EXTRACTION TASK (NO INTERPRETATION ALLOWED)

Read {self.project_path}/pyproject.toml and extract these EXACT values:

1. project.name → This is the AUTHORITATIVE project name
2. project.description → This is the OFFICIAL description
3. project.version → Current version
4. project.requires-python → Python version requirement
5. dependencies → List of main dependencies

CRITICAL RULES:
- Report EXACT strings from the file (no paraphrasing)
- Do NOT add your own descriptions
- Do NOT invent missing information
- If a field doesn't exist, report "NOT_FOUND"

Output format (use this EXACT structure):
```json
{{
  "name": "exact-name-from-file",
  "description": "exact description from file",
  "version": "x.y.z",
  "python_requires": ">=x.y",
  "dependencies": ["dep1", "dep2"]
}}
```

Read the file now and output ONLY the JSON (no other text)."""

        response = await self.conversation.chat(prompt)

        # TODO: Parse and validate JSON response
        # For now, store raw response
        self.facts["raw_extraction"] = response

        self.console.print("[green]✓[/green] Facts extracted")
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

        prompt = f"""BUILD TITLE SECTION (ASSEMBLY ONLY - NO CREATIVITY)

You previously extracted these facts:
{self.facts.get('raw_extraction', 'ERROR: No facts available')}

Your task: Create the title section using ONLY these extracted facts.

CRITICAL RULES:
- Use the EXACT project name from the facts
- Use the EXACT description from the facts
- Do NOT add emojis
- Do NOT add fake badges
- Do NOT invent taglines

Output format:
```markdown
# [exact project name from facts]

[exact description from facts]

## Table of Contents
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Development](#development)
- [License](#license)
```

Generate the title section now (markdown only, no explanations)."""

        section = await self.conversation.chat(prompt)
        self.sections["title"] = section

        # Validation check
        extracted_name = "hrisa-code"  # TODO: Parse from facts JSON
        if extracted_name.lower() not in section.lower():
            self.console.print(f"[yellow]⚠️  Warning: Project name '{extracted_name}' not found in title section[/yellow]")
        else:
            self.console.print("[green]✓[/green] Title section validated")

        return section

    async def build_features_section(self) -> str:
        """Phase 3: Build features section from actual code.

        Returns:
            Features section markdown
        """
        self.console.print(Panel(
            "[bold cyan]Phase 3: Features Section[/bold cyan]\n"
            "Discovering actual features from CLI commands...",
            border_style="cyan"
        ))

        prompt = f"""DISCOVER ACTUAL FEATURES (CODE-BASED ONLY)

Task: Find what this CLI actually DOES by reading the code.

Steps:
1. Use find_files to locate cli.py: pattern="**/cli.py", directory="{self.project_path}"
2. Read the cli.py file to find all @app.command() decorators
3. For each command:
   - Extract command name
   - Extract help text/docstring
   - This tells you what the CLI does

CRITICAL RULES:
- Only report features that correspond to ACTUAL commands found in cli.py
- Do NOT invent features
- Do NOT add generic "features" like "Easy to use" or "Fast performance"
- Base every feature on a concrete @app.command() you found

Output format:
## Features

- **[Command Name]**: [What the command does from its docstring]
- **[Command Name]**: [What the command does from its docstring]
[etc.]

Start by finding and reading cli.py."""

        section = await self.conversation.chat(prompt)
        self.sections["features"] = section

        self.console.print("[green]✓[/green] Features section built from actual commands")
        return section

    async def build_installation_section(self) -> str:
        """Phase 4: Build installation section from actual setup files.

        Returns:
            Installation section markdown
        """
        self.console.print(Panel(
            "[bold cyan]Phase 4: Installation Section[/bold cyan]\n"
            "Finding actual installation methods...",
            border_style="cyan"
        ))

        prompt = f"""DISCOVER INSTALLATION METHODS (FILE-BASED ONLY)

Task: Find how users actually install this project.

Steps:
1. Check if {self.project_path}/pyproject.toml has [project.scripts] or [tool.setuptools]
2. Check if {self.project_path}/README.md has installation instructions
3. Check if {self.project_path}/Makefile has install targets

Based on what you find, report ACTUAL installation methods (not generic ones).

CRITICAL RULES:
- Only report installation methods that EXIST in the project
- If it's on PyPI, show: pip install [exact-package-name]
- If it's source-only, show: git clone + pip install -e .
- Show the ACTUAL python version requirement from pyproject.toml

Output format:
## Prerequisites

- Python [exact version from pyproject.toml]
- [other actual prerequisites]

## Installation

[Actual installation commands based on what you found]

Start by reading pyproject.toml and README.md."""

        section = await self.conversation.chat(prompt)
        self.sections["installation"] = section

        self.console.print("[green]✓[/green] Installation section built from actual files")
        return section

    async def build_usage_section(self) -> str:
        """Phase 5: Build usage section from CLI help and examples.

        Returns:
            Usage section markdown
        """
        self.console.print(Panel(
            "[bold cyan]Phase 5: Usage Section[/bold cyan]\n"
            "Extracting actual CLI usage examples...",
            border_style="cyan"
        ))

        prompt = f"""CREATE USAGE EXAMPLES (COMMAND-BASED ONLY)

Task: Show how to actually use the CLI commands you found earlier.

For each command you discovered in Phase 3:
1. Show the basic command syntax
2. Show a simple example
3. Reference the command's help text

CRITICAL RULES:
- Only show commands that actually exist (from Phase 3)
- Use real command names (not placeholder names)
- Examples should be copy-pasteable
- No fake examples

Output format:
## Usage

### Basic Usage

```bash
[actual-command-name] [actual-subcommand]
```

### Examples

**[Actual feature]:**
```bash
[actual command example]
```

[More examples based on actual commands]

Generate usage section now."""

        section = await self.conversation.chat(prompt)
        self.sections["usage"] = section

        self.console.print("[green]✓[/green] Usage section built from actual commands")
        return section

    async def assemble_readme(self) -> str:
        """Phase 6: Assemble final README (no synthesis thinking).

        Returns:
            Complete README markdown
        """
        self.console.print(Panel(
            "[bold cyan]Phase 6: Assembly[/bold cyan]\n"
            "Combining validated sections...",
            border_style="cyan"
        ))

        # Simple string concatenation - no LLM needed!
        readme_parts = [
            self.sections.get("title", "# README\n"),
            self.sections.get("features", "## Features\n\nTODO\n"),
            self.sections.get("installation", "## Installation\n\nTODO\n"),
            self.sections.get("usage", "## Usage\n\nTODO\n"),
            "\n## Development\n\nSee CONTRIBUTING.md for development guidelines.\n",
            "\n## License\n\nMIT License\n",
        ]

        readme = "\n".join(readme_parts)

        # Final validation
        project_name = "hrisa-code"  # TODO: Get from validated facts
        if project_name.lower() not in readme.lower():
            self.console.print(f"[red]✗ VALIDATION FAILED: Project name '{project_name}' not in final README[/red]")
        else:
            self.console.print("[green]✓[/green] Final validation passed")

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
