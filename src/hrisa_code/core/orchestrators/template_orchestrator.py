"""Template-based orchestrator for configurable documentation generation.

This module demonstrates how to use the base orchestrators with configuration
instead of hard-coded subclasses. Useful for creating custom documentation
workflows without writing new orchestrator classes.
"""

from pathlib import Path
from typing import Optional, Dict, Any, List
from rich.console import Console

from hrisa_code.core.conversation import ConversationManager
from hrisa_code.core.model_router import ModelRouter
from hrisa_code.core.orchestrators.base_orchestrator import (
    BaseOrchestrator,
    WorkflowStep,
    WorkflowDefinition,
)
from hrisa_code.core.orchestrators.progressive_base import (
    ProgressiveBaseOrchestrator,
    PhaseDefinition,
    ProgressiveWorkflow,
)


class TemplateOrchestrator(BaseOrchestrator):
    """Configurable orchestrator using workflow templates.

    Instead of creating a subclass, pass a WorkflowDefinition to configure
    the orchestration workflow.

    Example:
        ```python
        workflow = WorkflowDefinition(
            name="Custom Doc",
            description="Generate custom documentation",
            steps=[
                WorkflowStep(
                    name="overview",
                    display_name="Overview Analysis",
                    prompt_template="Analyze {project_path} and provide overview..."
                ),
                WorkflowStep(
                    name="details",
                    display_name="Detailed Analysis",
                    prompt_template="Analyze {project_path} in detail..."
                ),
            ],
            synthesis_prompt_template="Generate doc from:\\n{discoveries}",
            output_filename="CUSTOM.md",
            audience="developers"
        )

        orchestrator = TemplateOrchestrator(
            conversation=conversation,
            project_path=Path("."),
            workflow=workflow
        )
        content = await orchestrator.generate()
        ```
    """

    def __init__(
        self,
        conversation: ConversationManager,
        project_path: Path,
        workflow: WorkflowDefinition,
        console: Optional[Console] = None,
        model_router: Optional[ModelRouter] = None,
        enable_multi_model: bool = False,
    ):
        """Initialize template orchestrator.

        Args:
            conversation: ConversationManager for LLM interactions
            project_path: Path to the project root
            workflow: Workflow definition to execute
            console: Rich console for output (creates new if None)
            model_router: Optional ModelRouter for multi-model orchestration
            enable_multi_model: Whether to use multi-model orchestration
        """
        super().__init__(
            conversation=conversation,
            project_path=project_path,
            console=console,
            model_router=model_router,
            enable_multi_model=enable_multi_model,
        )
        self._workflow = workflow

    @property
    def workflow_definition(self) -> WorkflowDefinition:
        """Return the configured workflow.

        Returns:
            The workflow definition passed during initialization
        """
        return self._workflow


class ProgressiveTemplateOrchestrator(ProgressiveBaseOrchestrator):
    """Configurable progressive orchestrator using workflow templates.

    Instead of creating a subclass, pass a ProgressiveWorkflow and implement
    phase methods dynamically or via configuration.

    Example:
        ```python
        workflow = ProgressiveWorkflow(
            name="Custom Progressive Doc",
            description="Generate documentation progressively",
            output_filename="CUSTOM.md",
            phases=[
                PhaseDefinition(
                    name="overview",
                    display_name="Overview Section",
                    description="Build overview from facts",
                    uses_llm=False
                ),
            ],
            audience="developers"
        )

        orchestrator = ProgressiveTemplateOrchestrator(
            conversation=conversation,
            project_path=Path("."),
            workflow=workflow,
            phase_builders={
                "overview": build_overview_fn,
            }
        )
        content = await orchestrator.generate()
        ```
    """

    def __init__(
        self,
        conversation: ConversationManager,
        project_path: Path,
        workflow: ProgressiveWorkflow,
        phase_builders: Optional[Dict[str, Any]] = None,
        console: Optional[Console] = None,
    ):
        """Initialize progressive template orchestrator.

        Args:
            conversation: Conversation manager for LLM interactions
            project_path: Path to the project root
            workflow: Progressive workflow definition
            phase_builders: Dictionary mapping phase names to builder functions
            console: Rich console for output
        """
        super().__init__(
            conversation=conversation, project_path=project_path, console=console
        )
        self._workflow = workflow
        self._phase_builders = phase_builders or {}

    @property
    def workflow_definition(self) -> ProgressiveWorkflow:
        """Return the configured workflow.

        Returns:
            The workflow definition passed during initialization
        """
        return self._workflow

    async def extract_facts(self) -> Dict[str, Any]:
        """Extract ground-truth facts from project metadata.

        Returns:
            Dictionary of project facts
        """
        metadata = self.extract_project_metadata()

        return {
            "name": metadata.get("name", "UNKNOWN"),
            "description": metadata.get("description", ""),
            "version": metadata.get("version", "0.0.0"),
            "python_requires": metadata.get("python_requires", ">=3.10"),
            "dependencies": metadata.get("dependencies", []),
            "license": metadata.get("license", ""),
        }

    async def assemble_document(self) -> str:
        """Assemble all sections into final document.

        Returns:
            Complete document content
        """
        # Simple assembly: concatenate all sections
        parts = []

        for phase in self._workflow.phases:
            if phase.name in self.sections:
                parts.append(self.sections[phase.name])

        return "\n\n".join(parts)

    def __getattribute__(self, name: str) -> Any:
        """Dynamically handle build_X_section method calls.

        This allows phase_builders to define methods without subclassing.

        Args:
            name: Attribute name

        Returns:
            Attribute value or dynamically created method
        """
        # Check if it's a build_X_section method
        if name.startswith("build_") and name.endswith("_section"):
            phase_name = name[6:-8]  # Remove "build_" and "_section"

            # If we have a builder function for this phase, return it
            phase_builders = object.__getattribute__(self, "_phase_builders")
            if phase_name in phase_builders:
                return phase_builders[phase_name]

        # Otherwise, use normal attribute access
        return object.__getattribute__(self, name)


