"""Unit tests for ApprovalManager and approval request helpers.

Tests cover:
- ApprovalRequest creation and validation
- ApprovalManager auto-approve mode
- Session-based approval memory (always/never)
- Diff generation for file changes
- Helper functions for creating approval requests
- Approval decision handling
- Integration with conversation flow
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from hrisa_code.core.approval_manager import (
    ApprovalType,
    ApprovalDecision,
    ApprovalRequest,
    ApprovalManager,
    create_file_write_request,
    create_file_delete_request,
    create_git_commit_request,
    create_git_push_request,
    create_command_request,
)


class TestApprovalType:
    """Test ApprovalType enum."""

    def test_approval_type_values(self):
        """Test that all approval types have correct values."""
        assert ApprovalType.FILE_WRITE.value == "file_write"
        assert ApprovalType.FILE_DELETE.value == "file_delete"
        assert ApprovalType.GIT_COMMIT.value == "git_commit"
        assert ApprovalType.GIT_PUSH.value == "git_push"
        assert ApprovalType.GIT_PULL.value == "git_pull"
        assert ApprovalType.GIT_STASH.value == "git_stash"
        assert ApprovalType.COMMAND_DESTRUCTIVE.value == "command_destructive"


class TestApprovalDecision:
    """Test ApprovalDecision enum."""

    def test_approval_decision_values(self):
        """Test that all decisions have correct values."""
        assert ApprovalDecision.YES.value == "yes"
        assert ApprovalDecision.NO.value == "no"
        assert ApprovalDecision.ALWAYS.value == "always"
        assert ApprovalDecision.NEVER.value == "never"


class TestApprovalRequest:
    """Test ApprovalRequest dataclass."""

    def test_approval_request_creation(self):
        """Test creating approval request."""
        request = ApprovalRequest(
            operation_type=ApprovalType.FILE_WRITE,
            description="Test operation",
            details={"key": "value"},
        )

        assert request.operation_type == ApprovalType.FILE_WRITE
        assert request.description == "Test operation"
        assert request.details == {"key": "value"}
        assert request.file_path is None
        assert request.old_content is None
        assert request.new_content is None
        assert request.command is None

    def test_approval_request_with_optional_fields(self):
        """Test creating approval request with optional fields."""
        request = ApprovalRequest(
            operation_type=ApprovalType.FILE_WRITE,
            description="Write file",
            details={"file": "test.txt"},
            file_path="/path/to/test.txt",
            old_content="old content",
            new_content="new content",
            command="some_command",
        )

        assert request.file_path == "/path/to/test.txt"
        assert request.old_content == "old content"
        assert request.new_content == "new content"
        assert request.command == "some_command"


class TestApprovalManager:
    """Test ApprovalManager class."""

    def test_approval_manager_initialization(self):
        """Test ApprovalManager initialization."""
        manager = ApprovalManager(auto_approve=False)

        assert manager.auto_approve is False
        assert len(manager._always_approve) == 0
        assert len(manager._never_approve) == 0

    def test_approval_manager_auto_approve_mode(self):
        """Test auto-approve mode always returns YES."""
        manager = ApprovalManager(auto_approve=True)

        request = ApprovalRequest(
            operation_type=ApprovalType.FILE_WRITE,
            description="Test",
            details={},
        )

        decision = manager.request_approval(request)
        assert decision == ApprovalDecision.YES

    def test_session_memory_always_approve(self):
        """Test session memory for always approve."""
        manager = ApprovalManager(auto_approve=False)

        # Add to always approve set
        manager._always_approve.add(ApprovalType.FILE_WRITE)

        request = ApprovalRequest(
            operation_type=ApprovalType.FILE_WRITE,
            description="Test",
            details={},
        )

        decision = manager.request_approval(request)
        assert decision == ApprovalDecision.YES

    def test_session_memory_never_approve(self):
        """Test session memory for never approve."""
        manager = ApprovalManager(auto_approve=False)

        # Add to never approve set
        manager._never_approve.add(ApprovalType.FILE_WRITE)

        request = ApprovalRequest(
            operation_type=ApprovalType.FILE_WRITE,
            description="Test",
            details={},
        )

        decision = manager.request_approval(request)
        assert decision == ApprovalDecision.NO

    @patch('builtins.input')
    def test_user_approves_operation(self, mock_input):
        """Test user approving operation."""
        mock_input.return_value = "y"
        manager = ApprovalManager(auto_approve=False)

        request = ApprovalRequest(
            operation_type=ApprovalType.FILE_WRITE,
            description="Test",
            details={},
        )

        decision = manager.request_approval(request)
        assert decision == ApprovalDecision.YES

    @patch('builtins.input')
    def test_user_denies_operation(self, mock_input):
        """Test user denying operation."""
        mock_input.return_value = "n"
        manager = ApprovalManager(auto_approve=False)

        request = ApprovalRequest(
            operation_type=ApprovalType.FILE_WRITE,
            description="Test",
            details={},
        )

        decision = manager.request_approval(request)
        assert decision == ApprovalDecision.NO

    @patch('builtins.input')
    def test_user_always_approve_updates_session_memory(self, mock_input):
        """Test that 'always' choice updates session memory."""
        mock_input.return_value = "a"
        manager = ApprovalManager(auto_approve=False)

        request = ApprovalRequest(
            operation_type=ApprovalType.FILE_WRITE,
            description="Test",
            details={},
        )

        decision = manager.request_approval(request)

        # Should return YES
        assert decision == ApprovalDecision.YES

        # Should add to always approve set
        assert ApprovalType.FILE_WRITE in manager._always_approve

    @patch('builtins.input')
    def test_user_never_approve_updates_session_memory(self, mock_input):
        """Test that 'never' choice updates session memory."""
        mock_input.return_value = "v"
        manager = ApprovalManager(auto_approve=False)

        request = ApprovalRequest(
            operation_type=ApprovalType.FILE_WRITE,
            description="Test",
            details={},
        )

        decision = manager.request_approval(request)

        # Should return NO
        assert decision == ApprovalDecision.NO

        # Should add to never approve set
        assert ApprovalType.FILE_WRITE in manager._never_approve

    def test_is_approved_returns_true_for_yes(self):
        """Test is_approved convenience method for YES."""
        manager = ApprovalManager(auto_approve=True)

        request = ApprovalRequest(
            operation_type=ApprovalType.FILE_WRITE,
            description="Test",
            details={},
        )

        assert manager.is_approved(request) is True

    def test_is_approved_returns_false_for_no(self):
        """Test is_approved convenience method for NO."""
        manager = ApprovalManager(auto_approve=False)
        manager._never_approve.add(ApprovalType.FILE_WRITE)

        request = ApprovalRequest(
            operation_type=ApprovalType.FILE_WRITE,
            description="Test",
            details={},
        )

        assert manager.is_approved(request) is False

    def test_reset_session_memory(self):
        """Test resetting session memory."""
        manager = ApprovalManager(auto_approve=False)

        # Add some approvals
        manager._always_approve.add(ApprovalType.FILE_WRITE)
        manager._never_approve.add(ApprovalType.GIT_COMMIT)

        # Reset
        manager.reset_session_memory()

        assert len(manager._always_approve) == 0
        assert len(manager._never_approve) == 0

    def test_get_session_approvals(self):
        """Test getting session approval state."""
        manager = ApprovalManager(auto_approve=False)

        manager._always_approve.add(ApprovalType.FILE_WRITE)
        manager._never_approve.add(ApprovalType.GIT_PUSH)

        state = manager.get_session_approvals()

        assert "always" in state
        assert "never" in state
        assert "file_write" in state["always"]
        assert "git_push" in state["never"]

    def test_generate_diff_with_changes(self):
        """Test diff generation with actual changes."""
        manager = ApprovalManager(auto_approve=False)

        old_content = "Line 1\nLine 2\nLine 3\n"
        new_content = "Line 1\nLine 2 modified\nLine 3\nLine 4\n"

        diff = manager._generate_diff(old_content, new_content, "test.txt")

        assert "---" in diff
        assert "+++" in diff
        assert "test.txt" in diff
        # Should show the modified line
        assert "Line 2" in diff

    def test_generate_diff_no_changes(self):
        """Test diff generation with no changes."""
        manager = ApprovalManager(auto_approve=False)

        content = "Same content\n"

        diff = manager._generate_diff(content, content, "test.txt")

        assert "No changes detected" in diff

    def test_generate_diff_truncates_large_diffs(self):
        """Test that large diffs are truncated."""
        manager = ApprovalManager(auto_approve=False)

        # Create content with many lines
        old_content = "\n".join([f"Line {i}" for i in range(1, 100)])
        new_content = "\n".join([f"Modified {i}" for i in range(1, 100)])

        diff = manager._generate_diff(old_content, new_content, "test.txt")

        # Should be truncated
        assert "truncated" in diff.lower()


class TestHelperFunctions:
    """Test helper functions for creating approval requests."""

    def test_create_file_write_request_new_file(self):
        """Test creating file write request for new file."""
        request = create_file_write_request(
            file_path="/path/to/new.txt",
            new_content="New content",
        )

        assert request.operation_type == ApprovalType.FILE_WRITE
        assert "Create" in request.description
        assert "new.txt" in request.description
        assert request.details["Action"] == "Create"
        assert request.file_path == "/path/to/new.txt"
        assert request.new_content == "New content"
        assert request.old_content is None

    def test_create_file_write_request_overwrite(self):
        """Test creating file write request for overwrite."""
        request = create_file_write_request(
            file_path="/path/to/existing.txt",
            new_content="New content",
            old_content="Old content",
        )

        assert request.operation_type == ApprovalType.FILE_WRITE
        assert "Overwrite" in request.description
        assert "existing.txt" in request.description
        assert request.details["Action"] == "Overwrite"
        assert request.old_content == "Old content"
        assert request.new_content == "New content"

    def test_create_file_delete_request(self):
        """Test creating file delete request."""
        request = create_file_delete_request("/path/to/delete.txt")

        assert request.operation_type == ApprovalType.FILE_DELETE
        assert "Delete" in request.description
        assert "delete.txt" in request.description
        assert request.details["Action"] == "Delete"
        assert "cannot be undone" in request.details["Warning"]
        assert request.file_path == "/path/to/delete.txt"

    def test_create_git_commit_request(self):
        """Test creating git commit request."""
        files = ["file1.txt", "file2.py", "file3.md"]
        request = create_git_commit_request(
            message="Test commit",
            files=files,
        )

        assert request.operation_type == ApprovalType.GIT_COMMIT
        assert "git commit" in request.description
        assert request.details["Message"] == "Test commit"
        assert request.details["Count"] == "3 file(s)"
        assert "file1.txt" in request.details["Files"]
        assert request.command == 'git commit -m "Test commit"'

    def test_create_git_commit_request_many_files(self):
        """Test creating git commit request with many files."""
        files = [f"file{i}.txt" for i in range(15)]
        request = create_git_commit_request(
            message="Big commit",
            files=files,
        )

        # Should truncate file list
        assert "... and 5 more" in request.details["Files"]
        assert request.details["Count"] == "15 file(s)"

    def test_create_git_push_request(self):
        """Test creating git push request."""
        request = create_git_push_request(
            branch="main",
            remote="origin",
        )

        assert request.operation_type == ApprovalType.GIT_PUSH
        assert "Push commits" in request.description
        assert request.details["Remote"] == "origin"
        assert request.details["Branch"] == "main"
        assert "visible to others" in request.details["Warning"]
        assert request.command == "git push origin main"

    def test_create_git_push_request_default_remote(self):
        """Test creating git push request with default remote."""
        request = create_git_push_request(branch="feature")

        assert request.details["Remote"] == "origin"
        assert request.details["Branch"] == "feature"

    def test_create_command_request(self):
        """Test creating destructive command request."""
        command = "rm -rf dangerous_dir"
        request = create_command_request(command)

        assert request.operation_type == ApprovalType.COMMAND_DESTRUCTIVE
        assert "destructive command" in request.description
        assert request.details["Command"] == command
        assert "modify or delete" in request.details["Warning"]
        assert request.command == command


class TestApprovalManagerIntegration:
    """Test ApprovalManager integration scenarios."""

    @patch('builtins.input')
    def test_multiple_operations_with_session_memory(self, mock_input):
        """Test multiple operations using session memory."""
        # First approval: user chooses 'always'
        mock_input.return_value = "a"

        manager = ApprovalManager(auto_approve=False)

        # First request
        request1 = ApprovalRequest(
            operation_type=ApprovalType.FILE_WRITE,
            description="First write",
            details={},
        )

        decision1 = manager.request_approval(request1)
        assert decision1 == ApprovalDecision.YES

        # Second request of same type - should not prompt
        request2 = ApprovalRequest(
            operation_type=ApprovalType.FILE_WRITE,
            description="Second write",
            details={},
        )

        decision2 = manager.request_approval(request2)
        assert decision2 == ApprovalDecision.YES

        # Should only prompt once
        assert mock_input.call_count == 1

    @patch('builtins.input')
    def test_different_operation_types_independent(self, mock_input):
        """Test that different operation types are tracked independently."""
        manager = ApprovalManager(auto_approve=False)

        # Always approve file writes
        manager._always_approve.add(ApprovalType.FILE_WRITE)

        # Never approve git pushes
        manager._never_approve.add(ApprovalType.GIT_PUSH)

        # File write should be approved
        write_request = ApprovalRequest(
            operation_type=ApprovalType.FILE_WRITE,
            description="Write",
            details={},
        )
        assert manager.request_approval(write_request) == ApprovalDecision.YES

        # Git push should be denied
        push_request = ApprovalRequest(
            operation_type=ApprovalType.GIT_PUSH,
            description="Push",
            details={},
        )
        assert manager.request_approval(push_request) == ApprovalDecision.NO

        # Should not have prompted user
        assert mock_input.call_count == 0

    def test_file_write_with_diff_preview(self, tmp_path):
        """Test file write request includes proper details for diff."""
        old_content = "Original content\n"
        new_content = "Modified content\n"

        request = create_file_write_request(
            file_path=str(tmp_path / "test.txt"),
            new_content=new_content,
            old_content=old_content,
        )

        # Request should have all needed data for diff
        assert request.old_content == old_content
        assert request.new_content == new_content
        assert request.file_path == str(tmp_path / "test.txt")

        # Manager should be able to generate diff
        manager = ApprovalManager(auto_approve=False)
        diff = manager._generate_diff(
            request.old_content,
            request.new_content,
            request.file_path,
        )

        assert "---" in diff
        assert "+++" in diff


# Run with: pytest tests/test_approval_manager.py -v
