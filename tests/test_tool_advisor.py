"""Tests for the ToolAdvisor (intelligent tool selection guidance)."""

import pytest
from hrisa_code.core.planning import (
    ToolAdvisor,
    ToolCapability,
    ToolValidationResult,
    ParameterSuggestion,
    ValidationStatus,
)
from hrisa_code.tools.file_operations import AVAILABLE_TOOLS


class TestToolAdvisorInitialization:
    """Tests for ToolAdvisor initialization."""

    def test_initialization(self):
        """Test basic initialization."""
        advisor = ToolAdvisor(available_tools=AVAILABLE_TOOLS)
        assert advisor.available_tools == AVAILABLE_TOOLS
        assert advisor.tool_capabilities is not None
        assert advisor.parameter_validators is not None

    def test_capability_database_built(self):
        """Test that capability database is populated."""
        advisor = ToolAdvisor(available_tools=AVAILABLE_TOOLS)
        assert len(advisor.tool_capabilities) > 0
        assert "read_file" in advisor.tool_capabilities
        assert "write_file" in advisor.tool_capabilities
        assert "execute_command" in advisor.tool_capabilities

    def test_parameter_validators_built(self):
        """Test that parameter validators are populated."""
        advisor = ToolAdvisor(available_tools=AVAILABLE_TOOLS)
        assert len(advisor.parameter_validators) > 0
        assert "read_file" in advisor.parameter_validators
        assert "write_file" in advisor.parameter_validators


class TestToolCapability:
    """Tests for ToolCapability information."""

    def test_get_tool_guidance_exists(self):
        """Test retrieving guidance for existing tool."""
        advisor = ToolAdvisor(available_tools=AVAILABLE_TOOLS)
        capability = advisor.get_tool_guidance("read_file")
        assert capability is not None
        assert isinstance(capability, ToolCapability)
        assert capability.tool_name == "read_file"
        assert len(capability.use_cases) > 0
        assert len(capability.limitations) > 0
        assert len(capability.examples) > 0

    def test_get_tool_guidance_nonexistent(self):
        """Test retrieving guidance for non-existent tool."""
        advisor = ToolAdvisor(available_tools=AVAILABLE_TOOLS)
        capability = advisor.get_tool_guidance("nonexistent_tool")
        assert capability is None

    def test_read_file_capability(self):
        """Test read_file capability details."""
        advisor = ToolAdvisor(available_tools=AVAILABLE_TOOLS)
        capability = advisor.get_tool_guidance("read_file")
        assert "Reading source code files" in capability.use_cases
        assert any("Cannot read binary files" in lim for lim in capability.limitations)
        assert len(capability.related_tools) > 0
        assert len(capability.common_mistakes) > 0

    def test_execute_command_capability(self):
        """Test execute_command capability details."""
        advisor = ToolAdvisor(available_tools=AVAILABLE_TOOLS)
        capability = advisor.get_tool_guidance("execute_command")
        assert "Running shell commands" in capability.use_cases
        assert any("background" in ex.lower() for ex in capability.examples)


