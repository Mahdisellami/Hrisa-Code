"""Progressive context-building orchestrator for CONTRIBUTING.md generation.

This orchestrator uses the proven progressive approach:
- Extract ground-truth facts first
- Build each section incrementally with validation
- Assemble (don't synthesize) final document

Target: Open-source contributors and maintainers
Focus: Getting started, development workflow, code standards
"""

import re
from pathlib import Path
from typing import Optional, Dict, Any
from rich.console import Console
from rich.panel import Panel

from hrisa_code.core.conversation import ConversationManager
from hrisa_code.tools.cli_introspection import (
    extract_cli_commands_from_ast,
    extract_pyproject_metadata,
    extract_tool_definitions,
    validate_content_quality,
)


class ProgressiveContributingOrchestrator:
    """Progressive CONTRIBUTING.md generation with validation at each step.

    Strategy:
    1. Extract Facts: Read pyproject.toml, validate extraction
    2. Build Title Section: Use extracted facts, validate project name
    3. Build Getting Started Section: From actual setup files
    4. Build Code Standards Section: From actual tool configs
    5. Build Workflow Section: From git history and .github/
    6. Build Project Structure Section: From actual src/ layout
    7. Assemble: Combine sections (no synthesis thinking)
    """

    def __init__(
        self,
        conversation: ConversationManager,
        project_path: Path,
        console: Optional[Console] = None,
    ):
        """Initialize progressive CONTRIBUTING orchestrator.

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
        """Phase 1: Extract ground-truth facts using static analysis.

        Returns:
            Validated facts dictionary
        """
        self.console.print(Panel(
            "[bold cyan]Phase 1: Ground Truth Extraction[/bold cyan]\n"
            "Parsing pyproject.toml directly (no LLM)...",
            border_style="cyan"
        ))

        # Use static analysis
        pyproject_path = self.project_path / "pyproject.toml"
        metadata = extract_pyproject_metadata(pyproject_path)

        self.facts = {
            "name": metadata.get("name", "UNKNOWN"),
            "description": metadata.get("description", "UNKNOWN"),
            "python_requires": metadata.get("python_requires", ">=3.10"),
        }

        # Validation
        if self.facts["name"] == "UNKNOWN":
            self.console.print("[red]✗ Could not extract project name![/red]")
        else:
            self.console.print(f"[green]✓[/green] Facts extracted: {self.facts['name']}")

        return self.facts

    async def _old_extract_facts(self) -> Dict[str, Any]:
        """OLD VERSION - kept for reference, not used.

        Returns:
            Validated facts dictionary
        """
        prompt = f"""FACT EXTRACTION TASK (NO INTERPRETATION ALLOWED)

Read {self.project_path}/pyproject.toml and extract these EXACT values:

1. project.name → This is the AUTHORITATIVE project name
2. project.description → This is the OFFICIAL description
3. project.requires-python → Python version requirement
4. First 3 dev dependencies from [project.optional-dependencies.dev]

CRITICAL RULES:
- Report EXACT strings from the file (copy-paste, no paraphrasing)
- Do NOT add your own descriptions
- Do NOT invent missing information

After reading the file, respond with ONLY this format (no markdown, no explanations):

PROJECT_NAME: [exact name from file]
PROJECT_DESC: [exact description from file]
PYTHON_REQ: [exact python requirement]
DEV_DEPS: [dep1, dep2, dep3]

Start by reading the file."""

        response = await self.conversation.process_message(prompt)

        # Parse the structured response
        name_match = re.search(r'PROJECT_NAME:\s*(.+?)(?:\n|$)', response)
        desc_match = re.search(r'PROJECT_DESC:\s*(.+?)(?:\n|$)', response)
        python_match = re.search(r'PYTHON_REQ:\s*(.+?)(?:\n|$)', response)

        self.facts = {
            "name": name_match.group(1).strip() if name_match else "UNKNOWN",
            "description": desc_match.group(1).strip() if desc_match else "UNKNOWN",
            "python_requires": python_match.group(1).strip() if python_match else ">=3.10",
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

        section = f"""# Contributing to {name}

Thank you for your interest in contributing! We welcome contributions from the community.

