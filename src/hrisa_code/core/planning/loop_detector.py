"""Loop detection system to prevent unproductive repeated tool calls."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json


class LoopStatus(Enum):
    """Status of loop detection check."""
    OK = "ok"                          # No loop detected
    WARNING = "warning"                # Approaching loop threshold
    DETECTED = "detected"              # Loop detected, intervention needed
    CRITICAL = "critical"              # Severe loop (many identical calls)


@dataclass
class ToolCall:
    """Represents a tool call with its metadata."""
    tool_name: str
    arguments: Dict[str, Any]
    round_number: int

    def matches(self, other: "ToolCall") -> bool:
        """Check if this call is identical to another.

        Args:
            other: Another tool call to compare against

        Returns:
            True if tool name and arguments are identical
        """
        return (
            self.tool_name == other.tool_name and
            self._normalize_args(self.arguments) == self._normalize_args(other.arguments)
        )

    @staticmethod
    def _normalize_args(args: Dict[str, Any]) -> str:
        """Normalize arguments for comparison (handle dict order, etc.)."""
        return json.dumps(args, sort_keys=True)


class LoopDetector:
    """Detects and prevents unproductive loops in tool calling.

    This class tracks tool call history and identifies when the LLM is stuck
    in a loop, repeatedly calling the same tool with the same parameters
    without making progress.
    """

    def __init__(
        self,
        max_identical_calls: int = 3,
        warning_threshold: int = 2,
        history_window: int = 20,
    ):
        """Initialize the loop detector.

        Args:
            max_identical_calls: Maximum identical calls before intervention (default: 3)
            warning_threshold: Warn after this many identical calls (default: 2)
            history_window: Number of recent calls to track (default: 20, increased to detect patterns)
        """
        self.max_identical = max_identical_calls
        self.warning_threshold = warning_threshold
        self.history_window = history_window
        self.tool_history: List[ToolCall] = []
        self.current_round = 0

    def add_call(self, tool_name: str, arguments: Dict[str, Any]) -> None:
        """Add a tool call to the history.

        Args:
            tool_name: Name of the tool being called
            arguments: Tool arguments
        """
        call = ToolCall(
            tool_name=tool_name,
            arguments=arguments,
            round_number=self.current_round
        )
        self.tool_history.append(call)

        # Keep history within window size
        if len(self.tool_history) > self.history_window:
            self.tool_history.pop(0)

    def check_loop(self, tool_name: str, arguments: Dict[str, Any]) -> LoopStatus:
        """Check if the next tool call would create a loop.

        Args:
            tool_name: Name of the tool about to be called
            arguments: Tool arguments

        Returns:
            LoopStatus indicating if a loop is detected
        """
        if not self.tool_history:
            return LoopStatus.OK

        # Create temporary call for comparison
        candidate = ToolCall(
            tool_name=tool_name,
            arguments=arguments,
            round_number=self.current_round
        )

        # Count identical calls in recent history
        identical_count = sum(
            1 for call in self.tool_history
            if candidate.matches(call)
        )

        # Check for identical call loops first
        if identical_count >= self.max_identical:
            return LoopStatus.DETECTED
        elif identical_count >= self.warning_threshold:
            return LoopStatus.WARNING

        # Check for semantic loops (same tool, different parameters)
        same_tool_count = sum(
            1 for call in self.tool_history
            if call.tool_name == tool_name
        )

        # If we've called this tool >60% of recent rounds, likely stuck in a pattern
        if len(self.tool_history) >= 5:
            same_tool_ratio = (same_tool_count + 1) / (len(self.tool_history) + 1)
            if same_tool_ratio > 0.6:
                return LoopStatus.WARNING

        # If this tool was called 4+ times in last 6 rounds, warn
        recent_calls = self.tool_history[-6:] if len(self.tool_history) >= 6 else self.tool_history
        recent_same_tool = sum(1 for call in recent_calls if call.tool_name == tool_name)
        if recent_same_tool >= 3:
            return LoopStatus.WARNING

        return LoopStatus.OK

    def get_loop_details(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get details about the detected loop.

        Args:
            tool_name: Name of the tool in the loop
            arguments: Tool arguments

        Returns:
            Dictionary with loop details
        """
        candidate = ToolCall(
            tool_name=tool_name,
            arguments=arguments,
            round_number=self.current_round
        )

        # Find all matching calls
        matching_calls = [
            call for call in self.tool_history
            if candidate.matches(call)
        ]

        return {
            "tool_name": tool_name,
            "arguments": arguments,
            "count": len(matching_calls),
            "first_round": matching_calls[0].round_number if matching_calls else None,
            "rounds": [call.round_number for call in matching_calls],
        }

    def get_intervention_message(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        status: LoopStatus
    ) -> str:
        """Generate an intervention message for the LLM.

        Args:
            tool_name: Name of the tool in the loop
            arguments: Tool arguments
            status: Current loop status

        Returns:
            Message to inject into the conversation
        """
        details = self.get_loop_details(tool_name, arguments)
        identical_count = details["count"]

        # Count total calls to this tool (semantic loop detection)
        same_tool_count = sum(1 for call in self.tool_history if call.tool_name == tool_name)

        if status == LoopStatus.WARNING:
            # Check if this is an identical call warning or semantic loop warning
            if identical_count >= self.warning_threshold:
                return (
                    f"[SYSTEM WARNING] You've called '{tool_name}' {identical_count} times with identical parameters. "
                    f"Consider if you have enough information to answer the user's question, or try a different approach."
                )
            else:
                # Semantic loop warning
                return (
                    f"[SYSTEM WARNING] You've called '{tool_name}' {same_tool_count} times recently with different parameters. "
                    f"You may be stuck in a search loop. Consider:\n"
                    f"1. Summarizing what you've found so far\n"
                    f"2. Trying a completely different tool or approach\n"
                    f"3. Providing an answer based on available information"
                )

        elif status == LoopStatus.DETECTED:
            return (
                f"[SYSTEM INTERVENTION] Loop detected: '{tool_name}' called {identical_count} times with identical parameters.\n\n"
                f"The tool results are not changing. You must either:\n"
                f"1. Provide a final answer based on the information you already have\n"
                f"2. Try a completely different tool or approach\n"
                f"3. Ask the user for clarification if you're unsure what they want\n\n"
                f"DO NOT call this tool again with the same parameters."
            )

        return ""

    def get_summary(self) -> str:
        """Get a summary of the tool call history.

        Returns:
            Human-readable summary of tool calls
        """
        if not self.tool_history:
            return "No tool calls in history"

        # Count calls by tool name
        tool_counts: Dict[str, int] = {}
        for call in self.tool_history:
            tool_counts[call.tool_name] = tool_counts.get(call.tool_name, 0) + 1

        summary_lines = [f"Tool call history ({len(self.tool_history)} total):"]
        for tool_name, count in sorted(tool_counts.items()):
            summary_lines.append(f"  - {tool_name}: {count} calls")

        return "\n".join(summary_lines)

    def next_round(self) -> None:
        """Increment the round counter."""
        self.current_round += 1

    def reset(self) -> None:
        """Reset the detector for a new conversation turn."""
        self.tool_history.clear()
        self.current_round = 0

    def has_any_loops(self) -> bool:
        """Check if there are any loops in the current history.

        Returns:
            True if any tool has been called multiple times with identical params
        """
        seen_calls: List[ToolCall] = []
        for call in self.tool_history:
            if any(call.matches(seen) for seen in seen_calls):
                return True
            seen_calls.append(call)
        return False