class TestParameterValidation:
    """Tests for parameter validation logic."""

    def test_validate_unknown_tool(self):
        """Test validation fails for unknown tool."""
        advisor = ToolAdvisor(available_tools=AVAILABLE_TOOLS)
        result = advisor.validate_tool_call("unknown_tool", {})
        assert not result.is_valid
        assert result.status == ValidationStatus.INVALID
        assert "Unknown tool" in result.errors[0]

    def test_validate_read_file_valid(self):
        """Test valid read_file call."""
        advisor = ToolAdvisor(available_tools=AVAILABLE_TOOLS)
        result = advisor.validate_tool_call(
            "read_file",
            {"file_path": "test.py"}
        )
        assert result.is_valid
        assert result.status == ValidationStatus.VALID
        assert len(result.errors) == 0

    def test_validate_read_file_missing_required(self):
        """Test read_file missing required parameter."""
        advisor = ToolAdvisor(available_tools=AVAILABLE_TOOLS)
        result = advisor.validate_tool_call("read_file", {})
        assert not result.is_valid
        assert result.status == ValidationStatus.MISSING_REQUIRED
        assert any("file_path" in error for error in result.errors)
        assert len(result.suggestions) > 0

    def test_validate_write_file_valid(self):
        """Test valid write_file call."""
        advisor = ToolAdvisor(available_tools=AVAILABLE_TOOLS)
        result = advisor.validate_tool_call(
            "write_file",
            {"file_path": "test.py", "content": "print('hello')"}
        )
        assert result.is_valid
        assert result.status == ValidationStatus.VALID

    def test_validate_write_file_missing_content(self):
        """Test write_file missing content parameter."""
        advisor = ToolAdvisor(available_tools=AVAILABLE_TOOLS)
        result = advisor.validate_tool_call(
            "write_file",
            {"file_path": "test.py"}
        )
        assert not result.is_valid
        assert any("content" in error for error in result.errors)


class TestTypeValidation:
    """Tests for type validation."""

    def test_validate_type_string_valid(self):
        """Test string type validation passes."""
        advisor = ToolAdvisor(available_tools=AVAILABLE_TOOLS)
        is_valid, error = advisor._validate_type("test", "string")
        assert is_valid
        assert error == ""

    def test_validate_type_string_invalid(self):
        """Test string type validation fails for integer."""
        advisor = ToolAdvisor(available_tools=AVAILABLE_TOOLS)
        is_valid, error = advisor._validate_type(123, "string")
        assert not is_valid
        assert "expected string" in error

    def test_validate_type_integer_valid(self):
        """Test integer type validation passes."""
        advisor = ToolAdvisor(available_tools=AVAILABLE_TOOLS)
        is_valid, error = advisor._validate_type(10, "integer")
        assert is_valid
        assert error == ""

    def test_validate_type_integer_invalid(self):
        """Test integer type validation fails for string."""
        advisor = ToolAdvisor(available_tools=AVAILABLE_TOOLS)
        is_valid, error = advisor._validate_type("10", "integer")
        assert not is_valid
        assert "expected integer" in error

    def test_validate_type_boolean_valid(self):
        """Test boolean type validation passes."""
        advisor = ToolAdvisor(available_tools=AVAILABLE_TOOLS)
        is_valid, error = advisor._validate_type(True, "boolean")
        assert is_valid
        assert error == ""

    def test_validate_type_boolean_invalid(self):
        """Test boolean type validation fails for string."""
        advisor = ToolAdvisor(available_tools=AVAILABLE_TOOLS)
        is_valid, error = advisor._validate_type("true", "boolean")
        assert not is_valid
        assert "expected boolean" in error


class TestRangeValidation:
    """Tests for integer range validation."""

    def test_validate_start_line_valid(self):
        """Test start_line with valid value."""
        advisor = ToolAdvisor(available_tools=AVAILABLE_TOOLS)
        result = advisor.validate_tool_call(
            "read_file",
            {"file_path": "test.py", "start_line": 10}
        )
        assert result.is_valid

    def test_validate_start_line_too_low(self):
        """Test start_line below minimum."""
        advisor = ToolAdvisor(available_tools=AVAILABLE_TOOLS)
        result = advisor.validate_tool_call(
            "read_file",
            {"file_path": "test.py", "start_line": 0}
        )
        assert not result.is_valid
        assert any("must be >= 1" in error for error in result.errors)

    def test_validate_end_line_valid(self):
        """Test end_line with valid value."""
        advisor = ToolAdvisor(available_tools=AVAILABLE_TOOLS)
        result = advisor.validate_tool_call(
            "read_file",
            {"file_path": "test.py", "end_line": 100}
        )
        assert result.is_valid

    def test_validate_end_line_too_low(self):
        """Test end_line below minimum."""
        advisor = ToolAdvisor(available_tools=AVAILABLE_TOOLS)
        result = advisor.validate_tool_call(
            "read_file",
            {"file_path": "test.py", "end_line": 0}
        )
        assert not result.is_valid
        assert any("must be >= 1" in error for error in result.errors)


