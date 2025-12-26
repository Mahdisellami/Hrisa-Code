"""Unit tests for git operation tools."""

import pytest
from pathlib import Path
from unittest.mock import patch, Mock
from src.hrisa_code.tools.git_operations import (
    GitStatusTool,
    GitDiffTool,
    GitLogTool,
    GitBranchTool,
    GitCommitTool,
    GitPushTool,
    GitPullTool,
    GitStashTool,
    get_all_git_tool_definitions,
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
        definitions = get_all_git_tool_definitions()
        assert len(definitions) == 8  # 4 read + 4 write tools

        for definition in definitions:
            assert "type" in definition
            assert definition["type"] == "function"
            assert "function" in definition
            assert "name" in definition["function"]
            assert "description" in definition["function"]
            assert "parameters" in definition["function"]


class TestGitCommitTool:
    """Test suite for git_commit tool."""

    def test_git_commit_definition(self):
        """Test that tool definition is correct."""
        definition = GitCommitTool.get_definition()
        assert definition["type"] == "function"
        assert definition["function"]["name"] == "git_commit"
        assert "IMPORTANT" in definition["function"]["description"]  # Warning about write operation
        assert "message" in definition["function"]["parameters"]["properties"]
        assert "message" in definition["function"]["parameters"]["required"]

    @patch('subprocess.run')
    def test_git_commit_execute_success(self, mock_run):
        """Test successful git commit."""
        mock_run.return_value = Mock(returncode=0, stdout="[main abc123] Test commit\n 1 file changed", stderr="")

        result = GitCommitTool.execute(message="Test commit")
        assert "Test commit" in result
        assert "Error" not in result
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_git_commit_with_add_all(self, mock_run):
        """Test git commit with add_all flag."""
        mock_run.return_value = Mock(returncode=0, stdout="Commit created", stderr="")

        result = GitCommitTool.execute(message="Test commit", add_all=True)
        assert "Error" not in result
        # Should be called twice: once for add, once for commit
        assert mock_run.call_count == 2

    @patch('subprocess.run')
    def test_git_commit_nothing_to_commit(self, mock_run):
        """Test git commit when nothing to commit."""
        mock_run.return_value = Mock(returncode=1, stdout="", stderr="nothing to commit")

        result = GitCommitTool.execute(message="Test commit")
        assert "No changes to commit" in result


class TestGitPushTool:
    """Test suite for git_push tool."""

    def test_git_push_definition(self):
        """Test that tool definition is correct."""
        definition = GitPushTool.get_definition()
        assert definition["type"] == "function"
        assert definition["function"]["name"] == "git_push"
        assert "IMPORTANT" in definition["function"]["description"]  # Warning
        assert "remote" in definition["function"]["parameters"]["properties"]

    @patch('subprocess.run')
    def test_git_push_execute_success(self, mock_run):
        """Test successful git push."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="Everything up-to-date")

        result = GitPushTool.execute()
        assert "Error" not in result
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_git_push_with_branch(self, mock_run):
        """Test git push with specific branch."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="Successfully pushed")

        result = GitPushTool.execute(remote="origin", branch="main")
        assert "Error" not in result
        call_args = mock_run.call_args[0][0]
        assert "main" in call_args

    @patch('subprocess.run')
    def test_git_push_set_upstream(self, mock_run):
        """Test git push with set_upstream flag."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="Branch set to track")

        result = GitPushTool.execute(set_upstream=True, branch="feature")
        assert "Error" not in result
        call_args = mock_run.call_args[0][0]
        assert "-u" in call_args


class TestGitPullTool:
    """Test suite for git_pull tool."""

    def test_git_pull_definition(self):
        """Test that tool definition is correct."""
        definition = GitPullTool.get_definition()
        assert definition["type"] == "function"
        assert definition["function"]["name"] == "git_pull"
        assert "IMPORTANT" in definition["function"]["description"]  # Warning
        assert "rebase" in definition["function"]["parameters"]["properties"]

    @patch('subprocess.run')
    def test_git_pull_execute_success(self, mock_run):
        """Test successful git pull."""
        mock_run.return_value = Mock(returncode=0, stdout="Already up to date.", stderr="")

        result = GitPullTool.execute()
        assert "Error" not in result
        assert "up to date" in result.lower() or "up-to-date" in result.lower()
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_git_pull_with_rebase(self, mock_run):
        """Test git pull with rebase."""
        mock_run.return_value = Mock(returncode=0, stdout="Successfully rebased", stderr="")

        result = GitPullTool.execute(rebase=True)
        assert "Error" not in result
        call_args = mock_run.call_args[0][0]
        assert "--rebase" in call_args

    @patch('subprocess.run')
    def test_git_pull_merge_conflict(self, mock_run):
        """Test git pull with merge conflict."""
        mock_run.return_value = Mock(returncode=1, stdout="", stderr="CONFLICT: merge conflict in file.txt")

        result = GitPullTool.execute()
        assert "conflict" in result.lower()
        assert "Error" in result


class TestGitStashTool:
    """Test suite for git_stash tool."""

    def test_git_stash_definition(self):
        """Test that tool definition is correct."""
        definition = GitStashTool.get_definition()
        assert definition["type"] == "function"
        assert definition["function"]["name"] == "git_stash"
        assert "IMPORTANT" in definition["function"]["description"]  # Warning
        assert "action" in definition["function"]["parameters"]["properties"]

    @patch('subprocess.run')
    def test_git_stash_save(self, mock_run):
        """Test git stash save."""
        mock_run.return_value = Mock(returncode=0, stdout="Saved working directory", stderr="")

        result = GitStashTool.execute(action="save", message="WIP changes")
        assert "Error" not in result
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "git" in call_args
        assert "stash" in call_args

    @patch('subprocess.run')
    def test_git_stash_list(self, mock_run):
        """Test git stash list."""
        mock_run.return_value = Mock(returncode=0, stdout="stash@{0}: WIP on main\nstash@{1}: WIP on feature", stderr="")

        result = GitStashTool.execute(action="list")
        assert "stash@{0}" in result
        assert "Error" not in result

    @patch('subprocess.run')
    def test_git_stash_pop(self, mock_run):
        """Test git stash pop."""
        mock_run.return_value = Mock(returncode=0, stdout="Dropped refs/stash@{0}", stderr="")

        result = GitStashTool.execute(action="pop", stash_index=0)
        assert "Error" not in result
        call_args = mock_run.call_args[0][0]
        assert "pop" in call_args

    @patch('subprocess.run')
    def test_git_stash_no_changes(self, mock_run):
        """Test git stash with no changes."""
        mock_run.return_value = Mock(returncode=1, stdout="", stderr="No local changes to save")

        result = GitStashTool.execute(action="save")
        assert "No local changes to stash" in result


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
