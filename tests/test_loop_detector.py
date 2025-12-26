"""Unit tests for loop detection system."""

import pytest
from src.hrisa_code.core.loop_detector import LoopDetector, LoopStatus, ToolCall


class TestToolCall:
    """Test suite for ToolCall dataclass."""

    def test_tool_call_creation(self):
        """Test creating a ToolCall."""
        call = ToolCall(
            tool_name="git_status",
            arguments={"directory": "."},
            round_number=1
        )
        assert call.tool_name == "git_status"
        assert call.arguments == {"directory": "."}
        assert call.round_number == 1

    def test_tool_call_matches_identical(self):
        """Test that identical calls match."""
        call1 = ToolCall("git_status", {"directory": "."}, 1)
        call2 = ToolCall("git_status", {"directory": "."}, 2)
        assert call1.matches(call2)

    def test_tool_call_matches_different_tool(self):
        """Test that different tools don't match."""
        call1 = ToolCall("git_status", {"directory": "."}, 1)
        call2 = ToolCall("git_diff", {"directory": "."}, 1)
        assert not call1.matches(call2)

    def test_tool_call_matches_different_args(self):
        """Test that different arguments don't match."""
        call1 = ToolCall("git_status", {"directory": "."}, 1)
        call2 = ToolCall("git_status", {"directory": "src"}, 1)
        assert not call1.matches(call2)

    def test_tool_call_matches_arg_order(self):
        """Test that argument order doesn't matter."""
        call1 = ToolCall("read_file", {"file_path": "test.py", "start_line": 1}, 1)
        call2 = ToolCall("read_file", {"start_line": 1, "file_path": "test.py"}, 1)
        assert call1.matches(call2)


class TestLoopDetector:
    """Test suite for LoopDetector."""

    def test_initialization(self):
        """Test loop detector initialization."""
        detector = LoopDetector(max_identical_calls=3)
        assert detector.max_identical == 3
        assert len(detector.tool_history) == 0
        assert detector.current_round == 0

    def test_add_call(self):
        """Test adding a call to history."""
        detector = LoopDetector()
        detector.add_call("git_status", {"directory": "."})
        assert len(detector.tool_history) == 1
        assert detector.tool_history[0].tool_name == "git_status"

    def test_check_loop_no_history(self):
        """Test loop check with empty history."""
        detector = LoopDetector()
        status = detector.check_loop("git_status", {"directory": "."})
        assert status == LoopStatus.OK

    def test_check_loop_first_call(self):
        """Test that first call is always OK."""
        detector = LoopDetector()
        detector.add_call("git_status", {"directory": "."})
        status = detector.check_loop("git_diff", {"directory": "."})
        assert status == LoopStatus.OK

    def test_check_loop_warning_threshold(self):
        """Test warning threshold (2 identical calls)."""
        detector = LoopDetector(max_identical_calls=3, warning_threshold=2)

        # First call
        detector.add_call("git_status", {"directory": "."})
        status = detector.check_loop("git_status", {"directory": "."})
        assert status == LoopStatus.OK

        # Second call - should still be OK
        detector.add_call("git_status", {"directory": "."})
        status = detector.check_loop("git_status", {"directory": "."})
        assert status == LoopStatus.WARNING  # Third would trigger warning

    def test_check_loop_detection(self):
        """Test loop detection at max threshold."""
        detector = LoopDetector(max_identical_calls=3)

        # Add 3 identical calls
        for _ in range(3):
            detector.add_call("git_status", {"directory": "."})

        # Fourth identical call should be detected as loop
        status = detector.check_loop("git_status", {"directory": "."})
        assert status == LoopStatus.DETECTED

    def test_check_loop_different_tools_ok(self):
        """Test that different tools don't trigger loop."""
        detector = LoopDetector(max_identical_calls=3)

        detector.add_call("git_status", {"directory": "."})
        detector.add_call("git_diff", {"directory": "."})
        detector.add_call("git_log", {"directory": "."})

        status = detector.check_loop("git_branch", {"directory": "."})
        assert status == LoopStatus.OK

    def test_check_loop_different_args_ok(self):
        """Test that same tool with different args doesn't trigger loop."""
        detector = LoopDetector(max_identical_calls=3)

        detector.add_call("git_status", {"directory": "."})
        detector.add_call("git_status", {"directory": "src"})
        detector.add_call("git_status", {"directory": "tests"})

        status = detector.check_loop("git_status", {"directory": "docs"})
        assert status == LoopStatus.OK

    def test_history_window(self):
        """Test that history window limits tracking."""
        detector = LoopDetector(max_identical_calls=3, history_window=5)

        # Add 6 different calls (exceeds window)
        for i in range(6):
            detector.add_call("read_file", {"file_path": f"file{i}.py"})

        # History should only keep last 5
        assert len(detector.tool_history) == 5
        assert detector.tool_history[0].arguments["file_path"] == "file1.py"

    def test_get_loop_details(self):
        """Test getting loop details."""
        detector = LoopDetector()

        detector.add_call("git_status", {"directory": "."})
        detector.next_round()
        detector.add_call("git_status", {"directory": "."})
        detector.next_round()

        details = detector.get_loop_details("git_status", {"directory": "."})

        assert details["tool_name"] == "git_status"
        assert details["count"] == 2
        assert details["first_round"] == 0
        assert len(details["rounds"]) == 2

    def test_get_intervention_message_warning(self):
        """Test intervention message for warning status."""
        detector = LoopDetector()

        detector.add_call("git_status", {"directory": "."})
        detector.add_call("git_status", {"directory": "."})

        msg = detector.get_intervention_message(
            "git_status",
            {"directory": "."},
            LoopStatus.WARNING
        )

        assert "WARNING" in msg
        assert "git_status" in msg
        assert "2 times" in msg

    def test_get_intervention_message_detected(self):
        """Test intervention message for detected loop."""
        detector = LoopDetector()

        for _ in range(3):
            detector.add_call("git_status", {"directory": "."})

        msg = detector.get_intervention_message(
            "git_status",
            {"directory": "."},
            LoopStatus.DETECTED
        )

        assert "INTERVENTION" in msg
        assert "Loop detected" in msg
        assert "3 times" in msg
        assert "DO NOT call this tool again" in msg

    def test_get_summary_empty(self):
        """Test summary with no history."""
        detector = LoopDetector()
        summary = detector.get_summary()
        assert "No tool calls" in summary

    def test_get_summary_with_calls(self):
        """Test summary with multiple calls."""
        detector = LoopDetector()

        detector.add_call("git_status", {"directory": "."})
        detector.add_call("git_status", {"directory": "."})
        detector.add_call("git_diff", {"directory": "."})

        summary = detector.get_summary()
        assert "3 total" in summary
        assert "git_status: 2 calls" in summary
        assert "git_diff: 1 call" in summary

    def test_next_round(self):
        """Test incrementing round counter."""
        detector = LoopDetector()
        assert detector.current_round == 0

        detector.next_round()
        assert detector.current_round == 1

        detector.next_round()
        assert detector.current_round == 2

    def test_reset(self):
        """Test resetting detector."""
        detector = LoopDetector()

        detector.add_call("git_status", {"directory": "."})
        detector.next_round()
        detector.add_call("git_diff", {"directory": "."})

        assert len(detector.tool_history) > 0
        assert detector.current_round > 0

        detector.reset()

        assert len(detector.tool_history) == 0
        assert detector.current_round == 0

    def test_has_any_loops_false(self):
        """Test has_any_loops with unique calls."""
        detector = LoopDetector()

        detector.add_call("git_status", {"directory": "."})
        detector.add_call("git_diff", {"directory": "."})
        detector.add_call("git_log", {"directory": "."})

        assert not detector.has_any_loops()

    def test_has_any_loops_true(self):
        """Test has_any_loops with duplicate calls."""
        detector = LoopDetector()

        detector.add_call("git_status", {"directory": "."})
        detector.add_call("git_diff", {"directory": "."})
        detector.add_call("git_status", {"directory": "."})  # Duplicate

        assert detector.has_any_loops()


