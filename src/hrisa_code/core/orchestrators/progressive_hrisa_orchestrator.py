"""Progressive context-building orchestrator for HRISA.md generation.

This orchestrator uses the proven progressive approach:
- Extract ground-truth facts first
- Build each section incrementally with validation
- Assemble (don't synthesize) final document

Target: AI coding assistants (like Claude Code)
Focus: Complete technical internals, architecture, development guide
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
from hrisa_code.tools.cli_introspection import (
    extract_tool_definitions,
    validate_content_quality,
)


class ProgressiveHrisaOrchestrator(ProgressiveBaseOrchestrator):
    """Progressive HRISA.md generation with validation at each step.

    Strategy:
    1. Extract Facts: Read pyproject.toml, validate extraction
    2. Build Title Section: Use extracted facts, validate project name
    3. Build Architecture Section: Technical internals for AI assistants
    4. Build Components Section: Core classes and their responsibilities
    5. Build Tools Section: Available tools with signatures
    6. Build Development Section: Contribution guide for AI assistants
    7. Assemble: Combine sections (no synthesis thinking)
    """

    @property
    def workflow_definition(self) -> ProgressiveWorkflow:
        """Define the HRISA.md generation workflow.

        Returns:
            Progressive workflow with all phases
        """
        return ProgressiveWorkflow(
            name="HRISA",
            description="Generate comprehensive HRISA.md documentation progressively for AI assistants",
            output_filename="HRISA.md",
            phases=[
                PhaseDefinition(
                    name="title",
                    display_name="Title Section",
                    description="Building title with validated project name...",
                    uses_llm=False,
                ),
                PhaseDefinition(
                    name="architecture",
                    display_name="Architecture Section",
                    description="Documenting technical architecture...",
                    uses_llm=True,  # Uses LLM for architecture analysis
                ),
                PhaseDefinition(
                    name="components",
                    display_name="Components Section",
                    description="Mapping core components...",
                    uses_llm=True,  # Uses LLM for component discovery
                ),
                PhaseDefinition(
                    name="tools",
                    display_name="Tools Section",
                    description="Extracting tool definitions...",
                    uses_llm=False,  # Static analysis
                ),
                PhaseDefinition(
                    name="development",
                    display_name="Development Section",
                    description="Documenting development practices...",
                    uses_llm=True,  # Uses LLM for workflow documentation
                ),
            ],
            audience="AI coding assistants",
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
            "version": metadata.get("version", "0.0.0"),
            "python_requires": metadata.get("python_requires", ">=3.10"),
        }

        return self.facts

    async def build_title_section(self) -> str:
        """Phase 2: Build title section using validated facts.

        Returns:
            Title section markdown
        """
        name = self.facts.get("name", "UNKNOWN")
        description = self.facts.get("description", "UNKNOWN")

        section = f"""# {name} - HRISA Documentation

> **Human-Readable Instructions for Software Assistants**

{description}

## Purpose

This document provides comprehensive technical documentation specifically designed for AI coding assistants (like Claude Code). It includes:

- Complete architecture overview
- Core component details
- Available tools and APIs
- Development practices
- File structure and conventions

## Quick Reference

- **Language**: Python {self.facts.get('python_requires', '3.10+')}
- **Version**: {self.facts.get('version', '0.1.0')}
- **Package**: `{name}`

## Table of Contents

