"""Goal tracking system to detect task completion and prevent aimless exploration."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json


class GoalStatus(Enum):
    """Status of goal progress."""
    UNKNOWN = "unknown"              # Not yet evaluated
    IN_PROGRESS = "in_progress"      # Making progress toward goal
    COMPLETE = "complete"            # Goal achieved, can provide answer
    STUCK = "stuck"                  # Not making progress, need intervention
    CLARIFICATION_NEEDED = "clarification_needed"  # User intent unclear


@dataclass
class ToolResult:
    """Represents a tool execution result."""
    tool_name: str
    arguments: Dict[str, Any]
    result: str
    round_number: int
    had_error: bool


class GoalTracker:
    """Tracks progress toward answering the user's question.

    This class uses lightweight LLM evaluation to determine if we have
    enough information to answer the user's question, preventing aimless
    tool calling and detecting when the task is complete.
    """

    def __init__(
        self,
        ollama_client=None,  # Will be injected from ConversationManager
        evaluation_model: str = "qwen2.5-coder:7b",  # Lightweight model for checks
        check_frequency: int = 3,  # Check after every N tool rounds
    ):
        """Initialize the goal tracker.

        Args:
            ollama_client: OllamaClient instance for progress evaluation
            evaluation_model: Lightweight model for progress checks (default: qwen2.5-coder:7b)
            check_frequency: Check progress every N rounds (default: 3)
        """
        self.ollama_client = ollama_client
        self.evaluation_model = evaluation_model
        self.check_frequency = check_frequency

        # Track state
        self.user_question: Optional[str] = None
        self.tool_results: List[ToolResult] = []
        self.current_round = 0
        self.last_check_round = 0
        self.current_status = GoalStatus.UNKNOWN

    def set_user_question(self, question: str) -> None:
        """Set the user's question for this conversation turn.

        Args:
            question: The user's question/request
        """
        self.user_question = question

    def add_tool_result(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        result: str,
        had_error: bool = False
    ) -> None:
        """Add a tool execution result.

        Args:
            tool_name: Name of the tool executed
            arguments: Tool arguments
            result: Tool result
            had_error: Whether the tool had an error
        """
        tool_result = ToolResult(
            tool_name=tool_name,
            arguments=arguments,
            result=result,
            round_number=self.current_round,
            had_error=had_error
        )
        self.tool_results.append(tool_result)

        # Check if user denied an operation - this is a definitive completion
        if result.startswith("[DENIED]"):
            self.current_status = GoalStatus.COMPLETE

    def should_check_progress(self) -> bool:
        """Determine if we should check progress now.

        Returns:
            True if it's time to check progress
        """
        # Check after first round, then every N rounds
        if self.current_round == 1:
            return True

        rounds_since_check = self.current_round - self.last_check_round
        return rounds_since_check >= self.check_frequency

    async def check_progress(self) -> GoalStatus:
        """Evaluate progress toward goal using LLM.

        Returns:
            Current goal status
        """
        if not self.user_question or not self.tool_results:
            return GoalStatus.UNKNOWN

        # If no ollama_client, can't evaluate (testing scenario)
        if not self.ollama_client:
            return GoalStatus.IN_PROGRESS

        self.last_check_round = self.current_round

        # Build evaluation prompt
        tool_summary = self._summarize_tool_results()
        evaluation_prompt = self._build_evaluation_prompt(tool_summary)

        try:
            # Use lightweight model for quick evaluation
            # Save current model and switch
            original_model = self.ollama_client.get_current_model()
            self.ollama_client.switch_model(self.evaluation_model, verbose=False)

            # Get evaluation (use raw API, no history needed)
            response = await self.ollama_client.chat_simple(
                message=evaluation_prompt,
                system_prompt="You are a progress evaluator. Analyze if enough information has been gathered to answer the user's question. Respond with ONLY one word: COMPLETE, IN_PROGRESS, STUCK, or CLARIFICATION_NEEDED."
            )

            # Restore original model
            self.ollama_client.switch_model(original_model, verbose=False)

            # Parse response
            status = self._parse_evaluation_response(response)
            self.current_status = status
            return status

        except Exception as e:
            # If evaluation fails, assume in progress
            return GoalStatus.IN_PROGRESS

    def _summarize_tool_results(self) -> str:
        """Summarize tool results for evaluation.

        Returns:
            Human-readable summary of tool results
        """
        if not self.tool_results:
            return "No tools executed yet."

        lines = []
        for i, result in enumerate(self.tool_results[-5:], 1):  # Last 5 results
            # Truncate long results
            result_preview = result.result[:200]
            if len(result.result) > 200:
                result_preview += "..."

            status = "ERROR" if result.had_error else "OK"
            lines.append(
                f"{i}. {result.tool_name}({json.dumps(result.arguments, sort_keys=True)}): "
                f"[{status}] {result_preview}"
            )

        return "\n".join(lines)

    def _build_evaluation_prompt(self, tool_summary: str) -> str:
        """Build prompt for LLM evaluation.

        Args:
            tool_summary: Summary of tool results

        Returns:
            Evaluation prompt
        """
        return f"""User asked: "{self.user_question}"

