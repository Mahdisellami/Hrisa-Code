"""Orchestrator for CONTRIBUTING.md generation.

This module guides an LLM through structured discovery steps to create
comprehensive contributor guidelines for open-source projects.
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


class ContributingOrchestrator(BaseOrchestrator):
    """Orchestrates multi-step repository analysis for CONTRIBUTING.md generation.

    This orchestrator guides the LLM through contributor-focused discovery steps:
    1. Project Setup - Development environment setup requirements
    2. Code Standards - Coding style, testing, linting guidelines
    3. Contribution Workflow - Git workflow, PR process, review guidelines
    4. Architecture Guide - Where to add features, common patterns
    5. Documentation Synthesis - Generate comprehensive CONTRIBUTING.md

    Target Audience: Open-source contributors and maintainers
    Focus: Making it easy for new contributors to get started
    """

    @property
    def workflow_definition(self) -> WorkflowDefinition:
        """Define the CONTRIBUTING.md generation workflow."""
        return WorkflowDefinition(
            name="CONTRIBUTING",
            description="Contributor guidelines for open-source projects",
            audience="Open-source contributors and maintainers",
            output_filename="CONTRIBUTING.md",
            steps=[
                WorkflowStep(
                    name="project_setup",
                    display_name="Project Setup Discovery",
                    model_preference="workflows",
                    prompt_template="""Discover how to set up the development environment for {project_path}.

Your task: Understand what contributors need to get started.

Steps:
1. Read {project_path}/README.md for existing setup instructions
2. Read {project_path}/pyproject.toml for dependencies and dev dependencies
3. Use list_directory on {project_path} to see Makefile, then read {project_path}/Makefile
4. Use list_directory on {project_path}/scripts/ to see setup scripts
5. Check for {project_path}/Dockerfile and {project_path}/docker-compose.yml
6. Identify Python version requirements from pyproject.toml
7. Look for {project_path}/.pre-commit-config.yaml or git hooks
8. Check for environment variables or config files

IMPORTANT: Always prepend {project_path} when reading files. Use list_directory to explore, then read files directly with full paths.

Provide a summary of:
- Python version requirements
- Dependency installation methods (pip, uv, poetry)
- Virtual environment setup
- Docker setup if available
- Pre-commit hooks if present
- Environment variables or config needed
- Any platform-specific requirements

Focus on what a new contributor needs to do FIRST.""",
                ),
                WorkflowStep(
                    name="code_standards",
                    display_name="Code Standards Discovery",
                    model_preference="architecture",
                    prompt_template="""Discover the code standards and quality requirements.

Your task: Understand coding style, testing, and quality expectations.

Steps:
1. Read {project_path}/pyproject.toml and look for [tool.ruff], [tool.black], [tool.mypy], [tool.pytest] sections
2. Check for {project_path}/ruff.toml, {project_path}/mypy.ini, {project_path}/pytest.ini
3. Read {project_path}/Makefile to find quality check commands
4. Use list_directory on {project_path}/tests/ to understand test structure
5. Check {project_path}/.github/workflows/ for CI/CD configs
6. Read example source files with full paths like {project_path}/src/hrisa_code/core/agent.py

IMPORTANT: Always use full paths with {project_path} prefix. Use list_directory to explore, then read files directly.

Provide a summary of:
- Code formatting standards (black, ruff, etc.)
- Linting requirements
- Type checking expectations
- Docstring style (Google, NumPy, etc.)
- Testing framework and structure
- Coverage requirements
- How to run quality checks locally
- CI/CD quality gates

Focus on what contributors need to know to write acceptable code.""",
                ),
                WorkflowStep(
                    name="contribution_workflow",
                    display_name="Contribution Workflow Discovery",
                    model_preference="workflows",
                    prompt_template="""Discover the contribution workflow and git practices.

Your task: Understand how to submit contributions.

Steps:
1. Check if {project_path}/CONTRIBUTING.md exists and read it
2. Use execute_command with "git log --oneline -10" in {project_path} to see commit messages
3. Check {project_path}/.github/pull_request_template.md if it exists
4. Use list_directory on {project_path}/.github/ISSUE_TEMPLATE/ to see issue templates
5. Use execute_command with "git branch -a" to check branch patterns
6. Check {project_path}/.pre-commit-config.yaml
7. Use list_directory on {project_path}/.github/workflows/ for CI/CD

