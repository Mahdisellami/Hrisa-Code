"""Progressive context-building orchestrator for HRISA.md generation.

This orchestrator uses the proven progressive approach:
- Extract ground-truth facts first
- Build each section incrementally with validation
- Assemble (don't synthesize) final document

Target: AI coding assistants (like Claude Code)
Focus: Technical architecture, tool usage, development patterns
"""

import re
from pathlib import Path
from typing import Optional, Dict, Any
from rich.console import Console
from rich.panel import Panel

from hrisa_code.core.conversation import ConversationManager


class ProgressiveHrisaOrchestrator:
    """Progressive HRISA.md generation with validation at each step.

    Strategy:
    1. Extract Facts: Read pyproject.toml, validate extraction
    2. Build Title Section: Use extracted facts, validate project name
    3. Build Architecture Section: From actual src/ layout
    4. Build Components Section: From core/*.py files
    5. Build Tools Section: From tools/*.py definitions
    6. Build Development Section: From testing/config infrastructure
    7. Assemble: Combine sections (no synthesis thinking)
    """

    def __init__(
        self,
        conversation: ConversationManager,
        project_path: Path,
        console: Optional[Console] = None,
    ):
        """Initialize progressive HRISA orchestrator.

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
5. Main CLI entry point from project.scripts

CRITICAL RULES:
- Report EXACT strings from the file (copy-paste, no paraphrasing)
- Do NOT add your own descriptions
- Do NOT invent missing information

After reading the file, respond with ONLY this format (no markdown, no explanations):

PROJECT_NAME: [exact name from file]
PROJECT_DESC: [exact description from file]
VERSION: [exact version]
PYTHON_REQ: [exact python requirement]
CLI_ENTRY: [exact entry point like "hrisa = hrisa_code.cli:app"]

Start by reading the file."""

        response = await self.conversation.process_message(prompt)

        # Parse the structured response
        name_match = re.search(r'PROJECT_NAME:\s*(.+?)(?:\n|$)', response)
        desc_match = re.search(r'PROJECT_DESC:\s*(.+?)(?:\n|$)', response)
        version_match = re.search(r'VERSION:\s*(.+?)(?:\n|$)', response)
        python_match = re.search(r'PYTHON_REQ:\s*(.+?)(?:\n|$)', response)
        cli_match = re.search(r'CLI_ENTRY:\s*(.+?)(?:\n|$)', response)

        self.facts = {
            "name": name_match.group(1).strip() if name_match else "UNKNOWN",
            "description": desc_match.group(1).strip() if desc_match else "UNKNOWN",
            "version": version_match.group(1).strip() if version_match else "0.0.0",
            "python_requires": python_match.group(1).strip() if python_match else ">=3.10",
            "cli_entry": cli_match.group(1).strip() if cli_match else "UNKNOWN",
            "raw_response": response,
        }

        # Validation
        if self.facts["name"] == "UNKNOWN":
            self.console.print("[red]✗ Could not extract project name![/red]")
        else:
            self.console.print(f"[green]✓[/green] Facts extracted: {self.facts['name']}")

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

        # Direct assembly - no LLM needed!
        name = self.facts.get("name", "UNKNOWN")
        description = self.facts.get("description", "UNKNOWN")

        section = f"""# {name} - Project Guide for AI Assistants

This document provides context and guidelines for AI coding assistants (like Claude Code) working on this project.

## Project Overview

**{name}** - {description}

### Quick Links
- [Architecture](#architecture)
- [Key Components](#key-components)
- [Available Tools](#available-tools)
- [Development Practices](#development-practices)
- [Common Tasks](#common-tasks)
"""

        self.sections["title"] = section

        # Validation
        if name.lower() in section.lower():
            self.console.print(f"[green]✓[/green] Title section built: {name}")
        else:
            self.console.print(f"[red]✗[/red] Validation failed for title")

        return section

    async def build_architecture_section(self) -> str:
        """Phase 3: Build architecture section from actual directory structure.

        Returns:
            Architecture section markdown
        """
        self.console.print(Panel(
            "[bold cyan]Phase 3: Architecture Section[/bold cyan]\n"
            "Discovering actual project structure...",
            border_style="cyan"
        ))

        prompt = f"""DISCOVER PROJECT ARCHITECTURE (DIRECTORY-BASED ONLY)

Task: Document the actual project architecture from directory structure.

Steps:
1. Use list_directory on {self.project_path}/src/
2. Identify the main package name and subdirectories
3. List key files in core/, tools/, and other directories
4. Check for tests/, docs/, examples/ directories

CRITICAL RULES:
- Only document directories and files that ACTUALLY EXIST
- Show the real structure, not an idealized one
- Group files by their purpose (core logic, tools, etc.)
- Output PURE MARKDOWN

Output format (EXACT):
## Architecture

### Project Structure

```
project-name/
├── src/
│   └── package_name/
│       ├── core/          # [What's actually here]
│       │   ├── file1.py
│       │   └── file2.py
│       ├── tools/         # [If it exists]
│       │   └── file.py
│       └── cli.py         # [Main entry point]
├── tests/                 # [If it exists]
├── docs/                  # [If it exists]
└── pyproject.toml
```

### Key Directories

- `src/package/core/`: [What's actually in this directory]
- `src/package/tools/`: [If it exists, what's here]
- `tests/`: [Testing infrastructure]

[etc.]

Output ONLY markdown."""

        section = await self.conversation.process_message(prompt)

        # Clean up markdown fences
        section = section.strip()
        if section.startswith("```markdown"):
            section = section[len("```markdown"):].strip()
        if section.startswith("```"):
            section = section[3:].strip()
        if section.endswith("```"):
            section = section[:-3].strip()

        self.sections["architecture"] = section

        self.console.print("[green]✓[/green] Architecture section built from actual directories")
        return section

    async def build_components_section(self) -> str:
        """Phase 4: Build components section from core/*.py files.

        Returns:
            Components section markdown
        """
        self.console.print(Panel(
            "[bold cyan]Phase 4: Key Components Section[/bold cyan]\n"
            "Discovering core components from actual code...",
            border_style="cyan"
        ))

        prompt = f"""DISCOVER KEY COMPONENTS (CODE-BASED ONLY)

Task: Document the purpose and responsibilities of key components.

Steps:
1. Use list_directory on {self.project_path}/src/[package]/core/
2. Read key files like cli.py, config.py, conversation.py, interactive.py
3. For each file:
   - Extract main classes
   - Extract key functions
   - Note what the module does (from docstrings)

CRITICAL RULES:
- Only document files that ACTUALLY EXIST
- Extract EXACT information from code and docstrings
- Focus on what each component DOES, not implementation details
- Output PURE MARKDOWN

Output format (EXACT):
## Key Components

### CLI Entry Point (`cli.py`)

Main entry point with Typer commands.

**Key Commands**:
- `chat` - [What it does]
- `models` - [What it does]
[etc.]

### Core Modules

#### `config.py`

[What this module does - from docstring]

**Key Classes**:
- `Config` - [Purpose]
- `ModelConfig` - [Purpose]

#### `conversation.py`

[What this module does]

**Key Classes**:
- `ConversationManager` - [Purpose and responsibilities]

[Repeat for each core module found]

Output ONLY markdown."""

        section = await self.conversation.process_message(prompt)

        # Clean up markdown fences
        section = section.strip()
        if section.startswith("```markdown"):
            section = section[len("```markdown"):].strip()
        if section.startswith("```"):
            section = section[3:].strip()
        if section.endswith("```"):
            section = section[:-3].strip()

        self.sections["components"] = section

        self.console.print("[green]✓[/green] Components section built from actual code")
        return section

    async def build_tools_section(self) -> str:
        """Phase 5: Build tools section from tools/*.py files.

        Returns:
            Tools section markdown
        """
        self.console.print(Panel(
            "[bold cyan]Phase 5: Available Tools Section[/bold cyan]\n"
            "Discovering tools from tools/*.py files...",
            border_style="cyan"
        ))

        prompt = f"""DISCOVER AVAILABLE TOOLS (CODE-BASED ONLY)

Task: Document all tools available to the LLM.

Steps:
1. Use find_files with pattern="**/tools/*.py" from {self.project_path}
2. Read each tool file (e.g., file_operations.py, git_operations.py)
3. For each tool class with get_definition() method:
   - Extract tool name (from schema)
   - Extract description
   - Extract key parameters
   - Note what the tool does

CRITICAL RULES:
- Only document tools with get_definition() method
- Extract EXACT descriptions from code
- Group tools by category (File Operations, Git Operations, etc.)
- Output PURE MARKDOWN

Output format (EXACT):
## Available Tools

### Tool System Overview

[Brief explanation of how tools work in this project]

### File Operations Tools

#### `read_file`

**Purpose**: [Exact description from tool definition]

**Key Parameters**:
- `file_path` (str): Path to file
- `offset` (int, optional): Line offset
[etc.]

#### `write_file`

[Same format]

### Git Operations Tools

[Same structure]

Output ONLY markdown."""

        section = await self.conversation.process_message(prompt)

        # Clean up markdown fences
        section = section.strip()
        if section.startswith("```markdown"):
            section = section[len("```markdown"):].strip()
        if section.startswith("```"):
            section = section[3:].strip()
        if section.endswith("```"):
            section = section[:-3].strip()

        self.sections["tools"] = section

        self.console.print("[green]✓[/green] Tools section built from actual code")
        return section

    async def build_development_section(self) -> str:
        """Phase 6: Build development practices section.

        Returns:
            Development section markdown
        """
        self.console.print(Panel(
            "[bold cyan]Phase 6: Development Practices Section[/bold cyan]\n"
            "Discovering development practices from configs and tests...",
            border_style="cyan"
        ))

        prompt = f"""DISCOVER DEVELOPMENT PRACTICES (CONFIG-BASED ONLY)

Task: Document development practices from actual configuration.

Steps:
1. Read {self.project_path}/pyproject.toml for tool configs:
   - [tool.black], [tool.ruff], [tool.mypy], [tool.pytest]
2. Check if {self.project_path}/Makefile exists and read it
3. Identify testing infrastructure in tests/ directory
4. Check for pre-commit hooks or CI configuration

CRITICAL RULES:
- Only document tools/practices that ARE CONFIGURED
- Extract EXACT settings from config files
- Include actual commands from Makefile
- Output PURE MARKDOWN

Output format (EXACT):
## Development Practices

### Code Style

This project uses [tools found in config]:

**Formatting**: [Tool name and key settings]
**Linting**: [Tool name and key settings]
**Type Checking**: [If configured]

### Testing

**Framework**: [pytest or other]
**Location**: [Where tests live]
**Run Tests**:
```bash
[actual command from Makefile or docs]
```

### Git Workflow

**Branch Naming**: [From actual commits or docs]
**Commit Style**: [Conventional commits? From git log]

### Common Commands

From Makefile:
```bash
make setup     # [What it does]
make test      # [What it does]
[etc.]
```

Output ONLY markdown."""

        section = await self.conversation.process_message(prompt)

        # Clean up markdown fences
        section = section.strip()
        if section.startswith("```markdown"):
            section = section[len("```markdown"):].strip()
        if section.startswith("```"):
            section = section[3:].strip()
        if section.endswith("```"):
            section = section[:-3].strip()

        self.sections["development"] = section

        self.console.print("[green]✓[/green] Development section built from actual configs")
        return section

    async def assemble_hrisa(self) -> str:
        """Phase 7: Assemble final HRISA.md (no synthesis thinking).

        Returns:
            Complete HRISA.md markdown
        """
        self.console.print(Panel(
            "[bold cyan]Phase 7: Assembly[/bold cyan]\n"
            "Combining validated sections...",
            border_style="cyan"
        ))

        # Simple string concatenation - no LLM needed!
        hrisa_parts = [
            self.sections.get("title", "# Project Guide\\n"),
            "\n",
            self.sections.get("architecture", "## Architecture\\n\\nTODO\\n"),
            "\n",
            self.sections.get("components", "## Key Components\\n\\nTODO\\n"),
            "\n",
            self.sections.get("tools", "## Available Tools\\n\\nTODO\\n"),
            "\n",
            self.sections.get("development", "## Development Practices\\n\\nTODO\\n"),
            "\n## Common Tasks\\n\\n"
            "[This section would be populated with common coding tasks and examples]\\n",
            "\n## Notes for AI Assistants\\n\\n"
            "- Be careful with file operations (this is a CLI tool)\\n"
            "- Always run tests after making changes\\n"
            "- Keep documentation in sync with code\\n"
            "- Respect the modular architecture\\n",
        ]

        # Join and clean up extra newlines
        hrisa = "\n".join(hrisa_parts)
        hrisa = re.sub(r'\n{3,}', '\n\n', hrisa)

        # Final validation
        project_name = self.facts.get("name", "UNKNOWN")
        if project_name.lower() not in hrisa.lower():
            self.console.print(f"[red]✗ VALIDATION FAILED: Project name '{project_name}' not in final HRISA.md[/red]")
        else:
            self.console.print(f"[green]✓[/green] Final validation passed: {project_name}")

        return hrisa

    async def generate(self) -> str:
        """Execute progressive HRISA.md generation workflow.

        Returns:
            Generated HRISA.md content
        """
        self.console.print(Panel(
            "[bold]Progressive HRISA.md Generation[/bold]\\n"
            f"Project: {self.project_path}\\n"
            "Strategy: Extract → Build → Validate → Assemble",
            title="► Starting Progressive Orchestration",
            border_style="bold cyan"
        ))

        try:
            # Phase 1: Extract facts
            await self.extract_facts()

            # Phase 2-6: Build sections incrementally
            await self.build_title_section()
            await self.build_architecture_section()
            await self.build_components_section()
            await self.build_tools_section()
            await self.build_development_section()

            # Phase 7: Assemble (no synthesis)
            hrisa = await self.assemble_hrisa()

            # Write to file
            output_path = self.project_path / "HRISA.md"
            output_path.write_text(hrisa)

            self.console.print(Panel(
                f"[green]✓ HRISA.md generated successfully![/green]\\n\\n"
                f"Output: {output_path}\\n"
                f"Sections: {len(self.sections)}\\n"
                f"Validated: ✓",
                title="► Complete",
                border_style="bold green"
            ))

            return hrisa

        except Exception as e:
            self.console.print(f"[red]✗ Error during progressive generation: {e}[/red]")
            raise
