"""Unit tests for git operation tools."""

import pytest
from pathlib import Path
from src.hrisa_code.tools.git_operations import (
    GitStatusTool,
    GitDiffTool,
    GitLogTool,
    GitBranchTool,
)


class TestGitStatusTool:
    """Test suite for git_status tool."""

    def test_git_status_definition(self):
        """Test that tool definition is correct."""
        definition = GitStatusTool.get_definition()
        assert definition["type"] == "function"
        assert definition["function"]["name"] == "git_status"
        assert "description" in definition["function"]
        assert "parameters" in definition["function"]

    def test_git_status_execute(self):
        """Test git status execution."""
        result = GitStatusTool.execute()
        assert isinstance(result, str)
        assert "Error" not in result or "fatal" not in result.lower()
        # Should contain branch information
        assert "branch" in result.lower() or "on branch" in result.lower()

    def test_git_status_short_format(self):
        """Test git status with short format."""
        result = GitStatusTool.execute(short=True)
        assert isinstance(result, str)


class TestGitDiffTool:
    """Test suite for git_diff tool."""

    def test_git_diff_definition(self):
        """Test that tool definition is correct."""
        definition = GitDiffTool.get_definition()
        assert definition["type"] == "function"
        assert definition["function"]["name"] == "git_diff"
        assert "cached" in definition["function"]["parameters"]["properties"]
        assert "file_path" in definition["function"]["parameters"]["properties"]

    def test_git_diff_execute(self):
        """Test git diff execution."""
        result = GitDiffTool.execute()
        assert isinstance(result, str)
        # Result can be empty if no changes, or contain diff
        assert "Error" not in result or "fatal" not in result.lower()

    def test_git_diff_name_only(self):
        """Test git diff with name_only flag."""
        result = GitDiffTool.execute(name_only=True)
        assert isinstance(result, str)


class TestGitLogTool:
    """Test suite for git_log tool."""

    def test_git_log_definition(self):
        """Test that tool definition is correct."""
        definition = GitLogTool.get_definition()
        assert definition["type"] == "function"
        assert definition["function"]["name"] == "git_log"
        assert "max_count" in definition["function"]["parameters"]["properties"]
        assert "oneline" in definition["function"]["parameters"]["properties"]

    def test_git_log_execute(self):
        """Test git log execution."""
        result = GitLogTool.execute(max_count=5)
        assert isinstance(result, str)
        # Should contain commit information
        assert len(result) > 0
        assert "Error" not in result or "fatal" not in result.lower()

    def test_git_log_oneline(self):
        """Test git log with oneline format."""
        result = GitLogTool.execute(max_count=3, oneline=True)
        assert isinstance(result, str)
        # Oneline format should be more compact
        lines = result.split("\n")
        assert len(lines) <= 3  # Should have at most 3 lines

    def test_git_log_max_count(self):
        """Test git log respects max_count."""
        result = GitLogTool.execute(max_count=2, oneline=True)
        assert isinstance(result, str)
        lines = [line for line in result.split("\n") if line.strip()]
        assert len(lines) <= 2


class TestGitBranchTool:
    """Test suite for git_branch tool."""

    def test_git_branch_definition(self):
        """Test that tool definition is correct."""
        definition = GitBranchTool.get_definition()
        assert definition["type"] == "function"
        assert definition["function"]["name"] == "git_branch"
        assert "list_all" in definition["function"]["parameters"]["properties"]
        assert "verbose" in definition["function"]["parameters"]["properties"]

    def test_git_branch_execute(self):
        """Test git branch execution."""
        result = GitBranchTool.execute()
        assert isinstance(result, str)
        assert len(result) > 0
        # Should show current branch (marked with *)
        assert "*" in result

    def test_git_branch_verbose(self):
        """Test git branch with verbose output."""
        result = GitBranchTool.execute(verbose=True)
        assert isinstance(result, str)
        # Verbose output should include commit hashes
        assert len(result) > 0


class TestGitToolsIntegration:
    """Integration tests for git tools."""

    def test_all_tools_registered(self):
        """Test that all git tools are properly registered."""
        from src.hrisa_code.tools.file_operations import AVAILABLE_TOOLS

        assert "git_status" in AVAILABLE_TOOLS
        assert "git_diff" in AVAILABLE_TOOLS
        assert "git_log" in AVAILABLE_TOOLS
        assert "git_branch" in AVAILABLE_TOOLS

    def test_tool_definitions_format(self):
        """Test that all tool definitions follow correct format."""
        from src.hrisa_code.tools.git_operations import get_all_git_tool_definitions

        definitions = get_all_git_tool_definitions()
        assert len(definitions) == 4

        for definition in definitions:
            assert "type" in definition
            assert definition["type"] == "function"
            assert "function" in definition
            assert "name" in definition["function"]
            assert "description" in definition["function"]
            assert "parameters" in definition["function"]


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
