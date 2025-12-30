"""Base class for progressive context-building orchestrators.

This provides a framework for orchestrators that:
1. Extract ground-truth facts (static analysis, no LLM)
2. Build sections incrementally with validation
3. Assemble (don't synthesize) final document

This prevents hallucination by avoiding freeform "synthesis" thinking.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any, List
from rich.console import Console
from rich.panel import Panel

from hrisa_code.core.conversation import ConversationManager
from hrisa_code.tools.cli_introspection import extract_pyproject_metadata


@dataclass
class PhaseDefinition:
    """Defines a single phase in progressive orchestration.

    Attributes:
        name: Internal name (e.g., "title", "features")
        display_name: Human-readable name (e.g., "Title Section")
        description: What this phase does
        uses_llm: Whether this phase requires LLM (vs static analysis)
        validates: Optional validation function name
    """

    name: str
    display_name: str
    description: str
    uses_llm: bool = True
    validates: Optional[str] = None


@dataclass
class ProgressiveWorkflow:
    """Defines a complete progressive orchestration workflow.

    Attributes:
        name: Workflow name (e.g., "README", "API")
        description: What this workflow generates
        output_filename: Generated file name (e.g., "README.md")
        phases: List of phases to execute
        audience: Target audience
    """

    name: str
    description: str
    output_filename: str
    phases: List[PhaseDefinition]
    audience: str = "developers"


class ProgressiveBaseOrchestrator(ABC):
    """Base class for progressive orchestration workflows.

    Progressive orchestration differs from base orchestration:
    - Extracts ground-truth facts first (static analysis)
    - Builds sections incrementally with validation
    - Assembles final document (no synthesis thinking)
    - Prevents hallucination through factual grounding

    Workflow:
        1. Extract facts from project metadata
        2. Build each section with validation
        3. Assemble final document from sections

    Subclasses must implement:
        - workflow_definition property
        - extract_facts() method
        - build_X_section() methods for each phase
        - assemble_document() method
    """

    def __init__(
        self,
        conversation: ConversationManager,
        project_path: Path,
        console: Optional[Console] = None,
    ):
        """Initialize progressive orchestrator.

        Args:
            conversation: Conversation manager for LLM interactions
            project_path: Path to the project root
            console: Rich console for output
        """
        self.conversation = conversation
        self.project_path = project_path
        self.console = console or Console()

        # Storage for facts and sections
        self.facts: Dict[str, Any] = {}
        self.sections: Dict[str, str] = {}

    @property
    @abstractmethod
    def workflow_definition(self) -> ProgressiveWorkflow:
        """Get the workflow definition for this orchestrator.

        Subclasses MUST override this property.

        Returns:
            ProgressiveWorkflow describing phases and assembly
        """
        pass

    def _show_phase_header(self, phase: PhaseDefinition, phase_num: int, total: int) -> None:
        """Display phase header panel.

        Args:
            phase: Phase definition
            phase_num: Current phase number (1-indexed)
            total: Total number of phases
        """
        self.console.print()
        self.console.print(
            Panel(
                f"[bold cyan]Phase {phase_num}/{total}: {phase.display_name}[/bold cyan]\n"
                f"{phase.description}",
                border_style="cyan",
            )
        )

    def _show_phase_result(self, success: bool, message: str) -> None:
        """Display phase result.

        Args:
            success: Whether phase succeeded
            message: Result message
        """
        if success:
            self.console.print(f"[green]✓[/green] {message}")
        else:
            self.console.print(f"[red]✗[/red] {message}")

    def extract_project_metadata(self) -> Dict[str, Any]:
        """Extract metadata from pyproject.toml using static analysis.

        Returns:
            Dictionary of project metadata
        """
        pyproject_path = self.project_path / "pyproject.toml"
        if not pyproject_path.exists():
            return {}

        return extract_pyproject_metadata(pyproject_path)

    @abstractmethod
    async def extract_facts(self) -> Dict[str, Any]:
        """Phase 1: Extract ground-truth facts.

        Must be implemented by subclasses to extract facts specific
        to their document type.

        Returns:
            Dictionary of validated facts
        """
        pass

    @abstractmethod
    async def assemble_document(self) -> str:
        """Final phase: Assemble all sections into final document.

        Must be implemented by subclasses to define assembly logic.

        Returns:
            Complete document content
        """
        pass

    async def generate(self) -> str:
        """Execute the full progressive orchestration workflow.

        This is the main entry point.

        Returns:
            Generated document content
        """
        workflow = self.workflow_definition

        # Display orchestration start
        self.console.print()
        self.console.print(
            Panel(
                f"[bold green]Progressive {workflow.name.upper()} Generation[/bold green]\n\n"
                f"Project: {self.project_path}\n"
                f"Model: {self.conversation.get_current_model()}\n"
                f"Strategy: Extract → Build → Validate → Assemble",
                border_style="green",
            )
        )

        # Display orchestration strategy
        self.console.print()
        self.console.print(
            Panel(
                f"[bold cyan]► Starting Progressive Orchestration[/bold cyan]\n"
                f"Progressive {workflow.name} Generation\n"
                f"Project: {self.project_path}\n"
                f"Strategy: Extract → Build → Validate → Assemble",
                border_style="cyan",
            )
        )

        # Phase 1: Extract facts (always first)
        total_phases = len(workflow.phases) + 1  # +1 for assembly
        self._show_phase_header(
            PhaseDefinition(
                name="extract_facts",
                display_name="Ground Truth Extraction",
                description="Parsing pyproject.toml directly (no LLM)...",
                uses_llm=False,
            ),
            1,
            total_phases,
        )

        self.facts = await self.extract_facts()

        if self.facts:
            name = self.facts.get("name", "UNKNOWN")
            version = self.facts.get("version", "0.0.0")
            self._show_phase_result(True, f"Facts extracted: {name} v{version}")
        else:
            self._show_phase_result(False, "Failed to extract facts")

        # Execute build phases (defined by subclass)
        for i, phase in enumerate(workflow.phases, start=2):
            self._show_phase_header(phase, i, total_phases)

            # Call the phase method dynamically
            method_name = f"build_{phase.name}_section"
            if hasattr(self, method_name):
                method = getattr(self, method_name)
                section_content = await method()
                self.sections[phase.name] = section_content

                # Validate if validation function provided
                if phase.validates:
                    validation_passed = self._validate_section(
                        section_content, phase.validates
                    )
                    self._show_phase_result(
                        validation_passed, f"{phase.display_name} built"
                    )
                else:
                    self._show_phase_result(True, f"{phase.display_name} built")
            else:
                self._show_phase_result(
                    False, f"Method {method_name} not implemented"
                )

        # Final phase: Assembly
        self._show_phase_header(
            PhaseDefinition(
                name="assembly",
                display_name="Document Assembly",
                description=f"Assembling {workflow.output_filename} from validated sections...",
                uses_llm=False,
            ),
            total_phases,
            total_phases,
        )

        content = await self.assemble_document()

        if content:
            self._show_phase_result(True, f"{workflow.output_filename} assembled")
        else:
            self._show_phase_result(False, "Assembly failed")

        # Display completion
        self.console.print()
        self.console.print(
            Panel(
                f"[bold green]✓ {workflow.output_filename} Complete[/bold green]\n\n"
                f"All {total_phases} phases completed successfully.",
                border_style="green",
            )
        )
        self.console.print()

        return content

    def _validate_section(self, content: str, validator_name: str) -> bool:
        """Validate section content using named validator.

        Args:
            content: Section content to validate
            validator_name: Name of validation function

        Returns:
            True if validation passed
        """
        # Default validation: check content is not empty
        if validator_name == "not_empty":
            return bool(content and content.strip())

        # Subclasses can override for custom validation
        return True
