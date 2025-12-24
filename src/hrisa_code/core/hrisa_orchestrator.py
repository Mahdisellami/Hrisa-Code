"""Orchestrator for comprehensive HRISA.md generation.

This module guides an LLM through structured discovery steps to create
comprehensive repository documentation.
"""

import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from hrisa_code.core.conversation import ConversationManager


class HrisaOrchestrator:
    """Orchestrates multi-step repository analysis for HRISA.md generation.

    This orchestrator guides the LLM through specific discovery steps:
    1. Architecture Discovery - Understand project structure
    2. Component Analysis - Analyze key modules and files
    3. Feature Identification - Find tools, commands, patterns
    4. Workflow Understanding - Trace execution flows
    5. Documentation Synthesis - Generate comprehensive HRISA.md
    """

    def __init__(
        self,
        conversation: ConversationManager,
        project_path: Path,
        console: Optional[Console] = None,
    ):
        """Initialize the orchestrator.

        Args:
            conversation: ConversationManager for LLM interactions
            project_path: Path to the project root
            console: Rich console for output (creates new if None)
        """
        self.conversation = conversation
        self.project_path = project_path
        self.console = console or Console()

        # Storage for discoveries
        self.discoveries: Dict[str, Any] = {
            "architecture": None,
            "components": None,
            "features": None,
            "workflows": None,
        }

    def _get_step_prompt(self, step: str) -> str:
        """Get the prompt for a specific discovery step.

        Args:
            step: The step name (architecture, components, features, workflows)

        Returns:
            Prompt text for the step
        """
        prompts = {
            "architecture": f"""Analyze the project structure of Hrisa Code at {self.project_path}.

Your task: Discover and document the project architecture.

Steps:
1. List all Python source files in src/hrisa_code/ (use appropriate search tools)
2. Identify the main modules and their purposes
3. Note the directory structure and organization
4. Identify key configuration files (pyproject.toml, Makefile, etc.)

Provide a summary of:
- Main modules and their roles
- Directory structure
- Key configuration files
- Project dependencies from pyproject.toml

Use available tools to explore the codebase. Be thorough.""",

            "components": f"""Analyze the core components of Hrisa Code.

Based on the architecture discovered, now dive deeper into key components:

Your task: Understand what each core component does.

Steps:
1. Read the main CLI entry point (src/hrisa_code/cli.py)
2. Read core modules: config.py, interactive.py, ollama_client.py, conversation.py
3. Read advanced modules: agent.py, task_manager.py (if they exist)
4. Note the key classes, functions, and their responsibilities

Provide a summary of:
- What each module does
- Key classes and their responsibilities
- How modules interact with each other
- Any design patterns used

Use available tools to read and analyze files.""",

            "features": f"""Identify the features and capabilities of Hrisa Code.

Your task: Document all features and capabilities.

Steps:
1. Search for all Typer @app.command() definitions
2. Identify tool definitions (search for tool schemas)
3. Find configuration options
4. Look for special modes (agent mode, background execution, etc.)
5. Identify testing infrastructure

Provide a summary of:
- All CLI commands available
- All tools/functions the LLM can use
- Configuration options
- Special features (agent mode, streaming, background tasks, etc.)
- Testing setup

Use search and read tools to explore the codebase.""",

            "workflows": f"""Understand the execution workflows in Hrisa Code.

Your task: Trace how the application works end-to-end.

Steps:
1. Trace the flow from CLI command to LLM interaction
2. Understand the conversation loop (messages → LLM → tools → response)
3. Understand multi-turn tool calling (Claude Code style)
4. Understand agent mode workflow (if different from normal mode)
5. Understand background task execution

Provide a summary of:
- Main execution flow (CLI → Interactive → Conversation → LLM)
- How tool calling works
- How multi-turn tool calling works
- How agent mode works
- How background tasks work

Use available tools to read relevant code sections.""",
        }

        return prompts.get(step, "")

    async def _execute_step(self, step_name: str, step_num: int, total_steps: int) -> str:
        """Execute a single discovery step.

        Args:
            step_name: Name of the step (architecture, components, features, workflows)
            step_num: Step number (1-indexed)
            total_steps: Total number of steps

        Returns:
            The LLM's response for this step
        """
        # Show progress
        self.console.print()
        self.console.print(
            Panel(
                f"[bold cyan]Step {step_num}/{total_steps}: {step_name.title()} Discovery[/bold cyan]\n\n"
                f"[dim]Exploring the codebase to understand {step_name}...[/dim]",
                title="► Orchestrator",
                border_style="cyan",
            )
        )
        self.console.print()

        # Get the prompt for this step
        prompt = self._get_step_prompt(step_name)

        # Execute the step (let the conversation handle multi-turn tool calling)
        response = await self.conversation.process_message(prompt)

        # Display the findings
        if response:
            self.console.print(f"[bold blue]Findings:[/bold blue]")
            self.console.print(response)
            self.console.print()

        # Store the discovery
        self.discoveries[step_name] = response

        return response

    async def _synthesize_documentation(self) -> str:
        """Synthesize all discoveries into comprehensive HRISA.md.

        Returns:
            The generated HRISA.md content
        """
        self.console.print()
        self.console.print(
            Panel(
                "[bold cyan]Step 5/5: Documentation Synthesis[/bold cyan]\n\n"
                "[dim]Generating comprehensive HRISA.md from all discoveries...[/dim]",
                title="► Orchestrator",
                border_style="cyan",
            )
        )
        self.console.print()

        # Create synthesis prompt with all discoveries
        synthesis_prompt = f"""You have completed a thorough analysis of the Hrisa Code repository.

Here are your findings from each discovery step:

## ARCHITECTURE DISCOVERY:
{self.discoveries['architecture']}

## COMPONENT ANALYSIS:
{self.discoveries['components']}

## FEATURE IDENTIFICATION:
{self.discoveries['features']}

## WORKFLOW UNDERSTANDING:
{self.discoveries['workflows']}

---

Your task: Generate a COMPREHENSIVE HRISA.md file.

This file should serve as the definitive guide for AI assistants working on this project.

Required sections:
1. Project Overview - What is Hrisa Code and what does it do?
2. Tech Stack - All technologies, libraries, and tools used
3. Project Structure - Directory layout and file organization
4. Key Components - Detailed explanation of each module
5. CLI Commands - All available commands with descriptions
6. Tools & Capabilities - All tools the LLM can use
7. Features - All major features (agent mode, multi-turn tools, background tasks, etc.)
8. Development Practices - Code style, testing, linting
9. Common Tasks - How to add features, run tests, etc.
10. Important Files - Critical files and their purposes
11. Workflows - How the application works end-to-end
12. Code Patterns - Common patterns and examples
13. Notes for AI Assistants - Important guidelines
14. Version Information - Current version and status

Format: Use Markdown with clear headings, code examples, and detailed explanations.

Be comprehensive and accurate. Include ALL features discovered, not just the basics.

Generate the COMPLETE HRISA.md content now:"""

        # Get the synthesized documentation
        hrisa_content = await self.conversation.process_message(synthesis_prompt)

        return hrisa_content

    async def generate_comprehensive_hrisa(self) -> str:
        """Execute the full orchestration to generate comprehensive HRISA.md.

        Returns:
            The generated HRISA.md content
        """
        # Display orchestration start
        self.console.print()
        self.console.print(
            Panel(
                "[bold green]COMPREHENSIVE HRISA.MD GENERATION[/bold green]\n\n"
                f"Project: {self.project_path}\n\n"
                "[dim]The orchestrator will guide the LLM through 5 discovery steps:\n"
                "1. Architecture Discovery\n"
                "2. Component Analysis\n"
                "3. Feature Identification\n"
                "4. Workflow Understanding\n"
                "5. Documentation Synthesis[/dim]",
                title="► Starting Orchestration",
                border_style="green",
            )
        )
        self.console.print()

        # Execute discovery steps
        steps = ["architecture", "components", "features", "workflows"]
        total_steps = len(steps) + 1  # +1 for synthesis

        for i, step in enumerate(steps, start=1):
            await self._execute_step(step, i, total_steps)

        # Synthesize documentation
        hrisa_content = await self._synthesize_documentation()

        # Display completion
        self.console.print()
        self.console.print(
            Panel(
                "[bold green]✓ Comprehensive HRISA.md generated successfully![/bold green]\n\n"
                f"All {total_steps} steps completed.",
                title="► Complete",
                border_style="green",
            )
        )
        self.console.print()

        return hrisa_content
