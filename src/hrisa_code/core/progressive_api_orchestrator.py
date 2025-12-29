"""Progressive context-building orchestrator for API documentation generation.

This orchestrator uses the proven progressive approach:
- Extract ground-truth facts first
- Build each section incrementally with validation
- Assemble (don't synthesize) final document

Target: Developers integrating with or extending the project
Focus: Complete API reference with CLI commands, tools, core APIs, configuration
"""

import re
from pathlib import Path
from typing import Optional, Dict, Any
from rich.console import Console
from rich.panel import Panel

from hrisa_code.core.conversation import ConversationManager


class ProgressiveApiOrchestrator:
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

    def __init__(
        self,
        conversation: ConversationManager,
        project_path: Path,
        console: Optional[Console] = None,
    ):
        """Initialize progressive API orchestrator.

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
4. project.scripts → Entry point commands (e.g., "hrisa = hrisa_code.cli:app")

CRITICAL RULES:
- Report EXACT strings from the file (copy-paste, no paraphrasing)
- Do NOT add your own descriptions
- Do NOT invent missing information

After reading the file, respond with ONLY this format (no markdown, no explanations):

PROJECT_NAME: [exact name from file]
PROJECT_DESC: [exact description from file]
VERSION: [exact version]
ENTRY_POINT: [exact entry point like "hrisa = hrisa_code.cli:app"]

Start by reading the file."""

        response = await self.conversation.process_message(prompt)

        # Parse the structured response
        name_match = re.search(r'PROJECT_NAME:\s*(.+?)(?:\n|$)', response)
        desc_match = re.search(r'PROJECT_DESC:\s*(.+?)(?:\n|$)', response)
        version_match = re.search(r'VERSION:\s*(.+?)(?:\n|$)', response)
        entry_match = re.search(r'ENTRY_POINT:\s*(.+?)(?:\n|$)', response)

        self.facts = {
            "name": name_match.group(1).strip() if name_match else "UNKNOWN",
            "description": desc_match.group(1).strip() if desc_match else "UNKNOWN",
            "version": version_match.group(1).strip() if version_match else "0.0.0",
            "entry_point": entry_match.group(1).strip() if entry_match else "UNKNOWN",
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

        self.sections["title"] = section

        # Validation
        if name.lower() in section.lower():
            self.console.print(f"[green]✓[/green] Title section built: {name}")
        else:
            self.console.print(f"[red]✗[/red] Validation failed for title")

        return section

    async def build_cli_commands_section(self) -> str:
        """Phase 3: Build CLI commands section from actual code.

        Returns:
            CLI commands section markdown
        """
        self.console.print(Panel(
            "[bold cyan]Phase 3: CLI Commands Section[/bold cyan]\n"
            "Discovering actual CLI commands from @app.command() decorators...",
            border_style="cyan"
        ))

        prompt = f"""DISCOVER CLI COMMANDS (CODE-BASED ONLY)

Task: Document every CLI command found in the codebase.

Steps:
1. Use find_files to locate cli.py: pattern="**/cli.py", directory="{self.project_path}"
2. Read the cli.py file
3. For each @app.command() decorator:
   - Extract function name (this is the command name)
   - Extract docstring (command description)
   - Extract parameters (arguments and options)
   - Extract type hints and defaults

CRITICAL RULES:
- Only document ACTUAL commands with @app.command() decorator
- Do NOT invent commands
- Extract EXACT parameter names, types, defaults from function signatures
- Output PURE MARKDOWN (no code fences, no explanations)

Output format (EXACT):
## CLI Reference

### Command: `command-name`

**Description**: [Exact docstring text]

**Usage**:
```bash
command-name [OPTIONS] [ARGUMENTS]
```

**Arguments**:
- `arg_name` (type): Description from docstring

**Options**:
- `--option-name, -o` (type, default: value): Description

**Examples**:
```bash
# Example from docstring or inferred usage
command-name --option value
```

[Repeat for each command found]

Start by finding and reading cli.py. Output ONLY markdown."""

        section = await self.conversation.process_message(prompt)

        # Clean up markdown fences
        section = section.strip()
        if section.startswith("```markdown"):
            section = section[len("```markdown"):].strip()
        if section.startswith("```"):
            section = section[3:].strip()
        if section.endswith("```"):
            section = section[:-3].strip()

        self.sections["cli_commands"] = section

        self.console.print("[green]✓[/green] CLI commands section built from actual code")
        return section

    async def build_tools_section(self) -> str:
        """Phase 4: Build tools section from tools/*.py files.

        Returns:
            Tools section markdown
        """
        self.console.print(Panel(
            "[bold cyan]Phase 4: Tools Section[/bold cyan]\n"
            "Discovering tools from tools/*.py files...",
            border_style="cyan"
        ))

        prompt = f"""DISCOVER TOOLS (CODE-BASED ONLY)

Task: Document all tools available to the LLM.

Steps:
1. Use find_files with pattern="**/tools/*.py" from {self.project_path}
2. Read each tool file (e.g., file_operations.py, git_operations.py)
3. For each class with get_definition() method:
   - Extract tool name (from schema)
   - Extract description
   - Extract parameters from schema
   - Extract return format

CRITICAL RULES:
- Only document tools with get_definition() method
- Extract EXACT schema from code
- Do NOT invent tools or parameters
- Output PURE MARKDOWN

Output format (EXACT):
## Tools Reference

### Tool System Overview
[Brief explanation of how tools work]

### File Operations Tools

#### Tool: `tool_name`

**Description**: [Exact description from schema]

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| param_name | type | Yes/No | Description |

**Returns**: Description of return format

**Example**:
```json
{{
  "tool": "tool_name",
  "parameters": {{
    "param": "value"
  }}
}}
```

[Repeat for each tool, grouped by category]

Start by finding tool files. Output ONLY markdown."""

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

    async def build_core_api_section(self) -> str:
        """Phase 5: Build core API section from core/*.py files.

        Returns:
            Core API section markdown
        """
        self.console.print(Panel(
            "[bold cyan]Phase 5: Core API Section[/bold cyan]\n"
            "Discovering core APIs from core/*.py files...",
            border_style="cyan"
        ))

        prompt = f"""DISCOVER CORE APIs (CODE-BASED ONLY)

Task: Document public classes and methods in core modules.

Steps:
1. Use list_directory on {self.project_path}/src/[package]/core/
2. Read key files like config.py, conversation.py, agent.py
3. For each public class:
   - Extract class name
   - Extract __init__ parameters
   - Extract public methods (not starting with _)
   - Extract docstrings and type hints

CRITICAL RULES:
- Only document public APIs (no _ prefixed)
- Extract EXACT signatures from code
- Include type hints if present
- Output PURE MARKDOWN

Output format (EXACT):
## Core API Reference

### Module: `module_name`

#### Class: `ClassName`

**Description**: [From class docstring]

**Constructor**:
```python
__init__(param1: Type, param2: Type = default)
```

**Parameters**:
- `param1` (Type): Description
- `param2` (Type, optional): Description. Default: value

**Methods**:

##### `method_name(param: Type) -> ReturnType`

Description from docstring.

**Parameters**:
- `param` (Type): Description

**Returns**: Description

[Repeat for each class/method]

Start by listing core directory. Output ONLY markdown."""

        section = await self.conversation.process_message(prompt)

        # Clean up markdown fences
        section = section.strip()
        if section.startswith("```markdown"):
            section = section[len("```markdown"):].strip()
        if section.startswith("```"):
            section = section[3:].strip()
        if section.endswith("```"):
            section = section[:-3].strip()

        self.sections["core_api"] = section

        self.console.print("[green]✓[/green] Core API section built from actual code")
        return section

    async def build_configuration_section(self) -> str:
        """Phase 6: Build configuration section from config.py.

        Returns:
            Configuration section markdown
        """
        self.console.print(Panel(
            "[bold cyan]Phase 6: Configuration Section[/bold cyan]\n"
            "Discovering configuration from config.py...",
            border_style="cyan"
        ))

        prompt = f"""DISCOVER CONFIGURATION (CODE-BASED ONLY)

Task: Document all configuration options.

Steps:
1. Use find_files with pattern="**/config.py" from {self.project_path}
2. Read config.py to find Pydantic models
3. For each config model:
   - Extract field names
   - Extract types
   - Extract defaults
   - Extract descriptions from Field()

CRITICAL RULES:
- Only document actual config fields from code
- Extract EXACT defaults from code
- Include validation rules if present
- Output PURE MARKDOWN

Output format (EXACT):
## Configuration Reference

### Configuration File Format

YAML configuration file format and location.

### Configuration Sections

#### Model Configuration

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| field_name | type | value | Description |

#### Ollama Configuration

[Same table format]

### Example Configuration

```yaml
model:
  name: qwen2.5:72b
  temperature: 0.7

ollama:
  host: http://localhost:11434
```

Start by finding config.py. Output ONLY markdown."""

        section = await self.conversation.process_message(prompt)

        # Clean up markdown fences
        section = section.strip()
        if section.startswith("```markdown"):
            section = section[len("```markdown"):].strip()
        if section.startswith("```"):
            section = section[3:].strip()
        if section.endswith("```"):
            section = section[:-3].strip()

        self.sections["configuration"] = section

        self.console.print("[green]✓[/green] Configuration section built from actual code")
        return section

    async def assemble_api_doc(self) -> str:
        """Phase 7: Assemble final API.md (no synthesis thinking).

        Returns:
            Complete API.md markdown
        """
        self.console.print(Panel(
            "[bold cyan]Phase 7: Assembly[/bold cyan]\n"
            "Combining validated sections...",
            border_style="cyan"
        ))

        # Simple string concatenation - no LLM needed!
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

        # Join and clean up extra newlines
        api_doc = "\n".join(api_parts)
        api_doc = re.sub(r'\n{3,}', '\n\n', api_doc)

        # Final validation
        project_name = self.facts.get("name", "UNKNOWN")
        if project_name.lower() not in api_doc.lower():
            self.console.print(f"[red]✗ VALIDATION FAILED: Project name '{project_name}' not in final API.md[/red]")
        else:
            self.console.print(f"[green]✓[/green] Final validation passed: {project_name}")

        return api_doc

    async def generate(self) -> str:
        """Execute progressive API.md generation workflow.

        Returns:
            Generated API.md content
        """
        self.console.print(Panel(
            "[bold]Progressive API Documentation Generation[/bold]\n"
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
            await self.build_cli_commands_section()
            await self.build_tools_section()
            await self.build_core_api_section()
            await self.build_configuration_section()

            # Phase 7: Assemble (no synthesis)
            api_doc = await self.assemble_api_doc()

            # Write to file
            output_path = self.project_path / "API.md"
            output_path.write_text(api_doc)

            self.console.print(Panel(
                f"[green]✓ API.md generated successfully![/green]\n\n"
                f"Output: {output_path}\n"
                f"Sections: {len(self.sections)}\n"
                f"Validated: ✓",
                title="► Complete",
                border_style="bold green"
            ))

            return api_doc

        except Exception as e:
            self.console.print(f"[red]✗ Error during progressive generation: {e}[/red]")
            raise
