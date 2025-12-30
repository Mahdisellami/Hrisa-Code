"""Tests for ComplexityDetector (task complexity analysis)."""

import pytest
from hrisa_code.core.planning.complexity_detector import (
    ComplexityDetector,
    TaskComplexity,
    ComplexityAnalysis,
)


class TestComplexityDetectorInitialization:
    """Tests for ComplexityDetector initialization."""

    def test_initialization_basic(self):
        """Test basic initialization."""
        detector = ComplexityDetector()
        assert detector.ollama_client is None
        assert detector.evaluation_model == "qwen2.5-coder:7b"

    def test_initialization_with_client(self):
        """Test initialization with ollama client."""
        mock_client = object()
        detector = ComplexityDetector(
            ollama_client=mock_client,
            evaluation_model="custom-model"
        )
        assert detector.ollama_client is mock_client
        assert detector.evaluation_model == "custom-model"

    def test_detection_rules_built(self):
        """Test that detection rules are initialized."""
        detector = ComplexityDetector()
        assert len(detector.simple_patterns) > 0
        assert len(detector.moderate_patterns) > 0
        assert len(detector.complex_patterns) > 0
        assert len(detector.complexity_indicators) > 0


class TestSimpleTaskDetection:
    """Tests for detecting simple tasks."""

    def test_simple_list_files(self):
        """Test detection of simple list command."""
        detector = ComplexityDetector()
        result = detector.analyze("list all Python files")
        assert result.complexity == TaskComplexity.SIMPLE
        assert result.confidence >= 0.8
        assert result.estimated_steps == 1

    def test_simple_show_status(self):
        """Test detection of git status command."""
        detector = ComplexityDetector()
        result = detector.analyze("show git status")
        assert result.complexity == TaskComplexity.SIMPLE
        assert result.confidence >= 0.8

    def test_simple_read_file(self):
        """Test detection of file read command."""
        detector = ComplexityDetector()
        result = detector.analyze("read the config.py file")
        assert result.complexity == TaskComplexity.SIMPLE
        assert "simple" in result.reasoning.lower()

    def test_simple_check_status(self):
        """Test detection of status check."""
        detector = ComplexityDetector()
        result = detector.analyze("check git diff")
        assert result.complexity == TaskComplexity.SIMPLE

    def test_simple_view_file(self):
        """Test detection of view command."""
        detector = ComplexityDetector()
        result = detector.analyze("view README.md")
        assert result.complexity == TaskComplexity.SIMPLE

    def test_simple_short_task(self):
        """Test that short unclear tasks default to simple."""
        detector = ComplexityDetector()
        result = detector.analyze("help me")
        assert result.complexity == TaskComplexity.SIMPLE
        assert result.confidence < 0.8  # Lower confidence for ambiguous


class TestModerateTaskDetection:
    """Tests for detecting moderate tasks."""

    def test_moderate_add_logging(self):
        """Test detection of add logging task."""
        detector = ComplexityDetector()
        result = detector.analyze("add logging to the API endpoints")
        assert result.complexity == TaskComplexity.MODERATE
        assert result.confidence >= 0.7
        assert result.estimated_steps > 1

    def test_moderate_fix_bug(self):
        """Test detection of bug fix task."""
        detector = ComplexityDetector()
        result = detector.analyze("fix the bug in authentication")
        assert result.complexity == TaskComplexity.MODERATE
        assert "moderate" in result.reasoning.lower()

    def test_moderate_update_config(self):
        """Test detection of config update."""
        detector = ComplexityDetector()
        result = detector.analyze("update the configuration file")
        assert result.complexity == TaskComplexity.MODERATE

    def test_moderate_add_validation(self):
        """Test detection of validation addition."""
        detector = ComplexityDetector()
        result = detector.analyze("add error handling to the parser")
        assert result.complexity == TaskComplexity.MODERATE

    def test_moderate_modify_function(self):
        """Test detection of function modification."""
        detector = ComplexityDetector()
        result = detector.analyze("modify the login function")
        assert result.complexity == TaskComplexity.MODERATE

    def test_moderate_with_exploration(self):
        """Test moderate task with exploration indicator."""
        detector = ComplexityDetector()
        result = detector.analyze("find and fix the memory leak")
        assert result.complexity == TaskComplexity.MODERATE
        assert any("exploration" in ind.lower() for ind in result.indicators)