IMPORTANT: Always use full paths with {project_path} prefix. Use list_directory to explore directories, then read specific files.

Provide a summary of:
- Fork vs branch workflow
- Branch naming conventions
- Commit message format (conventional commits, etc.)
- PR process and requirements
- Code review expectations
- CI/CD checks that must pass
- How to handle feedback
- Who reviews and merges

Focus on the step-by-step process from idea to merged PR.""",
                ),
                WorkflowStep(
                    name="architecture_guide",
                    display_name="Architecture & Patterns Discovery",
                    model_preference="architecture",
                    prompt_template="""Discover where and how to add features.

Your task: Help contributors understand the codebase structure.

Steps:
1. Use list_directory on {project_path}/src/ to see project structure
2. Use list_directory on {project_path}/src/hrisa_code/core/ and {project_path}/src/hrisa_code/tools/
3. Read {project_path}/src/hrisa_code/core/base_orchestrator.py to understand patterns
4. Check for {project_path}/ARCHITECTURE.md, {project_path}/CLAUDE.md, {project_path}/docs/ARCHITECTURE.md
5. Use list_directory on {project_path}/tests/ to understand test organization
6. Read example orchestrator files like {project_path}/src/hrisa_code/core/api_orchestrator.py

IMPORTANT: Always use full paths with {project_path} prefix. Use list_directory to explore, then read specific files with absolute paths.

Provide a summary of:
- High-level architecture overview
- Where different types of code live (core, tools, etc.)
- How to add a new feature (which files to touch)
- Common patterns to follow (tool classes, orchestrators, etc.)
- Where to add tests
- How to document new features
- Examples of good contributions to reference

Focus on making it easy to know WHERE to add code and HOW to structure it.""",
                ),
            ],
            synthesis_prompt_template="""You have completed a thorough analysis for CONTRIBUTING.md generation.

Here are your findings from each discovery step:
{discoveries}

---

Your task: Generate a COMPREHENSIVE CONTRIBUTING.md file for contributors.

This should be welcoming, clear, and make it easy for anyone to contribute.

Required sections (in this order):
1. **Welcome & Introduction**
   - Thank contributors for their interest
   - Link to CODE_OF_CONDUCT.md if it exists
   - Brief overview of contribution types (code, docs, issues, etc.)

2. **Getting Started**
   - Prerequisites (Python version, tools)
   - Fork and clone instructions
   - Development environment setup
   - Installing dependencies
   - Running the project locally

3. **Development Workflow**
   - Creating a branch (naming conventions)
   - Making changes
   - Running tests locally
   - Running linters/formatters
   - Committing changes (commit message format)

4. **Code Standards**
   - Code style (black, ruff, etc.)
   - Type hints expectations
   - Docstring requirements
   - Testing requirements
   - How to run quality checks

5. **Testing**
   - How to write tests
   - How to run tests
   - Coverage expectations
   - Test structure and organization

6. **Submitting Changes**
   - Creating a Pull Request
   - PR title and description guidelines
   - What to include in PR (tests, docs, etc.)
   - CI checks that must pass
   - Review process and timeline

7. **Code Review**
   - What to expect during review
   - How to respond to feedback
   - Iteration and updates
   - When PRs get merged

8. **Project Structure**
   - Overview of directory layout
   - Where different types of code live
   - Key modules and their purposes
   - Where to add new features

9. **Common Contribution Types**
   - Adding a new tool (with example)
   - Adding a new orchestrator (with example)
   - Fixing bugs
   - Improving documentation
   - Adding tests

10. **Resources**
    - Links to documentation
    - Architecture guides
    - Development guides
    - Communication channels (Discord, Issues, etc.)

11. **Questions?**
    - Where to ask questions
    - How to get help

Format Guidelines:
- Use welcoming, encouraging language
- Include concrete examples and code snippets
- Use checkboxes for step-by-step processes
- Make it skimmable with clear headings
- Include commands that contributors can copy-paste
- Assume contributor is smart but new to the project
- Focus on WORKFLOW and PROCESS, not just rules

Generate the COMPLETE CONTRIBUTING.md content now:""",
        )

    async def generate_contributing(self) -> str:
        """Execute the full orchestration to generate CONTRIBUTING.md.

        This is a convenience method that calls the base generate() method.

        Returns:
            The generated CONTRIBUTING.md content
        """
        return await self.generate()
