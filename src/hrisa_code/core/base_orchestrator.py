"""Base orchestrator for multi-step documentation generation workflows.

This module provides a reusable framework for orchestrating LLM-guided
documentation generation across multiple discovery steps.
"""

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any, List
from rich.console import Console
from rich.panel import Panel

from hrisa_code.core.conversation import ConversationManager
from hrisa_code.core.model_router import ModelRouter


@dataclass
class WorkflowStep:
    """Defines a single step in a documentation workflow.

    Attributes:
        name: Internal name for the step (e.g., "architecture")
        display_name: Human-readable name (e.g., "Architecture Discovery")
        prompt_template: Template string for the LLM prompt (can use {project_path})
        model_preference: Optional preferred model capability for this step
    """
    name: str
    display_name: str
    prompt_template: str
    model_preference: Optional[str] = None


@dataclass
class WorkflowDefinition:
    """Defines a complete documentation generation workflow.

    Attributes:
        name: Workflow name (e.g., "HRISA", "README")
        description: Short description of what this workflow generates
        steps: List of discovery/analysis steps to execute
        synthesis_prompt_template: Template for synthesizing final document
        output_filename: Name of the generated file (e.g., "HRISA.md", "README.md")
        audience: Target audience description
    """
    name: str
    description: str
    steps: List[WorkflowStep]
    synthesis_prompt_template: str
    output_filename: str
    audience: str = "developers"