class TestToolSuggestions:
    """Tests for tool suggestion system."""

    def test_suggest_tool_for_read_task(self):
        """Test tool suggestion for reading tasks."""
        advisor = ToolAdvisor(available_tools=AVAILABLE_TOOLS)
        suggestions = advisor.suggest_tool_for_task("read the config file")
        assert "read_file" in suggestions

    def test_suggest_tool_for_write_task(self):
        """Test tool suggestion for writing tasks."""
        advisor = ToolAdvisor(available_tools=AVAILABLE_TOOLS)
        suggestions = advisor.suggest_tool_for_task("create a new file")
        assert "write_file" in suggestions

    def test_suggest_tool_for_search_task(self):
        """Test tool suggestion for search tasks."""
        advisor = ToolAdvisor(available_tools=AVAILABLE_TOOLS)
        suggestions = advisor.suggest_tool_for_task("find all Python files")
        assert "search_files" in suggestions

    def test_suggest_tool_for_execute_task(self):
        """Test tool suggestion for execution tasks."""
        advisor = ToolAdvisor(available_tools=AVAILABLE_TOOLS)
        suggestions = advisor.suggest_tool_for_task("run the tests")
        assert "execute_command" in suggestions

    def test_suggest_tool_for_git_status(self):
        """Test tool suggestion for git status."""
        advisor = ToolAdvisor(available_tools=AVAILABLE_TOOLS)
        suggestions = advisor.suggest_tool_for_task("show git status")
        assert "git_status" in suggestions

    def test_suggest_tool_for_git_diff(self):
        """Test tool suggestion for git diff."""
        advisor = ToolAdvisor(available_tools=AVAILABLE_TOOLS)
        suggestions = advisor.suggest_tool_for_task("show git changes")
        assert "git_diff" in suggestions

    def test_suggest_tool_no_match(self):
        """Test tool suggestion with no matches."""
        advisor = ToolAdvisor(available_tools=AVAILABLE_TOOLS)
        suggestions = advisor.suggest_tool_for_task("do something random")
        # Should return empty list for unmatched tasks
        assert isinstance(suggestions, list)


class TestValidationErrorMessages:
    """Tests for validation error message formatting."""

    def test_format_validation_error_message_valid(self):
        """Test error message for valid call returns empty."""
        advisor = ToolAdvisor(available_tools=AVAILABLE_TOOLS)
        result = advisor.validate_tool_call(
            "read_file",
            {"file_path": "test.py"}
        )
        message = advisor.format_validation_error_message(result, "read_file")
        assert message == ""

    def test_format_validation_error_message_invalid(self):
        """Test error message for invalid call."""
        advisor = ToolAdvisor(available_tools=AVAILABLE_TOOLS)
        result = advisor.validate_tool_call("read_file", {})
        message = advisor.format_validation_error_message(result, "read_file")
        assert "[TOOL VALIDATION ERROR]" in message
        assert "read_file" in message
        assert "Errors:" in message
        assert "file_path" in message

    def test_format_validation_error_includes_suggestions(self):
        """Test error message includes suggestions."""
        advisor = ToolAdvisor(available_tools=AVAILABLE_TOOLS)
        result = advisor.validate_tool_call("read_file", {})
        message = advisor.format_validation_error_message(result, "read_file")
        assert "Suggestions:" in message
        assert "Example:" in message

    def test_format_validation_error_includes_guidance(self):
        """Test error message includes tool guidance."""
        advisor = ToolAdvisor(available_tools=AVAILABLE_TOOLS)
        result = advisor.validate_tool_call("read_file", {})
        message = advisor.format_validation_error_message(result, "read_file")
        assert "Tool Usage Guide" in message
        assert "Use cases:" in message


