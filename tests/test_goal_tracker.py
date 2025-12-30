"""Unit tests for goal tracking system."""

import pytest
from unittest.mock import Mock, AsyncMock
from hrisa_code.core.planning import GoalTracker, GoalStatus, ToolResult


class TestToolResult:
    """Test suite for ToolResult dataclass."""

    def test_tool_result_creation(self):
        """Test creating a ToolResult."""
        result = ToolResult(
            tool_name="git_status",
            arguments={"directory": "."},
            result="On branch main",
            round_number=1,
            had_error=False
        )
        assert result.tool_name == "git_status"
        assert result.arguments == {"directory": "."}
        assert result.result == "On branch main"
        assert result.round_number == 1
        assert not result.had_error

    def test_tool_result_with_error(self):
        """Test ToolResult with error flag."""
        result = ToolResult(
            tool_name="read_file",
            arguments={"file_path": "missing.txt"},
            result="Error: File not found",
            round_number=2,
            had_error=True
        )
        assert result.had_error
        assert "Error" in result.result


class TestGoalTracker:
    """Test suite for GoalTracker."""

    def test_initialization(self):
        """Test goal tracker initialization."""
        tracker = GoalTracker(check_frequency=3)
        assert tracker.check_frequency == 3
        assert tracker.user_question is None
        assert len(tracker.tool_results) == 0
        assert tracker.current_round == 0
        assert tracker.current_status == GoalStatus.UNKNOWN

    def test_set_user_question(self):
        """Test setting user question."""
        tracker = GoalTracker()
        tracker.set_user_question("What's the current git status?")
        assert tracker.user_question == "What's the current git status?"

    def test_add_tool_result(self):
        """Test adding a tool result."""
        tracker = GoalTracker()
        tracker.add_tool_result(
            tool_name="git_status",
            arguments={"directory": "."},
            result="On branch main",
            had_error=False
        )
        assert len(tracker.tool_results) == 1
        assert tracker.tool_results[0].tool_name == "git_status"
        assert not tracker.tool_results[0].had_error

    def test_add_multiple_tool_results(self):
        """Test adding multiple tool results."""
        tracker = GoalTracker()

        for i in range(5):
            tracker.add_tool_result(
                tool_name=f"tool_{i}",
                arguments={},
                result=f"result_{i}",
                had_error=False
            )

        assert len(tracker.tool_results) == 5
        assert tracker.tool_results[0].tool_name == "tool_0"
        assert tracker.tool_results[4].tool_name == "tool_4"

    def test_add_tool_result_with_denied_sets_status_complete(self):
        """Test that [DENIED] result no longer immediately sets status (requires async evaluation)."""
        tracker = GoalTracker()
        tracker.set_user_question("Can you create a git commit?")

        # Add a denied result
        tracker.add_tool_result(
            tool_name="git_commit",
            arguments={"message": "test"},
            result="[DENIED] User denied git commit",
            had_error=False
        )

        # Status is NOT immediately set (requires async evaluation via evaluate_denial_if_needed)
        assert tracker.current_status == GoalStatus.UNKNOWN
        assert len(tracker.tool_results) == 1

    def test_add_tool_result_without_denied_keeps_status_unknown(self):
        """Test that non-denied results don't change status to COMPLETE."""
        tracker = GoalTracker()
        tracker.set_user_question("What is the git status?")

        # Add a successful result
        tracker.add_tool_result(
            tool_name="git_status",
            arguments={"directory": "."},
            result="On branch main\nnothing to commit",
            had_error=False
        )

        # Status should remain UNKNOWN (not automatically COMPLETE)
        assert tracker.current_status == GoalStatus.UNKNOWN
        assert len(tracker.tool_results) == 1

    def test_should_check_progress_first_round(self):
        """Test that first round should check progress."""
        tracker = GoalTracker(check_frequency=3)
        tracker.next_round()
        assert tracker.should_check_progress()

    def test_should_check_progress_frequency(self):
        """Test progress check frequency."""
        tracker = GoalTracker(check_frequency=3)

        # Round 1 - should check
        tracker.next_round()
        assert tracker.should_check_progress()
        tracker.last_check_round = tracker.current_round

        # Round 2 - shouldn't check (only 1 round since last check)
        tracker.next_round()
        assert not tracker.should_check_progress()

        # Round 3 - shouldn't check (only 2 rounds since last check)
        tracker.next_round()
        assert not tracker.should_check_progress()

        # Round 4 - should check (3 rounds since last check)
        tracker.next_round()
        assert tracker.should_check_progress()

    @pytest.mark.asyncio
    async def test_check_progress_no_ollama_client(self):
        """Test check progress without ollama client."""
        tracker = GoalTracker(ollama_client=None)
        tracker.set_user_question("Test question")
        tracker.add_tool_result("git_status", {}, "result", False)

        status = await tracker.check_progress()
        assert status == GoalStatus.IN_PROGRESS

    @pytest.mark.asyncio
    async def test_check_progress_with_mocked_complete(self):
        """Test check progress with mocked LLM returning COMPLETE."""
        mock_client = Mock()
        mock_client.chat_simple = AsyncMock(return_value="COMPLETE")
        mock_client.get_current_model = Mock(return_value="qwen2.5-coder:32b")
        mock_client.switch_model = Mock()

        tracker = GoalTracker(ollama_client=mock_client)
        tracker.set_user_question("What's the git status?")
        tracker.add_tool_result("git_status", {}, "On branch main", False)

        status = await tracker.check_progress()
        assert status == GoalStatus.COMPLETE
        assert mock_client.chat_simple.called

    @pytest.mark.asyncio
    async def test_check_progress_with_mocked_stuck(self):
        """Test check progress with mocked LLM returning STUCK."""
        mock_client = Mock()
        mock_client.chat_simple = AsyncMock(return_value="STUCK")
        mock_client.get_current_model = Mock(return_value="qwen2.5-coder:32b")
        mock_client.switch_model = Mock()

        tracker = GoalTracker(ollama_client=mock_client)
        tracker.set_user_question("What's the git status?")
        tracker.add_tool_result("git_status", {}, "Error", True)
        tracker.add_tool_result("git_status", {}, "Error", True)
        tracker.add_tool_result("git_status", {}, "Error", True)

        status = await tracker.check_progress()
        assert status == GoalStatus.STUCK

    @pytest.mark.asyncio
    async def test_check_progress_with_mocked_in_progress(self):
        """Test check progress with mocked LLM returning IN_PROGRESS."""
        mock_client = Mock()
        mock_client.chat_simple = AsyncMock(return_value="IN_PROGRESS")
        mock_client.get_current_model = Mock(return_value="qwen2.5-coder:32b")
        mock_client.switch_model = Mock()

        tracker = GoalTracker(ollama_client=mock_client)
        tracker.set_user_question("Complex multi-step task")
        tracker.add_tool_result("search_files", {}, "Found 5 files", False)

        status = await tracker.check_progress()
        assert status == GoalStatus.IN_PROGRESS

    @pytest.mark.asyncio
    async def test_check_progress_with_mocked_clarification(self):
        """Test check progress with mocked LLM returning CLARIFICATION_NEEDED."""
        mock_client = Mock()
        mock_client.chat_simple = AsyncMock(return_value="CLARIFICATION_NEEDED")
        mock_client.get_current_model = Mock(return_value="qwen2.5-coder:32b")
        mock_client.switch_model = Mock()

        tracker = GoalTracker(ollama_client=mock_client)
        tracker.set_user_question("Unclear request")
        tracker.add_tool_result("list_directory", {}, "Many files", False)

        status = await tracker.check_progress()
        assert status == GoalStatus.CLARIFICATION_NEEDED

    def test_summarize_tool_results_empty(self):
        """Test summarizing with no tool results."""
        tracker = GoalTracker()
        summary = tracker._summarize_tool_results()
        assert "No tools executed" in summary

    def test_summarize_tool_results_with_results(self):
        """Test summarizing with tool results."""
        tracker = GoalTracker()
        tracker.add_tool_result("git_status", {}, "On branch main", False)
        tracker.add_tool_result("git_diff", {}, "No changes", False)

        summary = tracker._summarize_tool_results()
        assert "git_status" in summary
        assert "git_diff" in summary
        assert "OK" in summary

    def test_summarize_tool_results_truncates_long_results(self):
        """Test that long results are truncated."""
        tracker = GoalTracker()
        long_result = "x" * 300  # 300 chars
        tracker.add_tool_result("read_file", {}, long_result, False)

        summary = tracker._summarize_tool_results()
        assert "..." in summary  # Should be truncated

    def test_summarize_tool_results_limits_to_last_five(self):
        """Test that summary only includes last 5 results."""
        tracker = GoalTracker()
        for i in range(10):
            tracker.add_tool_result(f"tool_{i}", {}, f"result_{i}", False)

        summary = tracker._summarize_tool_results()
        # Should only have tools 5-9
        assert "tool_5" in summary
        assert "tool_9" in summary
        assert "tool_0" not in summary
        assert "tool_4" not in summary

    def test_build_evaluation_prompt(self):
        """Test building evaluation prompt."""
        tracker = GoalTracker()
        tracker.set_user_question("What's the git status?")
        tracker.add_tool_result("git_status", {}, "On branch main", False)
        tracker.current_round = 2

        prompt = tracker._build_evaluation_prompt("Tool summary here")
        assert "What's the git status?" in prompt
        assert "Tool summary here" in prompt
        assert "Total rounds: 2" in prompt
        assert "COMPLETE" in prompt
        assert "IN_PROGRESS" in prompt
        assert "STUCK" in prompt

    def test_parse_evaluation_response_complete(self):
        """Test parsing COMPLETE response."""
        tracker = GoalTracker()
        assert tracker._parse_evaluation_response("COMPLETE") == GoalStatus.COMPLETE
        assert tracker._parse_evaluation_response("complete") == GoalStatus.COMPLETE
        assert tracker._parse_evaluation_response("The task is COMPLETE") == GoalStatus.COMPLETE

    def test_parse_evaluation_response_stuck(self):
        """Test parsing STUCK response."""
        tracker = GoalTracker()
        assert tracker._parse_evaluation_response("STUCK") == GoalStatus.STUCK
        assert tracker._parse_evaluation_response("stuck") == GoalStatus.STUCK

    def test_parse_evaluation_response_in_progress(self):
        """Test parsing IN_PROGRESS response."""
        tracker = GoalTracker()
        assert tracker._parse_evaluation_response("IN_PROGRESS") == GoalStatus.IN_PROGRESS
        assert tracker._parse_evaluation_response("in progress") == GoalStatus.IN_PROGRESS

    def test_parse_evaluation_response_clarification(self):
        """Test parsing CLARIFICATION_NEEDED response."""
        tracker = GoalTracker()
        result = tracker._parse_evaluation_response("CLARIFICATION_NEEDED")
        assert result == GoalStatus.CLARIFICATION_NEEDED

        result = tracker._parse_evaluation_response("CLARIFICATION needed")
        assert result == GoalStatus.CLARIFICATION_NEEDED

    def test_parse_evaluation_response_default(self):
        """Test parsing unknown response defaults to IN_PROGRESS."""
        tracker = GoalTracker()
        assert tracker._parse_evaluation_response("UNKNOWN") == GoalStatus.IN_PROGRESS
        assert tracker._parse_evaluation_response("???") == GoalStatus.IN_PROGRESS
        assert tracker._parse_evaluation_response("") == GoalStatus.IN_PROGRESS

    def test_get_intervention_message_complete(self):
        """Test intervention message for COMPLETE status."""
        tracker = GoalTracker()
        tracker.set_user_question("What's the git status?")
        tracker.add_tool_result("git_status", {}, "On branch main", False)

        msg = tracker.get_intervention_message(GoalStatus.COMPLETE)
        assert "GOAL TRACKER" in msg
        assert "enough information" in msg
        assert "What's the git status?" in msg
        assert "1" in msg  # 1 tool result

    def test_get_intervention_message_stuck(self):
        """Test intervention message for STUCK status."""
        tracker = GoalTracker()
        tracker.set_user_question("Complex task")
        tracker.current_round = 5

        msg = tracker.get_intervention_message(GoalStatus.STUCK)
        assert "GOAL TRACKER" in msg
        assert "stuck" in msg
        assert "5 rounds" in msg
        assert "different approach" in msg

    def test_get_intervention_message_clarification(self):
        """Test intervention message for CLARIFICATION_NEEDED status."""
        tracker = GoalTracker()
        tracker.set_user_question("Vague request")

        msg = tracker.get_intervention_message(GoalStatus.CLARIFICATION_NEEDED)
        assert "GOAL TRACKER" in msg
        assert "unclear" in msg
        assert "clarification" in msg

    def test_get_intervention_message_in_progress(self):
        """Test intervention message for IN_PROGRESS returns empty."""
        tracker = GoalTracker()
        msg = tracker.get_intervention_message(GoalStatus.IN_PROGRESS)
        assert msg == ""

    def test_get_summary(self):
        """Test getting tracker summary."""
        tracker = GoalTracker()
        tracker.set_user_question("Test question")
        tracker.add_tool_result("tool1", {}, "result1", False)
        tracker.add_tool_result("tool2", {}, "Error", True)
        tracker.current_round = 3
        tracker.current_status = GoalStatus.IN_PROGRESS

        summary = tracker.get_summary()
        assert "Test question" in summary
        assert "in_progress" in summary  # Enum value is lowercase
        assert "Rounds: 3" in summary
        assert "Tool calls: 2" in summary
        assert "Errors: 1" in summary

    def test_get_summary_no_goal(self):
        """Test summary with no active goal."""
        tracker = GoalTracker()
        summary = tracker.get_summary()
        assert "No active goal" in summary

    def test_next_round(self):
        """Test incrementing round counter."""
        tracker = GoalTracker()
        assert tracker.current_round == 0

        tracker.next_round()
        assert tracker.current_round == 1

        tracker.next_round()
        assert tracker.current_round == 2

    def test_reset(self):
        """Test resetting tracker."""
        tracker = GoalTracker()
        tracker.set_user_question("Question")
        tracker.add_tool_result("tool", {}, "result", False)
        tracker.next_round()
        tracker.current_status = GoalStatus.COMPLETE

        assert tracker.user_question is not None
        assert len(tracker.tool_results) > 0
        assert tracker.current_round > 0

        tracker.reset()

        assert tracker.user_question is None
        assert len(tracker.tool_results) == 0
        assert tracker.current_round == 0
        assert tracker.last_check_round == 0
        assert tracker.current_status == GoalStatus.UNKNOWN

    def test_has_sufficient_info_not_enough_results(self):
        """Test has_sufficient_info with too few results."""
        tracker = GoalTracker()
        tracker.add_tool_result("tool1", {}, "result1", False)
        assert not tracker.has_sufficient_info()

        tracker.add_tool_result("tool2", {}, "result2", False)
        assert not tracker.has_sufficient_info()

    def test_has_sufficient_info_enough_results(self):
        """Test has_sufficient_info with enough successful results."""
        tracker = GoalTracker()
        for i in range(3):
            tracker.add_tool_result(f"tool{i}", {}, f"result{i}", False)

        assert tracker.has_sufficient_info()

    def test_has_sufficient_info_with_recent_errors(self):
        """Test has_sufficient_info returns false if recent errors."""
        tracker = GoalTracker()
        tracker.add_tool_result("tool1", {}, "result1", False)
        tracker.add_tool_result("tool2", {}, "result2", False)
        tracker.add_tool_result("tool3", {}, "Error", True)  # Recent error

        assert not tracker.has_sufficient_info()

    def test_is_making_progress_early_stages(self):
        """Test is_making_progress in early stages."""
        tracker = GoalTracker()
        tracker.add_tool_result("tool1", {}, "result1", False)
        assert tracker.is_making_progress()

        tracker.add_tool_result("tool2", {}, "result2", False)
        assert tracker.is_making_progress()

    def test_is_making_progress_with_diverse_tools(self):
        """Test is_making_progress with diverse tool usage."""
        tracker = GoalTracker()
        tracker.add_tool_result("git_status", {}, "result1", False)
        tracker.add_tool_result("git_diff", {}, "result2", False)
        tracker.add_tool_result("git_log", {}, "result3", False)
        tracker.add_tool_result("git_branch", {}, "result4", False)

        assert tracker.is_making_progress()

    def test_is_making_progress_stuck_on_same_tool(self):
        """Test is_making_progress returns false when stuck."""
        tracker = GoalTracker()
        # Use same tool repeatedly (only 1 unique tool in last 4)
        for i in range(6):
            tracker.add_tool_result("git_status", {}, f"result{i}", False)

        assert not tracker.is_making_progress()


