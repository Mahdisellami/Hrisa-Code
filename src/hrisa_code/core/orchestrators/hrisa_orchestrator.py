"""Orchestrator for comprehensive HRISA.md generation.

This module guides an LLM through structured discovery steps to create
comprehensive repository documentation for AI assistants.
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


class HrisaOrchestrator(BaseOrchestrator):
    """Orchestrates multi-step repository analysis for HRISA.md generation.

    This orchestrator guides the LLM through specific discovery steps:
    1. Architecture Discovery - Understand project structure
    2. Component Analysis - Analyze key modules and files
    3. Feature Identification - Find tools, commands, patterns
    4. Workflow Understanding - Trace execution flows
    5. Documentation Synthesis - Generate comprehensive HRISA.md
    """

    @property
    def workflow_definition(self) -> WorkflowDefinition:
        """Define the HRISA.md generation workflow."""
        return WorkflowDefinition(
            name="HRISA",
            description="Comprehensive repository documentation for AI assistants",
            audience="AI assistants (like Claude Code)",
            output_filename="HRISA.md",
            steps=[
                WorkflowStep(
                    name="architecture",
                    display_name="Architecture Discovery",
                    model_preference="architecture",
                    prompt_template="""Analyze the project structure of Hrisa Code at {project_path}.

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
                ),
                WorkflowStep(
                    name="components",
                    display_name="Component Analysis",
                    model_preference="components",
                    prompt_template="""Analyze the core components of Hrisa Code.

Based on the architecture discovered, now dive deeper into key components:

Your task: Understand what each core component does.

Steps:
1. Read the main CLI entry point (src/hrisa_code/cli.py)
2. Read core modules: config.py, interactive.py, ollama_client.py, conversation.py
3. Read advanced modules: agent.py, task_manager.py, orchestrators
4. Note the key classes, functions, and their responsibilities

Provide a summary of:
- What each module does
- Key classes and their responsibilities
- How modules interact with each other
- Any design patterns used

Use available tools to read and analyze files.""",
                ),
                WorkflowStep(
                    name="features",
                    display_name="Feature Identification",
                    model_preference="features",
                    prompt_template="""Identify the features and capabilities of Hrisa Code.

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
                ),
                WorkflowStep(
                    name="workflows",
                    display_name="Workflow Understanding",
                    model_preference="workflows",
                    prompt_template="""Understand the execution workflows in Hrisa Code.

Your task: Trace how the application works end-to-end.

Steps:
1. Trace the flow from CLI command to LLM interaction
2. Understand the conversation loop (messages → LLM → tools → response)
3. Understand multi-turn tool calling (Claude Code style)
4. Understand agent mode workflow (if different from normal mode)
5. Understand background task execution
6. Understand orchestration workflows

Provide a summary of:
- Main execution flow (CLI → Interactive → Conversation → LLM)
- How tool calling works
- How multi-turn tool calling works
- How agent mode works
- How background tasks work
- How orchestration works (HRISA, README generation)

Use available tools to read relevant code sections.""",
                ),
            ],
            synthesis_prompt_template="""You have completed a thorough analysis of the Hrisa Code repository.

Here are your findings from each discovery step:
{discoveries}

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
7. Features - All major features (agent mode, multi-turn tools, background tasks, orchestration, etc.)
8. Development Practices - Code style, testing, linting
9. Common Tasks - How to add features, run tests, create new orchestrators, etc.
10. Important Files - Critical files and their purposes
11. Workflows - How the application works end-to-end
12. Code Patterns - Common patterns and examples (including orchestrator patterns)
13. Notes for AI Assistants - Important guidelines
14. Version Information - Current version and status

Format: Use Markdown with clear headings, code examples, and detailed explanations.

Be comprehensive and accurate. Include ALL features discovered, not just the basics.

IMPORTANT: Describe the new orchestration framework (BaseOrchestrator, WorkflowDefinition, WorkflowStep) and how to create new orchestrators like READMEOrchestrator.

Generate the COMPLETE HRISA.md content now:""",
        )

    async def generate_comprehensive_hrisa(self) -> str:
        """Execute the full orchestration to generate comprehensive HRISA.md.

        This is a convenience method that calls the base generate() method.

        Returns:
            The generated HRISA.md content
        """
        return await self.generate()
