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
from typing import Dict, Any
from hrisa_code.core.conversation import ConversationManager
from hrisa_code.core.orchestrators.progressive_base import (
    ProgressiveBaseOrchestrator,
    PhaseDefinition,
    ProgressiveWorkflow,
)
from hrisa_code.tools.cli_introspection import validate_content_quality


class ProgressiveContributingOrchestrator(ProgressiveBaseOrchestrator):
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

    @property
    def workflow_definition(self) -> ProgressiveWorkflow:
        """Define the CONTRIBUTING.md generation workflow.

        Returns:
            Progressive workflow with all phases
        """
        return ProgressiveWorkflow(
            name="CONTRIBUTING",
            description="Generate comprehensive CONTRIBUTING.md documentation progressively",
            output_filename="CONTRIBUTING.md",
            phases=[
                PhaseDefinition(
                    name="title",
                    display_name="Title Section",
                    description="Building title with validated project name...",
                    uses_llm=False,
                ),
                PhaseDefinition(
                    name="getting_started",
                    display_name="Getting Started Section",
                    description="Discovering actual setup process...",
                    uses_llm=True,  # Uses LLM to read Makefile
                ),
                PhaseDefinition(
                    name="code_standards",
                    display_name="Code Standards Section",
                    description="Extracting code quality tools...",
                    uses_llm=True,  # Uses LLM to discover tools
                ),
                PhaseDefinition(
                    name="workflow",
                    display_name="Workflow Section",
                    description="Documenting development workflow...",
                    uses_llm=True,  # Uses LLM for git workflow
                ),
                PhaseDefinition(
                    name="project_structure",
                    display_name="Project Structure Section",
                    description="Mapping project layout...",
                    uses_llm=True,  # Uses LLM to explain structure
                ),
            ],
            audience="open-source contributors",
        )

    async def extract_facts(self) -> Dict[str, Any]:
        """Phase 1: Extract ground-truth facts using static analysis.

        Returns:
            Validated facts dictionary
        """
        metadata = self.extract_project_metadata()

        self.facts = {
            "name": metadata.get("name", "UNKNOWN"),
            "description": metadata.get("description", "UNKNOWN"),
            "python_requires": metadata.get("python_requires", ">=3.10"),
        }

        return self.facts

    async def build_title_section(self) -> str:
        """Phase 2: Build title section using validated facts.

        Returns:
            Title section markdown
        """
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

        return section

    async def build_getting_started_section(self) -> str:
        """Phase 3: Build getting started section from actual setup files.

        Returns:
            Getting started section markdown
        """
        python_req = self.facts.get("python_requires", ">=3.10")

        prompt = f"""DISCOVER SETUP PROCESS (FILE-BASED ONLY)

Task: Document how contributors actually set up the development environment.

Steps:
1. Check if {self.project_path}/Makefile exists and read it
2. Look for setup-related targets (setup, install, dev-setup, etc.)
3. Check for requirements files or pyproject.toml dev dependencies
4. Identify the actual setup commands used

OUTPUT FORMAT (markdown):
## Getting Started

### Prerequisites
- Python {python_req}
- [other prerequisites from Makefile or docs]

### Development Setup
```bash
[actual commands from Makefile or discovered setup process]
```

CRITICAL: Report ONLY actual commands/targets found. Do NOT invent steps."""

        response = await self.conversation.process_message(prompt)
        return response.strip()

    async def build_code_standards_section(self) -> str:
        """Phase 4: Build code standards section from actual tool configs.

        Returns:
            Code standards section markdown
        """
        prompt = f"""DISCOVER CODE QUALITY TOOLS (FILE-BASED ONLY)

Task: Document the actual code quality tools configured for this project.

Steps:
1. Read {self.project_path}/pyproject.toml [tool.*] sections
2. Check for .pre-commit-config.yaml, .black, .ruff.toml, etc.
3. Identify: formatter (black/ruff), linter (ruff/flake8), type checker (mypy), tests (pytest)

OUTPUT FORMAT (markdown):
## Code Standards

### Code Formatting
- Tool: [actual tool name]
- Config: [location of config]
- Command: `[actual command]`

### Linting
- Tool: [actual tool]
- Command: `[actual command]`

### Type Checking
- Tool: [actual tool if configured]
- Command: `[actual command]`

### Testing
- Framework: [actual framework]
- Command: `[actual command]`

CRITICAL: Report ONLY tools that are actually configured."""

        response = await self.conversation.process_message(prompt)
        return response.strip()

    async def build_workflow_section(self) -> str:
        """Phase 5: Build workflow section from git and GitHub configs.

        Returns:
            Workflow section markdown
        """
        prompt = f"""DISCOVER DEVELOPMENT WORKFLOW

Task: Document the actual development workflow for contributors.

Steps:
1. Check {self.project_path}/.github/ for PR templates, issue templates, workflows
2. Read git branch structure from recent commits
3. Identify testing/CI requirements

OUTPUT FORMAT (markdown):
## Development Workflow

### Branching Strategy
[Describe actual branch naming from .github or git history]

### Making Changes
1. Create feature branch
2. Make changes and test
3. Commit with descriptive message
4. [any other actual steps]

### Pull Requests
[Requirements from .github/PULL_REQUEST_TEMPLATE.md if it exists]

### Code Review
[Process based on .github configs]

CRITICAL: Base on actual files, not assumptions."""

        response = await self.conversation.process_message(prompt)
        return response.strip()

    async def build_project_structure_section(self) -> str:
        """Phase 6: Build project structure section from actual layout.

        Returns:
            Project structure section markdown
        """
        prompt = f"""DOCUMENT PROJECT STRUCTURE

Task: Explain the actual project layout for new contributors.

Steps:
1. List main directories in {self.project_path}/src/
2. Explain purpose of each major component
3. Include tests/, docs/, examples/ if they exist

OUTPUT FORMAT (markdown):
## Project Structure

```
[actual directory tree with explanations]
```

### Key Directories
- `src/`: [actual description]
- `tests/`: [actual description]
- [other actual directories]

CRITICAL: Show actual structure, not idealized version."""

        response = await self.conversation.process_message(prompt)
        return response.strip()

    async def assemble_document(self) -> str:
        """Phase 7: Assemble final CONTRIBUTING.md with quality validation.

        Returns:
            Complete CONTRIBUTING.md markdown
        """
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
            "\n## Questions?\n\nFeel free to open an issue for questions or discussions.\n",
        ]

        contributing = "\n".join(contributing_parts)
        contributing = re.sub(r"\n{3,}", "\n\n", contributing)

        is_valid, errors = validate_content_quality(contributing)

        if not is_valid:
            self.console.print("[red]✗ Content quality validation FAILED:[/red]")
            for error in errors:
                self.console.print(f"  • {error}")
            raise ValueError(f"Content quality validation failed: {len(errors)} issues found")

        project_name = self.facts.get("name", "UNKNOWN")
        if project_name.lower() not in contributing.lower():
            self.console.print(
                f"[red]✗ VALIDATION FAILED: Project name '{project_name}' not in final CONTRIBUTING.md[/red]"
            )
        else:
            self.console.print(
                f"[green]✓[/green] Content validation passed: clean, accurate documentation"
            )

        output_path = self.project_path / "CONTRIBUTING.md"
        output_path.write_text(contributing)

        return contributing
