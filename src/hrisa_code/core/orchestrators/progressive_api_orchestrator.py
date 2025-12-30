"""Progressive context-building orchestrator for API documentation generation.

This orchestrator uses the proven progressive approach:
- Extract ground-truth facts first (using static analysis, not LLM)
- Build each section incrementally with validation
- Assemble (don't synthesize) final document

Target: Developers integrating with or extending the project
Focus: Complete API reference with CLI commands, tools, core APIs, configuration
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
    extract_cli_commands_from_ast,
    extract_tool_definitions,
    validate_content_quality,
)


class ProgressiveApiOrchestrator(ProgressiveBaseOrchestrator):
    """Progressive API.md generation with validation at each step.

    Strategy:
    1. Extract Facts: Read pyproject.toml, validate extraction
    2. Build Title Section: Use extracted facts, validate project name
    3. Build CLI Commands Section: From actual @app.command() decorators
    4. Build Tools Section: From tools/*.py class definitions
    5. Build Core API Section: From core/*.py public classes
    6. Build Configuration Section: From config.py models
    7. Assemble: Combine sections (no synthesis thinking)
    """

    @property
    def workflow_definition(self) -> ProgressiveWorkflow:
        """Define the API documentation generation workflow.

        Returns:
            Progressive workflow with all phases
        """
        return ProgressiveWorkflow(
            name="API",
            description="Generate comprehensive API.md documentation progressively",
            output_filename="API.md",
            phases=[
                PhaseDefinition(
                    name="title",
                    display_name="Title Section",
                    description="Building title with validated project name...",
                    uses_llm=False,
                ),
                PhaseDefinition(
                    name="cli_commands",
                    display_name="CLI Commands Section",
                    description="Extracting CLI commands via AST parsing (no LLM)...",
                    uses_llm=False,
                ),
                PhaseDefinition(
                    name="tools",
                    display_name="Tools Section",
                    description="Extracting tools via static analysis (no LLM)...",
                    uses_llm=False,
                ),
                PhaseDefinition(
                    name="core_api",
                    display_name="Core API Section",
                    description="Building Core API reference...",
                    uses_llm=True,  # Uses LLM for integration guidance
                ),
                PhaseDefinition(
                    name="configuration",
                    display_name="Configuration Section",
                    description="Building configuration reference...",
                    uses_llm=False,
                ),
            ],
            audience="developers and integrators",
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

        section = f"""# {name} API Reference

{description}

## API Overview

This document provides comprehensive API documentation for developers, integrators, and extension authors.

### Quick Links
- [CLI Reference](#cli-reference)
- [Tools Reference](#tools-reference)
- [Core API Reference](#core-api-reference)
- [Configuration Reference](#configuration-reference)
- [Extension Guide](#extension-guide)
"""

        return section

    async def build_cli_commands_section(self) -> str:
        """Phase 3: Build CLI commands section using static analysis + LLM prose.

        Returns:
            CLI commands section markdown
        """
        cli_file = self.project_path / "src" / "hrisa_code" / "cli.py"
        if not cli_file.exists():
            cli_file = self.project_path / "cli.py"

        commands = extract_cli_commands_from_ast(cli_file)

        section = "## CLI Reference\n\n"

        if commands:
            for cmd in commands:
                section += f"### Command: `{cmd['name']}`\n\n"
                section += f"**Description**: {cmd['help'] or 'No description available'}\n\n"
                section += f"**Usage**:\n```bash\n{self.facts.get('name', 'hrisa')} {cmd['name']} [OPTIONS]\n```\n\n"
        else:
            section += "No CLI commands found.\n"

        return section

    async def build_tools_section(self) -> str:
        """Phase 4: Build tools section using static analysis + LLM prose.

        Returns:
            Tools section markdown
        """
        tools_dir = self.project_path / "src" / "hrisa_code" / "tools"
        if not tools_dir.exists():
            tools_dir = self.project_path / "tools"

        tools = extract_tool_definitions(tools_dir)

        section = "## Tools Reference\n\n"

        if tools:
            section += "### Available Tools\n\n"
            section += "The system provides the following tools for file operations, git integration, and command execution:\n\n"

            for tool in tools:
                section += f"#### `{tool['name']}`\n\n"
                section += f"**Source**: `{tool['file']}`\n\n"
                if tool["description"]:
                    section += f"**Description**: {tool['description']}\n\n"
        else:
            section += "No tools found.\n"

        return section

    async def build_core_api_section(self) -> str:
        """Phase 5: Build core API section with template + directive LLM.

        Returns:
            Core API section markdown
        """
        section = "## Core API Reference\n\n"
        section += "The core API consists of several key modules:\n\n"

        core_modules = [
            ("config", "Configuration management with Pydantic models"),
            ("conversation", "Conversation orchestration and tool execution"),
            ("ollama_client", "Async Ollama API client"),
            ("agent", "Autonomous task execution"),
            ("task_manager", "Background process management"),
        ]

        for module_name, description in core_modules:
            section += f"### Module: `hrisa_code.core.{module_name}`\n\n"
            section += f"{description}\n\n"
            section += f"See source code at `src/hrisa_code/core/{module_name}.py` for complete API details.\n\n"

        prompt = f"""Write 2-3 sentences about how developers can import and use the core modules.

Project: {self.facts.get('name')}
Core modules: config, conversation, ollama_client, agent, task_manager

OUTPUT ONLY THE PROSE (no headers, no code blocks).
Example: "Import core classes directly from hrisa_code.core..."

Do NOT use conversational phrases."""

        guidance = await self.conversation.process_message(prompt)
        section += f"\n### Usage\n\n{guidance.strip()}\n"

        return section

    async def build_configuration_section(self) -> str:
        """Phase 6: Build configuration section with template + example.

        Returns:
            Configuration section markdown
        """
        section = "## Configuration Reference\n\n"
        section += "### Configuration File Locations\n\n"
        section += "Configuration is loaded from:\n"
        section += "1. Project-specific: `.hrisa/config.yaml`\n"
        section += "2. User-level: `~/.config/hrisa-code/config.yaml`\n"
        section += "3. Default settings (built-in)\n\n"

        section += "### Configuration Sections\n\n"
        section += "#### Model Configuration\n\n"
        section += "- `name`: Model name (e.g., qwen2.5:72b)\n"
        section += "- `temperature`: Temperature for generation (0.0-1.0)\n"
        section += "- `top_p`: Top-p sampling parameter\n"
        section += "- `top_k`: Top-k sampling parameter\n\n"

        section += "#### Ollama Configuration\n\n"
        section += "- `host`: Ollama server URL (default: http://localhost:11434)\n"
        section += "- `timeout`: Request timeout in seconds\n\n"

        section += "#### Tools Configuration\n\n"
        section += "- `enable_file_operations`: Enable file read/write tools\n"
        section += "- `enable_command_execution`: Enable shell command execution\n"
        section += "- `enable_search`: Enable search operations\n\n"

        section += "### Example Configuration\n\n"
        section += "```yaml\n"
        section += "model:\n"
        section += "  name: qwen2.5:72b\n"
        section += "  temperature: 0.7\n"
        section += "  top_p: 0.9\n"
        section += "  top_k: 40\n\n"
        section += "ollama:\n"
        section += "  host: http://localhost:11434\n"
        section += "  timeout: 300\n\n"
        section += "tools:\n"
        section += "  enable_file_operations: true\n"
        section += "  enable_command_execution: true\n"
        section += "```\n"

        return section

    async def assemble_document(self) -> str:
        """Phase 7: Assemble final API.md with quality validation.

        Returns:
            Complete API.md markdown
        """
        api_parts = [
            self.sections.get("title", "# API Reference\n"),
            "\n",
            self.sections.get("cli_commands", "## CLI Reference\n\nTODO\n"),
            "\n",
            self.sections.get("tools", "## Tools Reference\n\nTODO\n"),
            "\n",
            self.sections.get("core_api", "## Core API Reference\n\nTODO\n"),
            "\n",
            self.sections.get("configuration", "## Configuration Reference\n\nTODO\n"),
            "\n## Extension Guide\n\nSee CONTRIBUTING.md for information on extending the API.\n",
            "\n## Error Handling\n\nCommon exceptions and error codes will be documented here.\n",
        ]

        api_doc = "\n".join(api_parts)
        api_doc = re.sub(r"\n{3,}", "\n\n", api_doc)

        is_valid, errors = validate_content_quality(api_doc)

        if not is_valid:
            self.console.print("[red]✗ Content quality validation FAILED:[/red]")
            for error in errors:
                self.console.print(f"  • {error}")
            raise ValueError(f"Content quality validation failed: {len(errors)} issues found")

        project_name = self.facts.get("name", "UNKNOWN")
        if project_name.lower() not in api_doc.lower():
            self.console.print(
                f"[red]✗ VALIDATION FAILED: Project name '{project_name}' not in final API.md[/red]"
            )
        else:
            self.console.print(
                f"[green]✓[/green] Content validation passed: clean, accurate documentation"
            )

        output_path = self.project_path / "API.md"
        output_path.write_text(api_doc)

        return api_doc