class TestComplexTaskDetection:
    """Tests for detecting complex tasks."""

    def test_complex_implement_system(self):
        """Test detection of system implementation."""
        detector = ComplexityDetector()
        result = detector.analyze("implement authentication system")
        assert result.complexity == TaskComplexity.COMPLEX
        assert result.confidence >= 0.75
        assert result.estimated_steps >= 5

    def test_complex_refactor_codebase(self):
        """Test detection of refactoring task."""
        detector = ComplexityDetector()
        result = detector.analyze("refactor the entire codebase")
        assert result.complexity == TaskComplexity.COMPLEX
        assert "complex" in result.reasoning.lower()

    def test_complex_build_feature(self):
        """Test detection of feature building."""
        detector = ComplexityDetector()
        result = detector.analyze("build a new API endpoint system")
        assert result.complexity == TaskComplexity.COMPLEX

    def test_complex_comprehensive_task(self):
        """Test detection of comprehensive task."""
        detector = ComplexityDetector()
        result = detector.analyze("add comprehensive error handling")
        assert result.complexity == TaskComplexity.COMPLEX

    def test_complex_migrate_system(self):
        """Test detection of migration task."""
        detector = ComplexityDetector()
        result = detector.analyze("migrate to new database system")
        assert result.complexity == TaskComplexity.COMPLEX

    def test_complex_many_indicators(self):
        """Test complex detection with multiple indicators."""
        detector = ComplexityDetector()
        result = detector.analyze(
            "find all files, design architecture, implement tests, and deploy"
        )
        assert result.complexity == TaskComplexity.COMPLEX
        assert len(result.indicators) >= 3


class TestComplexityIndicators:
    """Tests for complexity indicator detection."""

    def test_multi_file_indicator(self):
        """Test detection of multi-file operations."""
        detector = ComplexityDetector()
        result = detector.analyze("update all files in the project")
        assert any("multi_file" in ind for ind in result.indicators)

    def test_exploration_indicator(self):
        """Test detection of exploration needs."""
        detector = ComplexityDetector()
        result = detector.analyze("search for and analyze the bug")
        assert any("exploration" in ind for ind in result.indicators)

    def test_design_indicator(self):
        """Test detection of design requirements."""
        detector = ComplexityDetector()
        result = detector.analyze("design and implement the architecture")
        assert any("design" in ind for ind in result.indicators)

    def test_testing_indicator(self):
        """Test detection of testing requirements."""
        detector = ComplexityDetector()
        result = detector.analyze("add feature and write tests")
        assert any("testing" in ind for ind in result.indicators)

    def test_dependency_indicator(self):
        """Test detection of task dependencies."""
        detector = ComplexityDetector()
        result = detector.analyze("read files and then process them")
        assert any("dependencies" in ind for ind in result.indicators)

    def test_uncertainty_indicator(self):
        """Test detection of uncertainty."""
        detector = ComplexityDetector()
        result = detector.analyze("how to best implement this feature")
        assert any("uncertainty" in ind for ind in result.indicators)


class TestSuggestedApproach:
    """Tests for suggested approach generation."""

    def test_simple_approach(self):
        """Test suggested approach for simple task."""
        detector = ComplexityDetector()
        result = detector.analyze("list files")
        assert "direct tool execution" in result.suggested_approach.lower()
        assert "single tool call" in result.suggested_approach.lower()

    def test_moderate_approach(self):
        """Test suggested approach for moderate task."""
        detector = ComplexityDetector()
        result = detector.analyze("add logging to API")
        assert "sequential" in result.suggested_approach.lower()
        assert "multi-step" in result.suggested_approach.lower()

    def test_complex_approach(self):
        """Test suggested approach for complex task."""
        detector = ComplexityDetector()
        result = detector.analyze("implement authentication system")
        assert "orchestration" in result.suggested_approach.lower()
        assert "multi-phase" in result.suggested_approach.lower()