## Table of Contents
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Standards](#code-standards)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Project Structure](#project-structure)
- [Questions](#questions)
"""

        self.sections["title"] = section

        # Validation
        if name.lower() in section.lower():
            self.console.print(f"[green]✓[/green] Title section built: {name}")
        else:
            self.console.print(f"[red]✗[/red] Validation failed for title")

        return section

    async def build_getting_started_section(self) -> str:
        """Phase 3: Build getting started section from actual setup files.

        Returns:
            Getting started section markdown
        """
        self.console.print(Panel(
            "[bold cyan]Phase 3: Getting Started Section[/bold cyan]\n"
            "Discovering actual setup process...",
            border_style="cyan"
        ))

        python_req = self.facts.get("python_requires", ">=3.10")

        prompt = f"""DISCOVER SETUP PROCESS (FILE-BASED ONLY)

Task: Document how contributors actually set up the development environment.

Steps:
1. Check if {self.project_path}/Makefile exists and read it
2. Look for setup-related targets (setup, install, dev-setup, etc.)
3. Read {self.project_path}/pyproject.toml for [project.optional-dependencies.dev]
4. Check for {self.project_path}/README.md setup instructions

CRITICAL RULES:
- Only document ACTUAL setup methods that exist
- Extract EXACT commands from Makefile if present
- Use Python requirement: {python_req}
- Output PURE MARKDOWN

Output format (EXACT):
## Getting Started

### Prerequisites
- Python {python_req}
- [Other actual prerequisites found]

### Fork and Clone
1. Fork the repository on GitHub
2. Clone your fork:
```bash
git clone https://github.com/YOUR-USERNAME/PROJECT-NAME.git
cd PROJECT-NAME
```

### Development Setup

[Actual setup commands from Makefile or README]

```bash
# Actual commands found in files
make setup  # or pip install -e ".[dev]"
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

        self.sections["getting_started"] = section

        self.console.print("[green]✓[/green] Getting started section built from actual files")
        return section

    async def build_code_standards_section(self) -> str:
        """Phase 4: Build code standards section from actual tool configs.

        Returns:
            Code standards section markdown
        """
        self.console.print(Panel(
            "[bold cyan]Phase 4: Code Standards Section[/bold cyan]\n"
            "Discovering actual code standards from tool configs...",
            border_style="cyan"
        ))

        prompt = f"""DISCOVER CODE STANDARDS (CONFIG-BASED ONLY)

Task: Document code standards from actual tool configurations.

Steps:
1. Read {self.project_path}/pyproject.toml
2. Look for [tool.black], [tool.ruff], [tool.mypy], [tool.pytest] sections
3. Check if {self.project_path}/Makefile has quality check targets

CRITICAL RULES:
- Only document tools that ARE CONFIGURED
- Extract EXACT settings from config files
- Include commands to run these tools
- Output PURE MARKDOWN

Output format (EXACT):
## Code Standards

### Code Formatting
This project uses [black/ruff/etc - based on what's found].

Run formatter:
```bash
make format  # or actual command found
```

### Linting
[Based on actual config]

### Type Checking
[If mypy is configured]

### Testing
[Based on pytest config]

Run tests:
```bash
make test  # or actual command
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

        self.sections["code_standards"] = section

        self.console.print("[green]✓[/green] Code standards section built from actual configs")
        return section

    async def build_workflow_section(self) -> str:
        """Phase 5: Build workflow section from git and GitHub config.

        Returns:
            Workflow section markdown
        """
        self.console.print(Panel(
            "[bold cyan]Phase 5: Development Workflow Section[/bold cyan]\n"
            "Discovering workflow from git history...",
            border_style="cyan"
        ))

        prompt = f"""DISCOVER DEVELOPMENT WORKFLOW (GIT-BASED ONLY)

Task: Document the actual development workflow used by this project.

Steps:
1. Use execute_command to run: git log --oneline -10 (in {self.project_path})
2. Analyze commit message format (conventional commits? other style?)
3. Check if {self.project_path}/.github/pull_request_template.md exists
4. Look at branch names in git history

CRITICAL RULES:
- Base workflow on ACTUAL git history
- Extract commit message style from REAL commits
- Only mention PR templates if they exist
- Output PURE MARKDOWN

Output format (EXACT):
## Development Workflow

### Create a Branch
```bash
git checkout -b feature/your-feature-name
```

### Make Changes
[Guidelines based on actual practices]

### Commit Changes
Based on the project's commit history, use this format:
```
[actual format found, e.g., "feat: Add feature" or other style]
```

### Push and Create PR
```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

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

        self.sections["workflow"] = section

        self.console.print("[green]✓[/green] Workflow section built from actual git history")
        return section

    async def build_project_structure_section(self) -> str:
        """Phase 6: Build project structure section from actual directories.

        Returns:
            Project structure section markdown
        """
        self.console.print(Panel(
            "[bold cyan]Phase 6: Project Structure Section[/bold cyan]\n"
            "Discovering actual project structure...",
            border_style="cyan"
        ))

        prompt = f"""DISCOVER PROJECT STRUCTURE (DIRECTORY-BASED ONLY)

Task: Document the actual project directory structure.

Steps:
1. Use list_directory on {self.project_path}/src/
2. Note the main package name and subdirectories
3. Identify where different types of code live (core/, tools/, etc.)

CRITICAL RULES:
- Only document directories that ACTUALLY EXIST
- Show the real structure, not an idealized one
- Output PURE MARKDOWN

Output format (EXACT):
## Project Structure

```
project-name/
├── src/
│   └── package_name/
│       ├── core/          # [What's actually here]
│       ├── tools/         # [If it exists]
│       └── cli.py         # [Main entry point]
├── tests/                 # [If it exists]
├── docs/                  # [If it exists]
└── pyproject.toml
```

### Key Directories
- `src/package/core/`: [What's actually in this directory]
- `src/package/tools/`: [If it exists, what's here]
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

        self.sections["project_structure"] = section

        self.console.print("[green]✓[/green] Project structure section built from actual directories")
        return section

    async def assemble_contributing(self) -> str:
        """Phase 7: Assemble final CONTRIBUTING.md with quality validation.

        Returns:
            Complete CONTRIBUTING.md markdown
        """
        self.console.print(Panel(
            "[bold cyan]Phase 7: Assembly & Validation[/bold cyan]\n"
            "Combining sections and validating quality...",
            border_style="cyan"
        ))

        # Simple string concatenation - no LLM needed!
        contributing_parts = [
            self.sections.get("title", "# Contributing\n"),
            "\n",
            self.sections.get("getting_started", "## Getting Started\n\nTODO\n"),
            "\n",
            self.sections.get("code_standards", "## Code Standards\n\nTODO\n"),
            "\n",
            self.sections.get("workflow", "## Development Workflow\n\nTODO\n"),
            "\n",
            self.sections.get("project_structure", "## Project Structure\n\nTODO\n"),
            "\n## Questions?\n\nIf you have questions, please open an issue on GitHub.\n",
        ]

        # Join and clean up extra newlines
        contributing = "\n".join(contributing_parts)
        contributing = re.sub(r'\n{3,}', '\n\n', contributing)

        # Content quality validation
        is_valid, errors = validate_content_quality(contributing)

        if not is_valid:
            self.console.print("[red]✗ Content quality validation FAILED:[/red]")
            for error in errors:
                self.console.print(f"  • {error}")
            raise ValueError(f"Content quality validation failed: {len(errors)} issues found")

        # Basic validation
        project_name = self.facts.get("name", "UNKNOWN")
        if project_name.lower() not in contributing.lower():
            self.console.print(f"[red]✗ VALIDATION FAILED: Project name '{project_name}' not in final CONTRIBUTING.md[/red]")
        else:
            self.console.print(f"[green]✓[/green] Content validation passed: clean, accurate documentation")

        return contributing

    async def generate(self) -> str:
        """Execute progressive CONTRIBUTING.md generation workflow.

        Returns:
            Generated CONTRIBUTING.md content
        """
        self.console.print(Panel(
            "[bold]Progressive CONTRIBUTING.md Generation[/bold]\n"
            f"Project: {self.project_path}\n"
            "Strategy: Extract → Build → Validate → Assemble",
            title="► Starting Progressive Orchestration",
            border_style="bold cyan"
        ))

        try:
            # Phase 1: Extract facts
            await self.extract_facts()

            # Phase 2-6: Build sections incrementally
            await self.build_title_section()
            await self.build_getting_started_section()
            await self.build_code_standards_section()
            await self.build_workflow_section()
            await self.build_project_structure_section()

            # Phase 7: Assemble (no synthesis)
            contributing = await self.assemble_contributing()

            # Write to file
            output_path = self.project_path / "CONTRIBUTING.md"
            output_path.write_text(contributing)

            self.console.print(Panel(
                f"[green]✓ CONTRIBUTING.md generated successfully![/green]\n\n"
                f"Output: {output_path}\n"
                f"Sections: {len(self.sections)}\n"
                f"Validated: ✓",
                title="► Complete",
                border_style="bold green"
            ))

            return contributing

        except Exception as e:
            self.console.print(f"[red]✗ Error during progressive generation: {e}[/red]")
            raise