class TestLoopDetectorIntegration:
    """Integration tests simulating real scenarios."""

    def test_scenario_qwen_git_status_loop(self):
        """Simulate the qwen2.5-coder:32b git_status loop (9 identical calls)."""
        detector = LoopDetector(max_identical_calls=3)

        # Simulate 9 calls to git_status
        loop_detected_round = None
        for round_num in range(9):
            detector.next_round()

            status = detector.check_loop("git_status", {"directory": ".", "short": False})

            if status == LoopStatus.DETECTED:
                if loop_detected_round is None:
                    loop_detected_round = round_num
                # In real usage, would break/intervene here

            detector.add_call("git_status", {"directory": ".", "short": False})

        # Should have detected loop by round 3 (after 3 identical calls)
        assert loop_detected_round == 3
        assert detector.has_any_loops()

    def test_scenario_productive_exploration(self):
        """Test productive multi-tool exploration (no loops)."""
        detector = LoopDetector(max_identical_calls=3)

        # Simulate productive exploration
        productive_sequence = [
            ("search_files", {"pattern": "def main", "directory": "."}),
            ("read_file", {"file_path": "src/main.py"}),
            ("git_log", {"directory": ".", "max_count": 5}),
            ("git_diff", {"directory": ".", "cached": False}),
            ("read_file", {"file_path": "tests/test_main.py"}),
        ]

        for tool_name, args in productive_sequence:
            detector.next_round()
            status = detector.check_loop(tool_name, args)
            assert status == LoopStatus.OK
            detector.add_call(tool_name, args)

        assert not detector.has_any_loops()

    def test_scenario_retry_with_variation(self):
        """Test that retrying with different parameters is OK."""
        detector = LoopDetector(max_identical_calls=3)

        # Try searching with different patterns (not a loop)
        search_attempts = [
            {"pattern": "class Main", "directory": "."},
            {"pattern": "def main", "directory": "."},
            {"pattern": "import.*main", "directory": "."},
        ]

        for args in search_attempts:
            detector.next_round()
            status = detector.check_loop("search_files", args)
            assert status == LoopStatus.OK
            detector.add_call("search_files", args)

    def test_scenario_warning_then_change(self):
        """Test warning followed by strategy change."""
        detector = LoopDetector(max_identical_calls=3, warning_threshold=2)

        # Two identical calls
        detector.next_round()
        detector.add_call("git_status", {"directory": "."})
        detector.next_round()
        detector.add_call("git_status", {"directory": "."})

        # Third would warn
        detector.next_round()
        status = detector.check_loop("git_status", {"directory": "."})
        assert status == LoopStatus.WARNING

        # Agent changes strategy to different tool
        detector.add_call("git_log", {"directory": ".", "max_count": 5})

        # Should be OK now
        detector.next_round()
        status = detector.check_loop("git_log", {"directory": ".", "max_count": 5})
        assert status == LoopStatus.OK


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