class TestEstimatedSteps:
    """Tests for step estimation."""

    def test_simple_task_one_step(self):
        """Test that simple tasks estimate 1 step."""
        detector = ComplexityDetector()
        result = detector.analyze("show status")
        assert result.estimated_steps == 1

    def test_moderate_task_multiple_steps(self):
        """Test that moderate tasks estimate 2+ steps."""
        detector = ComplexityDetector()
        result = detector.analyze("add error handling")
        assert result.estimated_steps >= 2

    def test_complex_task_many_steps(self):
        """Test that complex tasks estimate 5+ steps."""
        detector = ComplexityDetector()
        result = detector.analyze("implement comprehensive system")
        assert result.estimated_steps >= 5

    def test_steps_increase_with_indicators(self):
        """Test that steps increase with complexity indicators."""
        detector = ComplexityDetector()
        simple_result = detector.analyze("add logging")
        complex_result = detector.analyze(
            "find files, design architecture, add logging, write tests"
        )
        assert complex_result.estimated_steps > simple_result.estimated_steps


class TestEdgeCases:
    """Tests for edge cases and ambiguous tasks."""

    def test_empty_task(self):
        """Test handling of empty task."""
        detector = ComplexityDetector()
        result = detector.analyze("")
        assert result.complexity in [TaskComplexity.SIMPLE, TaskComplexity.MODERATE]

    def test_very_long_task(self):
        """Test handling of very long task description."""
        detector = ComplexityDetector()
        long_task = " ".join(["do something"] * 50)
        result = detector.analyze(long_task)
        assert result.complexity in [TaskComplexity.MODERATE, TaskComplexity.COMPLEX]

    def test_mixed_signals(self):
        """Test task with mixed complexity signals."""
        detector = ComplexityDetector()
        result = detector.analyze("list files and implement authentication")
        # Should prioritize complex signal
        assert result.complexity == TaskComplexity.COMPLEX

    def test_ambiguous_task(self):
        """Test ambiguous task defaults to moderate."""
        detector = ComplexityDetector()
        result = detector.analyze("do the thing")
        assert result.confidence < 0.8  # Lower confidence for ambiguous


class TestAnalysisResult:
    """Tests for ComplexityAnalysis result structure."""

    def test_result_has_all_fields(self):
        """Test that result has all required fields."""
        detector = ComplexityDetector()
        result = detector.analyze("implement feature")
        assert hasattr(result, 'complexity')
        assert hasattr(result, 'confidence')
        assert hasattr(result, 'reasoning')
        assert hasattr(result, 'indicators')
        assert hasattr(result, 'suggested_approach')
        assert hasattr(result, 'estimated_steps')

    def test_confidence_in_valid_range(self):
        """Test that confidence is between 0 and 1."""
        detector = ComplexityDetector()
        result = detector.analyze("test task")
        assert 0.0 <= result.confidence <= 1.0

    def test_reasoning_not_empty(self):
        """Test that reasoning is provided."""
        detector = ComplexityDetector()
        result = detector.analyze("test task")
        assert len(result.reasoning) > 0

    def test_indicators_is_list(self):
        """Test that indicators is a list."""
        detector = ComplexityDetector()
        result = detector.analyze("test task")
        assert isinstance(result.indicators, list)

    def test_estimated_steps_positive(self):
        """Test that estimated steps is positive."""
        detector = ComplexityDetector()
        result = detector.analyze("test task")
        assert result.estimated_steps > 0