Tool results obtained (last 5):
{tool_summary}

Total rounds: {self.current_round}
Total tools executed: {len(self.tool_results)}

Question: Based on these tool results, can we answer the user's question?

Evaluate and respond with ONLY ONE WORD:
- COMPLETE: We have sufficient information to answer the user's question
- IN_PROGRESS: We're making progress but need more information
- STUCK: We're not making progress (e.g., same tool repeatedly, no new info)
- CLARIFICATION_NEEDED: The user's question is unclear or ambiguous

Response (one word only):"""

    def _parse_evaluation_response(self, response: str) -> GoalStatus:
        """Parse LLM evaluation response.

        Args:
            response: LLM response text

        Returns:
            Parsed goal status
        """
        response_clean = response.strip().upper()

        if "COMPLETE" in response_clean:
            return GoalStatus.COMPLETE
        elif "STUCK" in response_clean:
            return GoalStatus.STUCK
        elif "CLARIFICATION" in response_clean:
            return GoalStatus.CLARIFICATION_NEEDED
        elif "PROGRESS" in response_clean:
            return GoalStatus.IN_PROGRESS
        else:
            # Default to in progress if unclear
            return GoalStatus.IN_PROGRESS

    def get_intervention_message(self, status: GoalStatus) -> str:
        """Generate intervention message based on goal status.

        Args:
            status: Current goal status

        Returns:
            Message to inject into conversation
        """
        if status == GoalStatus.COMPLETE:
            return (
                f"[GOAL TRACKER] You appear to have enough information to answer the user's question.\n"
                f"User asked: \"{self.user_question}\"\n"
                f"Tool results collected: {len(self.tool_results)}\n\n"
                f"Please provide a final answer based on the information you've gathered."
            )

        elif status == GoalStatus.STUCK:
            return (
                f"[GOAL TRACKER] Progress appears stuck after {self.current_round} rounds.\n"
                f"User asked: \"{self.user_question}\"\n\n"
                f"You should either:\n"
                f"1. Provide an answer with the information you have\n"
                f"2. Try a completely different approach\n"
                f"3. Ask the user for clarification or more specific requirements"
            )

        elif status == GoalStatus.CLARIFICATION_NEEDED:
            return (
                f"[GOAL TRACKER] The user's intent may be unclear.\n"
                f"User asked: \"{self.user_question}\"\n\n"
                f"Consider asking the user for clarification about what they want."
            )

        return ""

    def get_summary(self) -> str:
        """Get a summary of goal tracking state.

        Returns:
            Human-readable summary
        """
        if not self.user_question:
            return "No active goal"

        error_count = sum(1 for r in self.tool_results if r.had_error)
        unique_tools = len(set(r.tool_name for r in self.tool_results))

        return (
            f"Goal: {self.user_question}\n"
            f"Status: {self.current_status.value}\n"
            f"Rounds: {self.current_round}\n"
            f"Tool calls: {len(self.tool_results)} ({unique_tools} unique tools)\n"
            f"Errors: {error_count}"
        )

    def next_round(self) -> None:
        """Increment the round counter."""
        self.current_round += 1

    def reset(self) -> None:
        """Reset the tracker for a new conversation turn."""
        self.user_question = None
        self.tool_results.clear()
        self.current_round = 0
        self.last_check_round = 0
        self.current_status = GoalStatus.UNKNOWN

    def has_sufficient_info(self) -> bool:
        """Check if we likely have sufficient information.

        This is a heuristic check (doesn't use LLM).

        Returns:
            True if we likely have enough information
        """
        # If we've executed tools and no recent errors, might be sufficient
        if len(self.tool_results) >= 3:
            recent_results = self.tool_results[-3:]
            if not any(r.had_error for r in recent_results):
                return True
        return False

    def is_making_progress(self) -> bool:
        """Check if we're making progress (heuristic).

        Returns:
            True if we appear to be making progress
        """
        if len(self.tool_results) < 4:
            return True  # Early stages, assume progress

        # Check if we're using different tools (diversity = progress)
        recent_tools = [r.tool_name for r in self.tool_results[-4:]]
        unique_recent = len(set(recent_tools))

        # If using at least 2 different tools recently, making progress
        return unique_recent >= 2
