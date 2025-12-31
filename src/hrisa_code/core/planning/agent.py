"""Agentic loop for autonomous multi-step task execution."""

from __future__ import annotations

import asyncio
from typing import Optional, TYPE_CHECKING
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

if TYPE_CHECKING:
    from hrisa_code.core.conversation import ConversationManager

from hrisa_code.core.planning.complexity_detector import ComplexityDetector
from hrisa_code.core.planning.dynamic_planner import DynamicPlanner, ExecutionPlan


class AgentLoop:
    """Autonomous agent that can execute multi-step tasks.

    This agent orchestrates complex tasks by:
    1. Breaking down the task into steps
    2. Proactively exploring the codebase
    3. Executing actions with tools
    4. Reflecting on results
    5. Deciding when the task is complete
    """

    # Completion markers that indicate the agent is done
    COMPLETION_MARKERS = [
        "[TASK_COMPLETE]",
        "[DONE]",
        "[FINISHED]",
    ]

    def __init__(
        self,
        conversation_manager: ConversationManager,
        max_iterations: int = 10,
        enable_reflection: bool = True,
        enable_planning: bool = True,
    ):
        """Initialize the agent loop.

        Args:
            conversation_manager: The conversation manager for LLM interactions
            max_iterations: Maximum number of reasoning iterations
            enable_reflection: Whether to add reflection prompts
            enable_planning: Whether to use dynamic planning for complex tasks
        """
        self.conversation = conversation_manager
        self.max_iterations = max_iterations
        self.enable_reflection = enable_reflection
        self.enable_planning = enable_planning
        self.console = Console()

        # Planning components
        self.complexity_detector = ComplexityDetector(
            ollama_client=conversation_manager.ollama_client,
            evaluation_model=conversation_manager.ollama_client.config.model
        )
        self.dynamic_planner = DynamicPlanner(
            ollama_client=conversation_manager.ollama_client,
            planning_model=conversation_manager.ollama_client.config.model
        )

        # State tracking
        self.current_iteration = 0
        self.task_complete = False
        self.error_count = 0
        self.current_plan: Optional[ExecutionPlan] = None

    def _get_agentic_system_prompt_additions(self) -> str:
        """Get additional system prompt instructions for agentic behavior.

        Returns:
            Additional system prompt text
        """
        return """

## AGENTIC MODE - AUTONOMOUS TASK EXECUTION

You are now in AGENTIC MODE. This means you should work autonomously to complete tasks:

1. THINK BEFORE ACTING:
   - Break down complex tasks into logical steps
   - Consider what information you need before making changes
   - Plan your approach before executing

2. PROACTIVE EXPLORATION:
   - Read relevant files to understand context BEFORE making changes
   - Search for similar patterns in the codebase
   - Check for dependencies and related code
   - Don't assume - verify by reading files

3. MULTI-STEP REASONING:
   - Execute one logical step at a time
   - Reflect on results after each step
   - Adjust your approach based on what you learn
   - Continue until the task is fully complete

4. ERROR RECOVERY:
   - If a tool fails, try a different approach
   - Don't give up after first failure
   - Learn from errors and adapt

5. COMPLETION:
   - Only finish when the task is truly complete
   - Verify your work before declaring completion
   - When done, end your response with [TASK_COMPLETE]

EXAMPLE WORKFLOW:
User: "Add error handling to the API endpoints"

Step 1: Explore
- Search for API endpoint files
- Read endpoint implementations
- Understand current error handling

Step 2: Plan
- Identify what error handling is missing
- Decide on approach (try/catch, middleware, etc.)

Step 3: Implement
- Add error handling code
- Follow existing patterns

Step 4: Verify
- Check if all endpoints are covered
- Ensure code quality

Step 5: Complete
- Summarize what was done
- [TASK_COMPLETE]

Remember: Be thorough, proactive, and autonomous. Don't ask for permission for each step - just do it.
"""

    def _augment_system_prompt(self) -> None:
        """Augment the conversation's system prompt with agentic instructions."""
        agentic_additions = self._get_agentic_system_prompt_additions()
        if agentic_additions not in self.conversation.system_prompt:
            self.conversation.system_prompt += agentic_additions

    def _is_task_complete(self, response: str) -> bool:
        """Check if the task is complete based on the response.

        Args:
            response: The LLM's response

        Returns:
            True if task is complete
        """
        if not response:
            return False

        # Check for explicit completion markers
        for marker in self.COMPLETION_MARKERS:
            if marker in response:
                return True

        return False

    def _create_iteration_prompt(self, original_task: str) -> str:
        """Create a prompt for the current iteration.

        Args:
            original_task: The original user task

        Returns:
            Prompt for this iteration
        """
        if self.current_iteration == 0:
            # First iteration - just the task
            return original_task
        else:
            # Subsequent iterations - remind of task and ask for next step
            prompt = (
                f"Continue working on the task: {original_task}\n\n"
                f"This is iteration {self.current_iteration + 1}/{self.max_iterations}. "
            )

            if self.enable_reflection:
                prompt += (
                    "Reflect on what you've done so far and decide on the next step. "
                    "If the task is complete, end your response with [TASK_COMPLETE]."
                )
            else:
                prompt += "What's the next step?"

            return prompt

    async def execute_task(self, task: str) -> str:
        """Execute a task with autonomous multi-step reasoning.

        Args:
            task: The task to execute

        Returns:
            Final response from the agent
        """
        # Augment system prompt with agentic instructions
        self._augment_system_prompt()

        # Display agent mode banner
        self.console.print()
        self.console.print(
            Panel(
                "[bold cyan]AGENTIC MODE ACTIVATED[/bold cyan]\n\n"
                f"Task: {task}\n"
                f"Max iterations: {self.max_iterations}\n"
                f"Reflection: {'enabled' if self.enable_reflection else 'disabled'}\n\n"
                "[dim]The agent will work autonomously to complete this task.[/dim]",
                title="► Agent",
                border_style="cyan",
            )
        )
        self.console.print()

        final_response = ""

        # Main agent loop
        for iteration in range(self.max_iterations):
            self.current_iteration = iteration

            # Show iteration progress
            self.console.print(
                f"[bold cyan]► Iteration {iteration + 1}/{self.max_iterations}[/bold cyan]"
            )
            self.console.print()

            # Create prompt for this iteration
            prompt = self._create_iteration_prompt(task)

            # Execute this step
            try:
                response = await self.conversation.process_message(prompt)

                # Display the response
                if response:
                    self.console.print("[bold blue]Agent:[/bold blue]")
                    self.console.print(response)
                    self.console.print()

                final_response = response

                # Check if tools had errors - add error recovery
                if self.conversation.last_tools_had_errors:
                    self.error_count += 1

                    # Build error summary
                    error_details = []
                    for tool_result in self.conversation.last_tool_results:
                        if tool_result["had_error"]:
                            error_details.append(
                                f"Tool: {tool_result['tool_name']}\n"
                                f"Arguments: {tool_result['arguments']}\n"
                                f"Error: {tool_result['content']}"
                            )

                    error_summary = "\n\n".join(error_details)

                    # Show error recovery prompt
                    self.console.print(
                        Panel(
                            "[yellow]⚠ Tool Errors Detected[/yellow]\n\n"
                            f"{error_summary}\n\n"
                            "[bold]The agent will try a different approach...[/bold]",
                            title="► Error Recovery",
                            border_style="yellow",
                        )
                    )

                    # If too many errors, give up
                    if self.error_count >= 3:
                        self.console.print(
                            Panel(
                                "[red]Too many tool failures (3+ errors)[/red]\n\n"
                                "The agent cannot complete this task with the current model.\n\n"
                                "[dim]Try with a better model (e.g., qwen2.5-coder:32b)[/dim]",
                                title="► Aborted",
                                border_style="red",
                            )
                        )
                        break

                    # Add explicit error recovery to next iteration
                    # Don't allow completion marker if tools failed
                    if self._is_task_complete(response):
                        self.console.print(
                            "[yellow]Note: Agent claimed completion but tools failed. Continuing...[/yellow]"
                        )
                        continue

                # Check if task is complete (only if no tool errors)
                elif self._is_task_complete(response):
                    self.task_complete = True
                    self.console.print(
                        Panel(
                            "[bold green]✓ Task completed successfully![/bold green]\n\n"
                            f"Completed in {iteration + 1} iterations",
                            title="► Success",
                            border_style="green",
                        )
                    )
                    break

            except Exception as e:
                self.error_count += 1
                self.console.print(f"[red]Error in iteration {iteration + 1}: {str(e)}[/red]")

                # If too many errors, give up
                if self.error_count >= 3:
                    self.console.print("[red]Too many errors, aborting agent loop[/red]")
                    break

                # Otherwise continue to next iteration
                continue

        # If we didn't complete, show a message
        if not self.task_complete:
            self.console.print(
                Panel(
                    "[yellow]⚠ Agent stopped without completing task[/yellow]\n\n"
                    f"Reached iteration limit ({self.max_iterations}) or encountered errors.\n"
                    "The agent made progress but didn't finish completely.\n\n"
                    "[dim]You can continue manually or adjust the task.[/dim]",
                    title="► Incomplete",
                    border_style="yellow",
                )
            )

        return final_response

    async def execute_with_plan(self, task: str, plan: Optional[ExecutionPlan] = None) -> str:
        """Execute a task using a generated execution plan.

        This method implements adaptive execution:
        1. Generate plan if not provided
        2. Execute steps sequentially
        3. Track progress
        4. Adapt plan based on discoveries
        5. Handle errors with recovery

        Args:
            task: The task to execute
            plan: Optional pre-generated plan (will generate if not provided)

        Returns:
            Final response after plan execution
        """
        # Generate plan if not provided
        if not plan:
            # Analyze complexity first
            with self.console.status("[bold blue]Analyzing task complexity...", spinner="dots"):
                complexity_analysis = self.complexity_detector.analyze(task)

            # For SIMPLE tasks, skip planning and use direct execution
            if complexity_analysis.complexity.value == "simple":
                self.console.print(
                    f"[yellow]Task is {complexity_analysis.complexity.value.upper()} - "
                    f"using direct execution instead of planning[/yellow]"
                )
                return await self.execute_task(task)

            # Generate plan for moderate/complex tasks
            with self.console.status(
                f"[bold cyan]Task complexity: {complexity_analysis.complexity.value.upper()} - generating execution plan...",
                spinner="dots"
            ):
                plan = await self.dynamic_planner.generate_plan(
                    task=task,
                    complexity=complexity_analysis.complexity.value.upper(),
                    context=None  # TODO: Add codebase context
                )

            # Validate plan
            if not self.dynamic_planner.validate_plan(plan):
                self.console.print("[yellow]Generated plan invalid - falling back to agent mode[/yellow]")
                # Fall back to regular execution
                return await self.execute_task(task)

        self.current_plan = plan

        # Display plan
        self._display_plan(plan)

        # Augment system prompt with agentic instructions
        self._augment_system_prompt()

        final_response = ""

        # Execute plan step by step
        while not plan.is_complete():
            next_step = plan.get_next_step()

            if not next_step:
                # No available steps (dependencies not met or all complete)
                break

            # Display current step
            self._display_step_start(next_step, plan)

            # Execute the step with spinner for long-running operations
            try:
                # Show spinner during execution
                with self.console.status(
                    f"[bold blue]Executing step {next_step.step_number}: {next_step.description}...",
                    spinner="dots"
                ):
                    step_result = await self._execute_step(next_step, task)

                # Mark step complete
                plan.mark_step_complete(next_step.step_number, step_result)

                # Display completion
                self._display_step_complete(next_step, plan)

                final_response = step_result

                # Check if plan needs refinement based on discoveries
                if self.enable_planning and "unexpected" in step_result.lower():
                    refined_plan = await self.dynamic_planner.refine_plan(
                        plan, step_result
                    )
                    if refined_plan.status.value == "refined":
                        self.console.print("[yellow]📋 Plan refined based on discoveries[/yellow]")
                        plan = refined_plan
                        self.current_plan = plan

            except Exception as e:
                # Handle step failure
                error_msg = f"Step {next_step.step_number} failed: {str(e)}"
                self.console.print(f"[red]✗ {error_msg}[/red]")

                # Mark step as failed but continue
                plan.mark_step_complete(next_step.step_number, f"FAILED: {error_msg}")

                # Try to recover or replan
                self.error_count += 1
                if self.error_count > 3:
                    break

        # Display final status
        self._display_plan_completion(plan)

        return final_response

    def _display_plan(self, plan: ExecutionPlan) -> None:
        """Display the execution plan to the user.

        Args:
            plan: The execution plan to display
        """
        from rich.table import Table

        table = Table(title=f"📋 Execution Plan: {plan.task}", show_header=True, header_style="bold cyan")
        table.add_column("#", style="dim", width=3)
        table.add_column("Step", style="cyan")
        table.add_column("Type", style="magenta")
        table.add_column("Dependencies", style="yellow", width=12)

        for step in plan.steps:
            deps = ", ".join(str(d) for d in step.dependencies) if step.dependencies else "none"
            table.add_row(
                str(step.step_number),
                step.description[:50] + "..." if len(step.description) > 50 else step.description,
                step.type.value,
                deps
            )

        self.console.print()
        self.console.print(table)
        self.console.print()

        # Display plan metadata
        self.console.print(f"[dim]Complexity: {plan.complexity} | Steps: {plan.total_steps} | Confidence: {plan.confidence:.0%}[/dim]")

        if plan.risks:
            self.console.print(f"[yellow]⚠ Risks: {', '.join(plan.risks)}[/yellow]")

        self.console.print()

    def _display_step_start(self, step: "PlanStep", plan: ExecutionPlan) -> None:
        """Display step start message.

        Args:
            step: The step being started
            plan: The execution plan
        """
        progress = plan.get_progress()
        self.console.print(
            f"[bold cyan]► Step {step.step_number}/{plan.total_steps}[/bold cyan] "
            f"[dim]({progress:.0f}% complete)[/dim]"
        )
        self.console.print(f"   {step.description}")
        self.console.print(f"   [dim]Type: {step.type.value}[/dim]")
        self.console.print()

    def _display_step_complete(self, step: "PlanStep", plan: ExecutionPlan) -> None:
        """Display step completion message.

        Args:
            step: The completed step
            plan: The execution plan
        """
        progress = plan.get_progress()
        self.console.print(
            f"[green]✓ Step {step.step_number} complete[/green] "
            f"[dim]({progress:.0f}% complete)[/dim]"
        )
        self.console.print()

    def _display_plan_completion(self, plan: ExecutionPlan) -> None:
        """Display plan completion status.

        Args:
            plan: The execution plan
        """
        if plan.is_complete():
            self.console.print()
            self.console.print(
                Panel(
                    "[bold green]✓ Plan Completed Successfully[/bold green]\n\n"
                    f"All {plan.total_steps} steps executed.\n\n"
                    "[dim]Task finished.[/dim]",
                    title="► Complete",
                    border_style="green",
                )
            )
        else:
            completed = sum(1 for s in plan.steps if s.completed)
            self.console.print()
            self.console.print(
                Panel(
                    "[yellow]⚠ Plan Incomplete[/yellow]\n\n"
                    f"Completed {completed}/{plan.total_steps} steps.\n"
                    "Some steps could not be finished.\n\n"
                    "[dim]Partial progress made.[/dim]",
                    title="► Incomplete",
                    border_style="yellow",
                )
            )

    async def _execute_step(self, step: "PlanStep", original_task: str) -> str:
        """Execute a single plan step.

        Args:
            step: The step to execute
            original_task: The original task description

        Returns:
            Result of step execution
        """
        # Build prompt for this step
        prompt = self._build_step_prompt(step, original_task)

        # Disable goal tracking during plan step execution
        # Goal tracker evaluates overall task completion, but we're executing a specific step
        # Let the plan orchestration handle step completion logic instead
        original_goal_tracking = self.conversation._goal_tracking_enabled
        self.conversation._goal_tracking_enabled = False

        try:
            # Execute via conversation manager
            response = await self.conversation.process_message(prompt)
            return response or "Step completed"
        finally:
            # Restore original goal tracking state
            self.conversation._goal_tracking_enabled = original_goal_tracking

    def _build_step_prompt(self, step: "PlanStep", original_task: str) -> str:
        """Build prompt for executing a specific step.

        Args:
            step: The step to execute
            original_task: The original task

        Returns:
            Formatted prompt
        """
        prompt = f"""Execute this step from the plan:

Original Task: {original_task}

Current Step ({step.step_number}):
{step.description}

Rationale: {step.rationale}

Expected Tools: {', '.join(step.expected_tools) if step.expected_tools else 'Any appropriate tools'}

Success Criteria: {step.success_criteria}

Execute this step now. Be thorough and use the expected tools. Report what you did.
"""
        return prompt

    async def execute_task_stream(self, task: str) -> None:
        """Execute a task with streaming output.

        This is similar to execute_task but streams responses as they come.
        Currently just calls execute_task (streaming to be implemented).

        Args:
            task: The task to execute
        """
        await self.execute_task(task)