# Example workflow templates

CHANGELOG_WORKFLOW = WorkflowDefinition(
    name="Changelog",
    description="Generate a CHANGELOG.md from git history",
    steps=[
        WorkflowStep(
            name="git_history",
            display_name="Git History Analysis",
            prompt_template=(
                "Analyze the git history of {project_path}. "
                "List commits, identify notable changes, bug fixes, and new features. "
                "Use git_log and git_diff tools."
            ),
        ),
        WorkflowStep(
            name="categorization",
            display_name="Change Categorization",
            prompt_template=(
                "Categorize the changes into: Added, Changed, Deprecated, "
                "Removed, Fixed, Security. Use semantic versioning principles."
            ),
        ),
    ],
    synthesis_prompt_template=(
        "Generate a CHANGELOG.md file following the Keep a Changelog format. "
        "Use the discovered information:\n{discoveries}\n\n"
        "Format:\n"
        "# Changelog\n\n"
        "## [Unreleased]\n"
        "### Added\n"
        "### Changed\n"
        "### Fixed\n"
    ),
    output_filename="CHANGELOG.md",
    audience="developers and users",
)

ARCHITECTURE_WORKFLOW = WorkflowDefinition(
    name="Architecture",
    description="Generate architecture documentation",
    steps=[
        WorkflowStep(
            name="structure",
            display_name="Project Structure",
            prompt_template=(
                "Analyze the project structure of {project_path}. "
                "Identify main directories, modules, and their purposes."
            ),
        ),
        WorkflowStep(
            name="components",
            display_name="Component Analysis",
            prompt_template=(
                "Identify key components/classes and their responsibilities. "
                "Map relationships and dependencies."
            ),
        ),
        WorkflowStep(
            name="patterns",
            display_name="Design Patterns",
            prompt_template=(
                "Identify design patterns and architectural decisions. "
                "Explain key architectural choices."
            ),
        ),
    ],
    synthesis_prompt_template=(
        "Generate an ARCHITECTURE.md document:\n{discoveries}\n\n"
        "Include:\n"
        "1. High-level architecture diagram (as text/ASCII)\n"
        "2. Component descriptions\n"
        "3. Design patterns used\n"
        "4. Key architectural decisions and rationale\n"
    ),
    output_filename="ARCHITECTURE.md",
    audience="developers and architects",
)


def create_custom_orchestrator(
    conversation: ConversationManager,
    project_path: Path,
    workflow_name: str,
    console: Optional[Console] = None,
) -> Optional[BaseOrchestrator]:
    """Factory function to create orchestrators from template names.

    Args:
        conversation: ConversationManager instance
        project_path: Path to project
        workflow_name: Name of workflow template ("changelog", "architecture")
        console: Optional console for output

    Returns:
        Configured orchestrator or None if workflow_name unknown
    """
    workflows = {
        "changelog": CHANGELOG_WORKFLOW,
        "architecture": ARCHITECTURE_WORKFLOW,
    }

    workflow = workflows.get(workflow_name.lower())
    if not workflow:
        return None

    return TemplateOrchestrator(
        conversation=conversation,
        project_path=project_path,
        workflow=workflow,
        console=console,
    )