class TestParameterSuggestions:
    """Tests for parameter suggestions."""

    def test_suggestion_for_missing_parameter(self):
        """Test suggestion provided for missing parameter."""
        advisor = ToolAdvisor(available_tools=AVAILABLE_TOOLS)
        result = advisor.validate_tool_call("read_file", {})
        assert len(result.suggestions) > 0
        suggestion = result.suggestions[0]
        assert isinstance(suggestion, ParameterSuggestion)
        assert suggestion.parameter_name == "file_path"
        assert "required" in suggestion.reason.lower()
        assert len(suggestion.example) > 0


class TestUnknownParameters:
    """Tests for handling unknown parameters."""

    def test_unknown_parameter_warning(self):
        """Test warning for unknown parameter."""
        advisor = ToolAdvisor(available_tools=AVAILABLE_TOOLS)
        result = advisor.validate_tool_call(
            "read_file",
            {"file_path": "test.py", "unknown_param": "value"}
        )
        # Should still be valid but have warning
        assert result.is_valid
        assert len(result.warnings) > 0
        assert any("unknown_param" in warning.lower() for warning in result.warnings)


class TestToolAdvisorIntegration:
    """Integration tests for ToolAdvisor."""

    def test_complete_validation_flow_valid(self):
        """Test complete validation flow for valid call."""
        advisor = ToolAdvisor(available_tools=AVAILABLE_TOOLS)

        # Validate the call
        result = advisor.validate_tool_call(
            "write_file",
            {"file_path": "test.py", "content": "print('hello')"}
        )

        assert result.is_valid
        assert result.status == ValidationStatus.VALID
        assert len(result.errors) == 0

        # Format message (should be empty)
        message = advisor.format_validation_error_message(result, "write_file")
        assert message == ""

    def test_complete_validation_flow_invalid(self):
        """Test complete validation flow for invalid call."""
        advisor = ToolAdvisor(available_tools=AVAILABLE_TOOLS)

        # Validate the call (missing required parameters)
        result = advisor.validate_tool_call("write_file", {})

        assert not result.is_valid
        assert result.status == ValidationStatus.MISSING_REQUIRED
        assert len(result.errors) > 0
        assert len(result.suggestions) > 0

        # Format message
        message = advisor.format_validation_error_message(result, "write_file")
        assert "[TOOL VALIDATION ERROR]" in message
        assert "file_path" in message
        assert "content" in message

    def test_suggestion_and_capability_together(self):
        """Test that suggestions work with capability guidance."""
        advisor = ToolAdvisor(available_tools=AVAILABLE_TOOLS)

        # Get suggestions for a task
        suggestions = advisor.suggest_tool_for_task("read a file")
        assert "read_file" in suggestions

        # Get capability for suggested tool
        capability = advisor.get_tool_guidance("read_file")
        assert capability is not None
        assert len(capability.use_cases) > 0

        # Validate with correct parameters
        result = advisor.validate_tool_call(
            "read_file",
            {"file_path": "test.py"}
        )
        assert result.is_valid

    def test_multiple_missing_parameters(self):
        """Test validation with multiple missing parameters."""
        advisor = ToolAdvisor(available_tools=AVAILABLE_TOOLS)
        result = advisor.validate_tool_call("write_file", {})

        # Should report both file_path and content as missing
        assert not result.is_valid
        assert len(result.errors) == 2
        assert any("file_path" in error for error in result.errors)
        assert any("content" in error for error in result.errors)
        assert len(result.suggestions) == 2

    def test_mixed_valid_and_invalid_parameters(self):
        """Test validation with mix of valid and invalid parameters."""
        advisor = ToolAdvisor(available_tools=AVAILABLE_TOOLS)
        result = advisor.validate_tool_call(
            "read_file",
            {"file_path": "test.py", "start_line": -1}  # Valid file_path, invalid start_line
        )

        assert not result.is_valid
        assert any("start_line" in error for error in result.errors)
