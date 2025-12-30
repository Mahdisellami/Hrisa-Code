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
    ):
        """Initialize the agent loop.

        Args:
            conversation_manager: The conversation manager for LLM interactions
            max_iterations: Maximum number of reasoning iterations
            enable_reflection: Whether to add reflection prompts
        """
        self.conversation = conversation_manager
        self.max_iterations = max_iterations
        self.enable_reflection = enable_reflection
        self.console = Console()

        # State tracking
        self.current_iteration = 0
        self.task_complete = False
        self.error_count = 0

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

    async def execute_task_stream(self, task: str) -> None:
        """Execute a task with streaming output.

        This is similar to execute_task but streams responses as they come.
        Currently just calls execute_task (streaming to be implemented).

        Args:
            task: The task to execute
        """
        await self.execute_task(task)