class BaseOrchestrator:
    """Base class for multi-step documentation orchestration.

    This orchestrator provides a reusable framework for guiding an LLM through
    structured discovery steps to generate comprehensive documentation.

    Workflow:
        1. Execute discovery steps in sequence
        2. Store findings from each step
        3. Synthesize final documentation
        4. Return generated content

    Subclasses should:
        - Define workflow_definition property
        - Optionally override customize_step_prompt()
        - Optionally override customize_synthesis_prompt()
    """

    def __init__(
        self,
        conversation: ConversationManager,
        project_path: Path,
        console: Optional[Console] = None,
        model_router: Optional[ModelRouter] = None,
        enable_multi_model: bool = False,
    ):
        """Initialize the base orchestrator.

        Args:
            conversation: ConversationManager for LLM interactions
            project_path: Path to the project root
            console: Rich console for output (creates new if None)
            model_router: Optional ModelRouter for multi-model orchestration
            enable_multi_model: Whether to use multi-model orchestration
        """
        self.conversation = conversation
        self.project_path = project_path
        self.console = console or Console()
        self.model_router = model_router
        self.enable_multi_model = enable_multi_model

        # Storage for discoveries from each step
        self.discoveries: Dict[str, Any] = {}

    @property
    def workflow_definition(self) -> WorkflowDefinition:
        """Get the workflow definition for this orchestrator.

        Subclasses MUST override this property to define their workflow.

        Returns:
            WorkflowDefinition describing the steps and synthesis
        """
        raise NotImplementedError("Subclasses must define workflow_definition")

    def customize_step_prompt(self, step: WorkflowStep) -> str:
        """Customize the prompt for a specific step.

        Subclasses can override this to add dynamic content to prompts.

        Args:
            step: The workflow step

        Returns:
            Customized prompt string (default: uses template with project_path)
        """
        # Default: just substitute project_path
        return step.prompt_template.format(project_path=self.project_path)

    def customize_synthesis_prompt(self, workflow: WorkflowDefinition) -> str:
        """Customize the synthesis prompt with all discoveries.

        Subclasses can override this to modify how findings are combined.

        Args:
            workflow: The workflow definition

        Returns:
            Customized synthesis prompt string
        """
        # Build discoveries section
        discoveries_text = ""
        for step in workflow.steps:
            step_name = step.name.upper().replace("_", " ")
            discoveries_text += f"\n## {step_name}:\n{self.discoveries[step.name]}\n"

        # Default: substitute discoveries into template
        return workflow.synthesis_prompt_template.format(
            discoveries=discoveries_text,
            project_path=self.project_path,
        )

    async def _select_model_for_step(self, step: WorkflowStep) -> None:
        """Select and switch to appropriate model for a step.

        Args:
            step: The workflow step to select model for
        """
        if not self.enable_multi_model or not self.model_router:
            return

        # Determine model selection strategy
        if step.model_preference:
            selected_model = self.model_router.select_model_for_orchestration_step(
                step.model_preference
            )
        else:
            selected_model = self.model_router.select_model_for_orchestration_step(
                step.name
            )

        current_model = self.conversation.get_current_model()

        if selected_model != current_model:
            # Get model info for display
            model_info = self.model_router.get_model_info(selected_model)
            reason = model_info.strengths if model_info else "selected for this task"

            # Show model selection
            self.console.print()
            self.console.print(
                Panel(
                    f"[bold yellow]Selected Model: {selected_model}[/bold yellow]\n\n"
                    f"[dim]Reason: {reason}[/dim]",
                    title="► Model Selection",
                    border_style="yellow",
                )
            )

            # Switch model
            self.conversation.switch_model(selected_model, verbose=False)

    async def _execute_step(
        self,
        step: WorkflowStep,
        step_number: int,
        total_steps: int
    ) -> str:
        """Execute a single workflow step.

        Args:
            step: The workflow step to execute
            step_number: Current step number (1-indexed)
            total_steps: Total number of steps

        Returns:
            The LLM's response for this step
        """
        # Select model for this step
        await self._select_model_for_step(step)

        # Display step header
        self.console.print()
        self.console.print(
            Panel(
                f"[bold cyan]Step {step_number}/{total_steps}: {step.display_name}[/bold cyan]\n\n"
                f"[dim]Analyzing {self.project_path.name}...[/dim]",
                title="► Orchestrator",
                border_style="cyan",
            )
        )
        self.console.print()

        # Get customized prompt
        prompt = self.customize_step_prompt(step)

        # Execute the step
        response = await self.conversation.process_message(prompt)

        # Display findings
        if response:
            self.console.print(f"[bold blue]Findings:[/bold blue]")
            self.console.print(response, markup=False)
            self.console.print()

        # Store the discovery
        self.discoveries[step.name] = response

        return response

    async def _synthesize_documentation(self, workflow: WorkflowDefinition) -> str:
        """Synthesize all discoveries into final documentation.

        Args:
            workflow: The workflow definition

        Returns:
            The generated documentation content
        """
        # Select appropriate model for synthesis
        if self.enable_multi_model and self.model_router:
            selected_model = self.model_router.select_model_for_orchestration_step("synthesis")
            current_model = self.conversation.get_current_model()

            if selected_model != current_model:
                model_info = self.model_router.get_model_info(selected_model)
                reason = model_info.strengths if model_info else "selected for this task"

                self.console.print()
                self.console.print(
                    Panel(
                        f"[bold yellow]Selected Model: {selected_model}[/bold yellow]\n\n"
                        f"[dim]Reason: {reason}[/dim]",
                        title="► Model Selection",
                        border_style="yellow",
                    )
                )

                self.conversation.switch_model(selected_model, verbose=False)

        # Display synthesis header
        total_steps = len(workflow.steps) + 1
        self.console.print()
        self.console.print(
            Panel(
                f"[bold cyan]Step {total_steps}/{total_steps}: Documentation Synthesis[/bold cyan]\n\n"
                f"[dim]Generating {workflow.output_filename} from all discoveries...[/dim]",
                title="► Orchestrator",
                border_style="cyan",
            )
        )
        self.console.print()

        # Get customized synthesis prompt
        synthesis_prompt = self.customize_synthesis_prompt(workflow)

        # Generate the documentation
        content = await self.conversation.process_message(synthesis_prompt)

        return content

    async def generate(self) -> str:
        """Execute the full orchestration workflow.

        This is the main entry point for running the orchestration.

        Returns:
            The generated documentation content
        """
        workflow = self.workflow_definition

        # Display orchestration start
        self.console.print()
        self.console.print(
            Panel(
                f"[bold green]{workflow.name.upper()} GENERATION[/bold green]\n\n"
                f"Project: {self.project_path}\n"
                f"Output: {workflow.output_filename}\n"
                f"Audience: {workflow.audience}\n\n"
                f"[dim]{workflow.description}\n\n"
                f"Discovery steps: {len(workflow.steps)}\n"
                f"Total steps: {len(workflow.steps) + 1} (including synthesis)[/dim]",
                title="► Starting Orchestration",
                border_style="green",
            )
        )
        self.console.print()

        # Execute discovery steps
        total_steps = len(workflow.steps) + 1  # +1 for synthesis

        for i, step in enumerate(workflow.steps, start=1):
            await self._execute_step(step, i, total_steps)

        # Synthesize documentation
        content = await self._synthesize_documentation(workflow)

        # Display completion
        self.console.print()
        self.console.print(
            Panel(
                f"[bold green]✓ {workflow.output_filename} generated successfully![/bold green]\n\n"
                f"All {total_steps} steps completed.",
                title="► Complete",
                border_style="green",
            )
        )
        self.console.print()

        return content
