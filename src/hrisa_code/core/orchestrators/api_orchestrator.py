"""Orchestrator for API documentation generation.

This module guides an LLM through structured discovery steps to create
comprehensive API reference documentation.
"""

from pathlib import Path
from typing import Optional
from rich.console import Console

from hrisa_code.core.orchestrators.base_orchestrator import (
    BaseOrchestrator,
    WorkflowDefinition,
    WorkflowStep,
)
from hrisa_code.core.conversation import ConversationManager
from hrisa_code.core.model_router import ModelRouter


class ApiOrchestrator(BaseOrchestrator):
    """Orchestrates multi-step repository analysis for API documentation generation.

    This orchestrator guides the LLM through API-focused discovery steps:
    1. CLI Commands - Discover all CLI commands and their usage
    2. Tools Discovery - Find all available tools and their schemas
    3. Core APIs - Analyze public classes, methods, and functions
    4. Configuration - Document configuration options and formats
    5. Documentation Synthesis - Generate comprehensive API.md

    Target Audience: Developers integrating with or extending the project
    Focus: Complete API reference with examples
    """

    @property
    def workflow_definition(self) -> WorkflowDefinition:
        """Define the API.md generation workflow."""
        return WorkflowDefinition(
            name="API",
            description="Comprehensive API reference documentation",
            audience="Developers integrating with or extending the project",
            output_filename="API.md",
            steps=[
                WorkflowStep(
                    name="cli_commands",
                    display_name="CLI Commands Discovery",
                    model_preference="features",
                    prompt_template="""Discover all CLI commands in {project_path}.

Your task: Document every CLI command with complete usage information.

Steps:
1. Use find_files to locate cli.py with pattern="**/cli.py" searching from {project_path} (the project root)
   - The result will be a path like "src/hrisa_code/cli.py" (relative to project root)
   - To read the file, prepend {project_path} to get the absolute path
   - Example: If find_files returns "src/hrisa_code/cli.py", read "{project_path}/src/hrisa_code/cli.py"
2. Read the cli.py file to see all @app.command() definitions
3. IMPORTANT: If you get stuck, use list_directory on {project_path}/src/ to understand the structure
4. For each command, extract:
   - Command name
   - Description (from docstring)
   - Arguments (positional parameters)
   - Options/flags (--option, -o)
   - Default values
   - Help text
5. Look for command groups or subcommands
6. Check for global options (--version, --help)
7. Find examples of command usage in README or docs

IMPORTANT FALLBACK: If goal tracker warns you're stuck after multiple rounds:
- Stop trying complex searches or regex patterns
- Use find_files with simple patterns like "**/*.py"
- Read files directly instead of searching within them

Provide a summary of:
- Complete list of all commands
- For each command:
  - Full signature with all arguments and options
  - Description of what it does
  - Parameter descriptions with types and defaults
  - Return behavior or exit codes
  - Usage examples
- Command organization (groups, categories)

Format as reference documentation with clear syntax.""",
                ),
                WorkflowStep(
                    name="tools_discovery",
                    display_name="Tools & Functions Discovery",
                    model_preference="features",
                    prompt_template="""Discover all tools and functions available to the LLM.

Your task: Document the tool system for developers extending functionality.

Steps:
1. Use find_files with pattern="**/tools/*.py" from {project_path} to locate tool files
   - Results will be like "src/hrisa_code/tools/file_operations.py"
   - Prepend {project_path} to read: "{project_path}/src/hrisa_code/tools/file_operations.py"
2. Read each tool file (file_operations.py, git_operations.py) to see tool class definitions
3. For each tool class, extract from the get_definition() method:
   - Tool name (function name in schema)
   - Description
   - Parameters with types and descriptions
   - Return type and format
4. Look at execute() method to understand usage patterns
5. Identify tool categories by file (file_operations.py = file ops, git_operations.py = git ops)
6. Use find_files to check for test files in tests/ to find usage examples

IMPORTANT: Read the tool definition FILES directly - do NOT try to call tools with placeholder paths to test them.

Provide a summary of:
- Tool system architecture
- Complete list of all tools by category
- For each tool:
  - Function signature
  - Parameter details with types
  - Return value format
  - Error conditions
  - Usage examples
- How to add new tools

Format as API reference with JSON schemas.""",
                ),
                WorkflowStep(
                    name="core_apis",
                    display_name="Core API Discovery",
                    model_preference="components",
                    prompt_template="""Discover public APIs in core modules.

Your task: Document classes, methods, and functions developers can use.

Steps:
1. Identify public modules in src/hrisa_code/core/
2. For each module, find:
   - Public classes
   - Public functions
   - Key methods
3. Read docstrings and type hints
4. Identify usage patterns
5. Look for examples in tests
6. Check for factory functions, builders, etc.

Provide a summary organized by module:
- ConversationManager class
  - __init__ parameters
  - Public methods with signatures
  - Usage examples
- OllamaClient class
- Config system
- Agent class
- Task manager
- Orchestrators (BaseOrchestrator, subclasses)
- Other public APIs

For each API:
- Full signature with types
- Parameter descriptions
- Return types
- Exceptions raised
- Usage examples
- Common patterns

Focus on what developers would import and use.""",
                ),
                WorkflowStep(
                    name="configuration",
                    display_name="Configuration Discovery",
                    model_preference="workflows",
                    prompt_template="""Document configuration system and options.

Your task: Explain how to configure the application.

Steps:
1. Read core/config.py for all config models
2. Identify all configuration options:
   - Model settings (name, temperature, etc.)
   - Ollama settings (host, timeout, etc.)
   - Tool settings
   - Agent settings
3. Find default values
4. Look at config.example.yaml
5. Check for environment variables
6. Find config file locations (project vs user)
7. Look for config validation rules

Provide a summary of:
- Configuration file format (YAML)
- Configuration hierarchy (project → user → defaults)
- All configuration sections and options:
  - model: name, temperature, top_p, top_k, max_tokens
  - ollama: host, timeout
  - tools: enabled tools
  - agent: settings
  - etc.
- For each option:
  - Type and format
  - Default value
  - Description
  - Example values
- Environment variable overrides if supported
- Configuration examples for common scenarios

Format as reference with YAML examples.""",
                ),
            ],
            synthesis_prompt_template="""You have completed a thorough API analysis.

Here are your findings from each discovery step:
{discoveries}

---

Your task: Generate a COMPREHENSIVE API.md reference documentation.

This should be a complete API reference for developers.

Required sections (in this order):
1. **API Overview**
   - What this document covers
   - Intended audience (developers, integrators, extension authors)
   - Quick links to main sections

2. **CLI Reference**
   - All commands organized logically
   - For each command:
     - Syntax: `hrisa command [OPTIONS] [ARGS]`
     - Description
     - Arguments table (name, type, default, description)
     - Options table (flag, type, default, description)
     - Examples (2-3 practical examples)
     - Exit codes if applicable

3. **Tools Reference**
   - Tool system overview
   - Tools organized by category
   - For each tool:
     - Tool name
     - Description
     - JSON schema
     - Parameters table
     - Return format
     - Example tool call
     - Error conditions
   - How to add custom tools

4. **Core API Reference**
   - Organized by module
   - For each public class/function:
     - Import path
     - Class/function signature with types
     - Description
     - Parameters (name, type, default, description)
     - Returns (type, description)
     - Raises (exception types and conditions)
     - Usage example
     - Related APIs

5. **Configuration Reference**
   - Config file format and location
   - Configuration hierarchy
   - All config sections and options in tables
   - YAML schema
   - Example configurations for:
     - Basic setup
     - Advanced features
     - Development setup
     - Production setup
   - Environment variables

6. **Orchestrator API**
   - BaseOrchestrator class reference
   - How to create custom orchestrators
   - WorkflowDefinition and WorkflowStep
   - Customization hooks
   - Complete example orchestrator

7. **Extension Guide**
   - Adding new CLI commands
   - Adding new tools
   - Creating new orchestrators
   - Hooks and plugins (if available)

8. **Error Handling**
   - Common exceptions
   - Error codes
   - How to handle errors in integrations

9. **Examples**
   - Common integration patterns
   - Programmatic usage examples
   - Extension examples

10. **Migration Guide**
    - Breaking changes by version
    - Deprecation notices
    - Upgrade instructions

Format Guidelines:
- Use tables for parameters, options, config values
- Include type annotations in signatures
- Use code blocks with language tags (python, yaml, bash)
- Cross-reference related APIs
- Include practical, working examples
- Use consistent formatting for signatures
- Make it searchable and skimmable
- Focus on WHAT you can do and HOW to do it

Generate the COMPLETE API.md content now:""",
        )

    async def generate_api(self) -> str:
        """Execute the full orchestration to generate API.md.

        This is a convenience method that calls the base generate() method.

        Returns:
            The generated API.md content
        """
        return await self.generate()