class TestRealWorldScenarios:
    """Tests for real-world task scenarios."""

    def test_scenario_file_search(self):
        """Test: User wants to search files."""
        detector = ComplexityDetector()
        result = detector.analyze("find all Python files in the project")
        # "find" triggers exploration indicator, so this becomes moderate
        assert result.complexity in [TaskComplexity.SIMPLE, TaskComplexity.MODERATE]

    def test_scenario_bug_fix(self):
        """Test: User wants to fix a bug."""
        detector = ComplexityDetector()
        result = detector.analyze("fix the memory leak in the parser")
        assert result.complexity == TaskComplexity.MODERATE

    def test_scenario_feature_implementation(self):
        """Test: User wants to implement new feature."""
        detector = ComplexityDetector()
        result = detector.analyze("implement user authentication with JWT")
        assert result.complexity == TaskComplexity.COMPLEX

    def test_scenario_code_review(self):
        """Test: User wants code review."""
        detector = ComplexityDetector()
        result = detector.analyze("review the code in main.py")
        assert result.complexity == TaskComplexity.SIMPLE

    def test_scenario_refactoring(self):
        """Test: User wants to refactor code."""
        detector = ComplexityDetector()
        result = detector.analyze("refactor the authentication module")
        assert result.complexity == TaskComplexity.COMPLEX

    def test_scenario_config_update(self):
        """Test: User wants to update config."""
        detector = ComplexityDetector()
        result = detector.analyze("update the database configuration")
        assert result.complexity == TaskComplexity.MODERATE

    def test_scenario_documentation(self):
        """Test: User wants to read documentation."""
        detector = ComplexityDetector()
        result = detector.analyze("show me the API documentation")
        assert result.complexity == TaskComplexity.SIMPLE

    def test_scenario_comprehensive_feature(self):
        """Test: User wants comprehensive feature."""
        detector = ComplexityDetector()
        result = detector.analyze(
            "add comprehensive logging with configuration, "
            "multiple log levels, and file rotation"
        )
        assert result.complexity == TaskComplexity.COMPLEX
        assert result.estimated_steps >= 5


class TestPatternMatching:
    """Tests for pattern matching logic."""

    def test_check_patterns_method(self):
        """Test _check_patterns method."""
        detector = ComplexityDetector()
        task = "list and show files"
        patterns = ["list", "show", "read"]
        score = detector._check_patterns(task, patterns)
        assert score == 2  # Matches "list" and "show"

    def test_check_patterns_no_match(self):
        """Test _check_patterns with no matches."""
        detector = ComplexityDetector()
        task = "something random"
        patterns = ["list", "show", "read"]
        score = detector._check_patterns(task, patterns)
        assert score == 0

    def test_check_complexity_indicators_method(self):
        """Test _check_complexity_indicators method."""
        detector = ComplexityDetector()
        task = "find and design the solution"
        indicators = detector._check_complexity_indicators(task)
        assert "exploration" in indicators or "design" in indicators
        assert all(v >= 0 for v in indicators.values())


class TestIntegration:
    """Integration tests for ComplexityDetector."""

    def test_analyze_returns_valid_result(self):
        """Test that analyze always returns valid result."""
        detector = ComplexityDetector()
        tasks = [
            "list files",
            "add logging to API",
            "implement authentication system",
            "do something",
            "",
        ]
        for task in tasks:
            result = detector.analyze(task)
            assert isinstance(result, ComplexityAnalysis)
            assert isinstance(result.complexity, TaskComplexity)
            assert 0.0 <= result.confidence <= 1.0
            assert result.estimated_steps > 0

    def test_complexity_ordering(self):
        """Test that complexity increases appropriately."""
        detector = ComplexityDetector()
        simple = detector.analyze("list files")
        moderate = detector.analyze("add logging to files")
        complex_task = detector.analyze("implement comprehensive logging system")

        # Verify ordering
        assert simple.complexity == TaskComplexity.SIMPLE
        assert moderate.complexity == TaskComplexity.MODERATE
        assert complex_task.complexity == TaskComplexity.COMPLEX

        # Verify step estimates increase
        assert simple.estimated_steps < moderate.estimated_steps
        assert moderate.estimated_steps < complex_task.estimated_steps
