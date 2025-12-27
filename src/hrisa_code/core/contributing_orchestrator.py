"""Orchestrator for CONTRIBUTING.md generation.

This module guides an LLM through structured discovery steps to create
comprehensive contributor guidelines for open-source projects.
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
1. Read README.md for existing setup instructions
2. Read pyproject.toml for dependencies and dev dependencies
3. Use find_files or list_directory to locate setup scripts (Makefile in root, scripts/ directory)
4. Use find_files to check for Docker support (Dockerfile, docker-compose.yml in root)
5. Identify Python version requirements from pyproject.toml
6. Check for virtual environment recommendations in README or setup scripts
7. Use find_files to look for pre-commit config (.pre-commit-config.yaml) or git hooks
8. Check for environment variables or config files needed

IMPORTANT: Use find_files to locate files before trying to read them. Read files directly rather than using complex search patterns.

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
1. Read pyproject.toml and look for [tool.ruff], [tool.black], [tool.mypy], [tool.pytest] sections
2. Use find_files to check for standalone config files (ruff.toml, mypy.ini, pytest.ini)
3. Read Makefile to find quality check commands (format, lint, type-check, test)
4. Use list_directory on tests/ to understand test structure
5. Use find_files to check for CI/CD config (.github/workflows/)
6. Read a few example source files to see docstring and type hint patterns

IMPORTANT: Read config files directly. Use find_files to locate files before reading them.

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
1. Use find_files to check for existing CONTRIBUTING.md
2. Use git log commands to examine recent commit message style
3. Use find_files to look for PR templates (.github/pull_request_template.md)
4. Use find_files to check for issue templates (.github/ISSUE_TEMPLATE/)
5. Use git branch commands to check branch naming patterns
6. Use find_files for pre-commit config (.pre-commit-config.yaml)
7. Use find_files to check CI/CD (.github/workflows/)

IMPORTANT: Use find_files and list_directory to locate files. Read files directly rather than searching.

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
1. Use list_directory on src/ to see project structure
2. Use find_files to locate key modules in src/hrisa_code/core/ and src/hrisa_code/tools/
3. Read a few core files to understand architectural patterns (orchestrators, tools, etc.)
4. Use find_files to check for architecture documentation (ARCHITECTURE.md, CLAUDE.md in docs/ or root)
5. Use list_directory on tests/ to understand test organization
6. Read example files to identify patterns (tool classes, orchestrator classes)

IMPORTANT: Use list_directory and find_files to explore structure. Read files directly.

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