- [Architecture](#architecture)
- [Core Components](#core-components)
- [Tools](#tools)
- [Development Guide](#development-guide)
"""

        return section

    async def build_architecture_section(self) -> str:
        """Phase 3: Build architecture section with technical details.

        Returns:
            Architecture section markdown
        """
        prompt = f"""DOCUMENT TECHNICAL ARCHITECTURE

Task: Explain the technical architecture for an AI coding assistant.

Steps:
1. Read src/{self.facts.get('name', 'project')}/core/ to understand core modules
2. Identify main architectural patterns (async, event-driven, etc.)
3. Map data flow and component relationships
4. Document key design decisions

OUTPUT FORMAT (markdown):
## Architecture

### High-Level Design
[Describe overall architecture: CLI → Core → LLM integration → Tools]

### Core Modules
- **Module Name**: Brief description and responsibility
- **Module Name**: Brief description and responsibility

### Design Patterns
- Pattern: Usage and rationale
- Pattern: Usage and rationale

### Data Flow
[Describe how data flows through the system]

CRITICAL: Focus on technical details useful for an AI assistant modifying code."""

        response = await self.conversation.process_message(prompt)
        return response.strip()

    async def build_components_section(self) -> str:
        """Phase 4: Build components section with class details.

        Returns:
            Components section markdown
        """
        prompt = f"""DOCUMENT CORE COMPONENTS

Task: Document key classes and their responsibilities for an AI assistant.

Steps:
1. Read src/{self.facts.get('name')}/core/*.py files
2. Identify main classes (ConversationManager, OllamaClient, TaskManager, etc.)
3. Document their public APIs and responsibilities
4. Note important methods and their signatures

OUTPUT FORMAT (markdown):
## Core Components

### Class: ComponentName (`module.py`)

**Purpose**: Brief description

**Key Methods**:
- `method_name(args) -> return_type`: Description
- `method_name(args) -> return_type`: Description

**Usage**:
```python
# Example usage
```

[Repeat for each major component]

CRITICAL: Include method signatures for AI assistant reference."""

        response = await self.conversation.process_message(prompt)
        return response.strip()

    async def build_tools_section(self) -> str:
        """Phase 5: Build tools section using static analysis.

        Returns:
            Tools section markdown
        """
        tools_dir = self.project_path / "src" / "hrisa_code" / "tools"
        if not tools_dir.exists():
            tools_dir = self.project_path / "tools"

        tools = extract_tool_definitions(tools_dir)

        section = "## Tools\n\n"
        section += "The system provides these tools for file operations, git integration, and execution:\n\n"

        if tools:
            for tool in tools:
                section += f"### `{tool['name']}`\n\n"
                section += f"**Source**: `{tool['file']}`\n\n"
                if tool["description"]:
                    section += f"**Description**: {tool['description']}\n\n"
                section += "**Tool Definition**: Available via `get_definition()` method\n\n"
        else:
            section += "No tools found.\n"

        return section

    async def build_development_section(self) -> str:
        """Phase 6: Build development guide section.

        Returns:
            Development section markdown
        """
        prompt = f"""DOCUMENT DEVELOPMENT PRACTICES

Task: Document development practices for an AI assistant contributing code.

Steps:
1. Read pyproject.toml for code quality tools
2. Check for testing framework and conventions
3. Identify file naming patterns
4. Document code style requirements

OUTPUT FORMAT (markdown):
## Development Guide

### Code Standards
- **Formatter**: [tool and config]
- **Linter**: [tool and config]
- **Type Checking**: [tool and config]
- **Testing**: [framework and location]

### File Organization
```
src/
├── core/       [purpose]
├── tools/      [purpose]
└── ...
```

### Adding New Features
1. [Where to add code]
2. [How to test]
3. [Conventions to follow]

### Common Tasks
- Adding a new tool: [steps]
- Adding a CLI command: [steps]
- Modifying orchestrators: [steps]

CRITICAL: Be specific and actionable for an AI assistant."""

        response = await self.conversation.process_message(prompt)
        return response.strip()

    async def assemble_document(self) -> str:
        """Phase 7: Assemble final HRISA.md with quality validation.

        Returns:
            Complete HRISA.md markdown
        """
        hrisa_parts = [
            self.sections.get("title", "# HRISA Documentation\n"),
            "\n",
            self.sections.get("architecture", "## Architecture\n\nTODO\n"),
            "\n",
            self.sections.get("components", "## Core Components\n\nTODO\n"),
            "\n",
            self.sections.get("tools", "## Tools\n\nTODO\n"),
            "\n",
            self.sections.get("development", "## Development Guide\n\nTODO\n"),
            "\n## Additional Resources\n\n"
            "- README.md: User-facing documentation\n"
            "- API.md: API reference\n"
            "- CONTRIBUTING.md: Contributor guide\n",
        ]

        hrisa = "\n".join(hrisa_parts)
        hrisa = re.sub(r"\n{3,}", "\n\n", hrisa)

        is_valid, errors = validate_content_quality(hrisa)

        if not is_valid:
            self.console.print("[red]✗ Content quality validation FAILED:[/red]")
            for error in errors:
                self.console.print(f"  • {error}")
            raise ValueError(f"Content quality validation failed: {len(errors)} issues found")

        project_name = self.facts.get("name", "UNKNOWN")
        if project_name.lower() not in hrisa.lower():
            self.console.print(
                f"[red]✗ VALIDATION FAILED: Project name '{project_name}' not in final HRISA.md[/red]"
            )
        else:
            self.console.print(
                f"[green]✓[/green] Content validation passed: clean, accurate documentation"
            )

        output_path = self.project_path / "HRISA.md"
        output_path.write_text(hrisa)

        return hrisa
