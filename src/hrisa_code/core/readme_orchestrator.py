"""Orchestrator for README.md generation.

This module guides an LLM through structured discovery steps to create
user-friendly repository documentation for human developers.
"""

from pathlib import Path
from typing import Optional
from rich.console import Console

from hrisa_code.core.base_orchestrator import (
    BaseOrchestrator,
    WorkflowDefinition,
    WorkflowStep,
)
from hrisa_code.core.conversation import ConversationManager
from hrisa_code.core.model_router import ModelRouter


class ReadmeOrchestrator(BaseOrchestrator):
    """Orchestrates multi-step repository analysis for README.md generation.

    This orchestrator guides the LLM through user-focused discovery steps:
    1. Project Discovery - Understand what the project does and why it exists
    2. Feature Highlights - Identify key features and their benefits
    3. Installation Guide - Determine setup requirements and steps
    4. Usage Examples - Create practical examples for users
    5. Documentation Synthesis - Generate comprehensive README.md

    Target Audience: Human developers and users (not AI assistants)
    Focus: Getting started, ease of use, practical examples
    """

    @property
    def workflow_definition(self) -> WorkflowDefinition:
        """Define the README.md generation workflow."""
        return WorkflowDefinition(
            name="README",
            description="User-friendly documentation for developers and users",
            audience="Human developers and users",
            output_filename="README.md",
            steps=[
                WorkflowStep(
                    name="project_discovery",
                    display_name="Project Discovery",
                    model_preference="architecture",
                    prompt_template="""Discover and understand the purpose of the project at {project_path}.

Your task: Understand what this project does and why it exists.

Steps:
1. Read {project_path}/README.md if it exists (to understand current description)
2. Read {project_path}/pyproject.toml to understand project metadata, dependencies, and description
3. List the main source files with list_directory on {project_path}/src/
4. Use find_files with pattern="**/cli.py" from {project_path} to locate cli.py
   - Result will be like "src/hrisa_code/cli.py" (relative to project root)
   - Read it with: {project_path}/src/hrisa_code/cli.py
5. Identify CLI commands with @app.command() decorators
6. IMPORTANT: Read files directly instead of using complex regex patterns

Provide a summary of:
- Project name and tagline
- What problem does it solve?
- Who is the target audience?
- Main value proposition
- Tech stack (Python version, key libraries)
- Project category (CLI tool, library, framework, etc.)

Focus on understanding the "why" and "what", not the "how".""",
                ),
                WorkflowStep(
                    name="feature_highlights",
                    display_name="Feature Highlights",
                    model_preference="features",
                    prompt_template="""Identify the key features and their benefits for users.

Your task: Find features that users care about (not implementation details).

Steps:
1. Use find_files with pattern="**/cli.py" from {project_path}, then read the file directly
   - Prepend {project_path} to the result to get absolute path
2. Read {project_path}/README.md to understand current feature descriptions
3. Use find_files with pattern="**/core/*.py" to locate core modules
   - Read key files like agent.py, task_manager.py directly (prepend {project_path})
4. Look for config.py with find_files, then read {project_path}/[result]
5. Check tool modules with pattern="**/tools/*.py"

IMPORTANT: Read files directly rather than searching with regex patterns. Use literal search for "@app.command" if needed, then read those files.

Provide a summary of:
- Top 5-8 features with user-facing benefits (not just "has feature X" but "lets you do Y")
- Unique capabilities that differentiate from similar tools
- Configuration and customization options
- Integration capabilities

Format as feature + benefit pairs.
Example: "Multi-turn Tool Calling → Execute complex tasks automatically without manual intervention"

Focus on what users can DO with the tool, not how it's implemented.""",
                ),
                WorkflowStep(
                    name="installation",
                    display_name="Installation Guide",
                    model_preference="workflows",
                    prompt_template="""Determine installation requirements and setup steps.

Your task: Figure out how users install and set up the project.

Steps:
1. Check for installation instructions in existing README or docs/
2. Read pyproject.toml for dependencies and installation metadata
3. Check for setup scripts, Makefile targets, or setup guides
4. Identify external dependencies (ollama, docker, etc.)
5. Look for configuration file examples or initialization commands
6. Check for Docker support (Dockerfile, docker-compose.yml)

Provide a summary of:
- Prerequisites (Python version, ollama, etc.)
- Installation methods (pip, uv, docker, from source)
- Post-installation setup (configuration, initialization)
- Quick start command to verify installation
- Docker/containerized options if available

Focus on the smoothest path for new users to get started.""",
                ),
                WorkflowStep(
                    name="usage_examples",
                    display_name="Usage Examples",
                    model_preference="workflows",
                    prompt_template="""Create practical usage examples for common scenarios.

Your task: Show users how to actually use the tool.

Steps:
1. Identify the most common CLI commands
2. Look for usage examples in docs/, README, or test files
3. Find configuration file examples (config.yaml, etc.)
4. Check for special modes or features worth demonstrating
5. Look for workflow examples (agent mode, interactive chat, background tasks)

Provide:
- Basic usage example (simplest way to start)
- 3-5 practical examples for common tasks
- Configuration example if applicable
- Advanced usage example showing powerful features
- Link to more comprehensive docs if they exist

Examples should be:
- Copy-pasteable commands
- Include expected output or behavior description
- Progress from simple to advanced
- Cover different use cases

Focus on real-world scenarios users will encounter.""",
                ),
            ],
            synthesis_prompt_template="""You have completed a thorough analysis for README generation.

Here are your findings from each discovery step:
{discoveries}

---

Your task: Generate a COMPREHENSIVE README.md file for human users.

This README should be welcoming, clear, and help users get started quickly.

Required sections (in this order):
1. **Project Title & Badges**
   - Project name with tagline
   - Relevant badges (if applicable): Python version, license, status

2. **Overview**
   - 2-3 sentence description of what it does
   - Key value proposition
   - Target audience

3. **Features**
   - Bullet list of 5-8 key features with brief benefits
   - Each feature should answer "what can I do with this?"

4. **Prerequisites**
   - Python version
   - Ollama or other external dependencies
   - Platform requirements

5. **Installation**
   - Recommended installation method (pip/uv/docker)
   - Alternative installation methods
   - Post-installation setup if needed

6. **Quick Start**
   - Simplest possible example to get started
   - Expected output

7. **Usage**
   - Basic commands with examples
   - Common use cases
   - Configuration options

8. **Examples**
   - 3-4 practical examples showing different features
   - Copy-pasteable commands with descriptions

9. **Configuration**
   - Config file location and format
   - Key configuration options
   - Example config snippets

10. **Documentation**
    - Links to more detailed docs if they exist
    - Architecture docs, development guides, etc.

11. **Development**
    - How to set up development environment
    - Running tests
    - Contributing guidelines (link to CONTRIBUTING.md if exists)

12. **Troubleshooting**
    - Common issues and solutions
    - Where to get help

13. **License**
    - License type

14. **Acknowledgments**
    - Credits, inspiration, related projects if applicable

Format Guidelines:
- Use clear, welcoming language (avoid jargon when possible)
- Include code blocks with syntax highlighting
- Use emojis sparingly for visual clarity (like ✨ 🚀 🛠️)
- Make it skimmable with good heading hierarchy
- Focus on user benefits, not implementation details
- Include practical, working examples

Generate the COMPLETE README.md content now:""",
        )

    async def generate_readme(self) -> str:
        """Execute the full orchestration to generate README.md.

        This is a convenience method that calls the base generate() method.

        Returns:
            The generated README.md content
        """
        return await self.generate()