class TestGoalTrackerIntegration:
    """Integration tests simulating real scenarios."""

    @pytest.mark.asyncio
    async def test_scenario_simple_question_answered(self):
        """Simulate a simple question that gets answered quickly."""
        mock_client = Mock()
        mock_client.chat_simple = AsyncMock(return_value="COMPLETE")
        mock_client.get_current_model = Mock(return_value="qwen2.5-coder:32b")
        mock_client.switch_model = Mock()

        tracker = GoalTracker(ollama_client=mock_client, check_frequency=3)
        tracker.set_user_question("What's the current git status?")

        # Round 1: Check git status
        tracker.next_round()
        tracker.add_tool_result("git_status", {}, "On branch main\nnothing to commit", False)

        # Should check after round 1
        assert tracker.should_check_progress()
        status = await tracker.check_progress()
        assert status == GoalStatus.COMPLETE

    @pytest.mark.asyncio
    async def test_scenario_complex_multi_step_task(self):
        """Simulate a complex task with multiple tools."""
        mock_client = Mock()
        # First check: IN_PROGRESS, Second check: COMPLETE
        mock_client.chat_simple = AsyncMock(side_effect=["IN_PROGRESS", "IN_PROGRESS", "COMPLETE"])
        mock_client.get_current_model = Mock(return_value="qwen2.5-coder:32b")
        mock_client.switch_model = Mock()

        tracker = GoalTracker(ollama_client=mock_client, check_frequency=3)
        tracker.set_user_question("Analyze the codebase structure")

        # Rounds 1-3: Exploration
        for i in range(1, 4):
            tracker.next_round()
            tracker.add_tool_result(f"search_files", {"pattern": f"pattern{i}"}, f"Found files {i}", False)

        # Check after round 1
        status = await tracker.check_progress()
        assert status == GoalStatus.IN_PROGRESS

        # Rounds 4-6: More exploration
        for i in range(4, 7):
            tracker.next_round()
            tracker.add_tool_result("read_file", {"file_path": f"file{i}.py"}, f"Content {i}", False)

        # Check after round 4
        status = await tracker.check_progress()
        assert status == GoalStatus.IN_PROGRESS

        # Rounds 7-9: Final analysis
        for i in range(7, 10):
            tracker.next_round()
            tracker.add_tool_result("list_directory", {}, f"Directory {i}", False)

        # Check after round 7
        status = await tracker.check_progress()
        assert status == GoalStatus.COMPLETE

    def test_scenario_stuck_detection_heuristic(self):
        """Test heuristic detection of being stuck."""
        tracker = GoalTracker()
        tracker.set_user_question("Find something")

        # Add 6 calls to same tool (stuck)
        for i in range(6):
            tracker.add_tool_result("search_files", {"pattern": "x"}, "No results", False)

        assert not tracker.is_making_progress()

    def test_scenario_diverse_exploration(self):
        """Test that diverse tool usage is considered progress."""
        tracker = GoalTracker()
        tracker.set_user_question("Understand the project")

        tools = ["search_files", "read_file", "list_directory", "git_log"]
        for i, tool in enumerate(tools):
            tracker.add_tool_result(tool, {}, f"result{i}", False)

        assert tracker.is_making_progress()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
