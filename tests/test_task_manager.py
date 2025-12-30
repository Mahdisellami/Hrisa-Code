"""Unit tests for TaskManager and BackgroundTask.

Tests cover:
- BackgroundTask creation and lifecycle
- Task status tracking (running, completed, failed)
- Process management (start, kill, cleanup)
- Output capture and retrieval
- TaskManager initialization
- Task creation and storage
- Task listing and retrieval
- Error handling
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
from pathlib import Path
import subprocess
import time
from datetime import datetime

from hrisa_code.core.memory import BackgroundTask, TaskManager


class TestBackgroundTask:
    """Test BackgroundTask class."""

    def test_background_task_creation(self, tmp_path):
        """Test creating a background task."""
        mock_process = Mock(spec=subprocess.Popen)
        mock_process.pid = 12345
        mock_process.poll.return_value = None  # Still running
        log_file = tmp_path / "task.log"

        task = BackgroundTask(
            task_id="task-1",
            command="echo test",
            process=mock_process,
            log_file=log_file,
        )

        assert task.task_id == "task-1"
        assert task.command == "echo test"
        assert task.process == mock_process
        assert task.log_file == log_file
        assert task.started is not None
        assert isinstance(task.started, datetime)
        assert task.exit_code is None

    def test_background_task_pid_property(self, tmp_path):
        """Test pid property."""
        mock_process = Mock(spec=subprocess.Popen)
        mock_process.pid = 99999
        log_file = tmp_path / "task.log"

        task = BackgroundTask(
            task_id="task-1",
            command="echo test",
            process=mock_process,
            log_file=log_file,
        )

        assert task.pid == 99999

    def test_background_task_status_running(self, tmp_path):
        """Test status property for running task."""
        mock_process = Mock(spec=subprocess.Popen)
        mock_process.pid = 12345
        mock_process.poll.return_value = None  # Still running
        log_file = tmp_path / "task.log"

        task = BackgroundTask(
            task_id="task-1",
            command="sleep 10",
            process=mock_process,
            log_file=log_file,
        )

        assert task.status == "running"
        assert task.exit_code is None

    def test_background_task_status_completed(self, tmp_path):
        """Test status property for completed task."""
        mock_process = Mock(spec=subprocess.Popen)
        mock_process.pid = 12345
        mock_process.poll.return_value = 0  # Completed successfully
        log_file = tmp_path / "task.log"

        task = BackgroundTask(
            task_id="task-1",
            command="echo test",
            process=mock_process,
            log_file=log_file,
        )

        assert task.status == "completed"
        assert task.exit_code == 0

    def test_background_task_status_failed(self, tmp_path):
        """Test status property for failed task."""
        mock_process = Mock(spec=subprocess.Popen)
        mock_process.pid = 12345
        mock_process.poll.return_value = 1  # Failed with exit code 1
        log_file = tmp_path / "task.log"

        task = BackgroundTask(
            task_id="task-1",
            command="false",
            process=mock_process,
            log_file=log_file,
        )

        assert task.status == "failed"
        assert task.exit_code == 1

    def test_background_task_status_caches_exit_code(self, tmp_path):
        """Test that status caches exit code after first check."""
        mock_process = Mock(spec=subprocess.Popen)
        mock_process.pid = 12345
        mock_process.poll.side_effect = [0, None]  # First returns 0, then None
        log_file = tmp_path / "task.log"

        task = BackgroundTask(
            task_id="task-1",
            command="echo test",
            process=mock_process,
            log_file=log_file,
        )

        # First call should cache exit code
        assert task.status == "completed"
        assert task.exit_code == 0

        # Second call should use cached exit code, not poll again
        assert task.status == "completed"
        # poll should only be called once since exit_code is cached
        assert mock_process.poll.call_count == 1

    def test_background_task_elapsed_time(self, tmp_path):
        """Test elapsed_time property."""
        mock_process = Mock(spec=subprocess.Popen)
        mock_process.pid = 12345
        log_file = tmp_path / "task.log"

        task = BackgroundTask(
            task_id="task-1",
            command="sleep 1",
            process=mock_process,
            log_file=log_file,
        )

        # Elapsed time should be very small right after creation
        assert task.elapsed_time < 0.5

        # Simulate some time passing
        time.sleep(0.1)
        assert task.elapsed_time >= 0.1

    def test_background_task_get_output_success(self, tmp_path):
        """Test getting output from log file."""
        mock_process = Mock(spec=subprocess.Popen)
        mock_process.pid = 12345
        log_file = tmp_path / "task.log"
        log_file.write_text("Test output\nLine 2\n")

        task = BackgroundTask(
            task_id="task-1",
            command="echo test",
            process=mock_process,
            log_file=log_file,
        )

        output = task.get_output()
        assert output == "Test output\nLine 2\n"

    def test_background_task_get_output_no_file(self, tmp_path):
        """Test getting output when log file doesn't exist."""
        mock_process = Mock(spec=subprocess.Popen)
        mock_process.pid = 12345
        log_file = tmp_path / "nonexistent.log"

        task = BackgroundTask(
            task_id="task-1",
            command="echo test",
            process=mock_process,
            log_file=log_file,
        )

        output = task.get_output()
        assert output == ""

    def test_background_task_kill_success(self, tmp_path):
        """Test successfully killing a task."""
        mock_process = Mock(spec=subprocess.Popen)
        mock_process.pid = 12345
        mock_process.poll.return_value = 0  # Process terminated
        log_file = tmp_path / "task.log"

        task = BackgroundTask(
            task_id="task-1",
            command="sleep 100",
            process=mock_process,
            log_file=log_file,
        )

        result = task.kill()
        assert result is True
        mock_process.terminate.assert_called_once()

    def test_background_task_kill_requires_force(self, tmp_path):
        """Test killing a task that requires SIGKILL."""
        mock_process = Mock(spec=subprocess.Popen)
        mock_process.pid = 12345
        mock_process.poll.return_value = None  # Still running after terminate
        log_file = tmp_path / "task.log"

        task = BackgroundTask(
            task_id="task-1",
            command="sleep 100",
            process=mock_process,
            log_file=log_file,
        )

        result = task.kill()
        assert result is True
        mock_process.terminate.assert_called_once()
        mock_process.kill.assert_called_once()  # Force kill called

    def test_background_task_kill_failure(self, tmp_path):
        """Test kill failure."""
        mock_process = Mock(spec=subprocess.Popen)
        mock_process.pid = 12345
        mock_process.terminate.side_effect = ProcessLookupError("No such process")
        log_file = tmp_path / "task.log"

        task = BackgroundTask(
            task_id="task-1",
            command="sleep 100",
            process=mock_process,
            log_file=log_file,
        )

        result = task.kill()
        assert result is False

    def test_background_task_to_dict(self, tmp_path):
        """Test converting task to dictionary."""
        mock_process = Mock(spec=subprocess.Popen)
        mock_process.pid = 12345
        mock_process.poll.return_value = None  # Still running
        log_file = tmp_path / "task.log"

        task = BackgroundTask(
            task_id="task-1",
            command="echo test",
            process=mock_process,
            log_file=log_file,
        )

        task_dict = task.to_dict()

        assert task_dict["id"] == "task-1"
        assert task_dict["command"] == "echo test"
        assert task_dict["pid"] == 12345
        assert task_dict["status"] == "running"
        assert "started" in task_dict
        assert "elapsed" in task_dict
        assert task_dict["exit_code"] is None
        assert str(log_file) in task_dict["log_file"]


class TestTaskManager:
    """Test TaskManager class."""

    def test_task_manager_initialization(self, tmp_path):
        """Test TaskManager initialization."""
        manager = TaskManager(working_directory=tmp_path)

        assert manager.working_directory == tmp_path
        assert manager.tasks == {}
        assert manager._task_counter == 0
        assert manager.task_dir.exists()
        assert manager.log_dir.exists()

    def test_task_manager_creates_directories(self, tmp_path):
        """Test that TaskManager creates necessary directories."""
        # Use a clean temp directory
        working_dir = tmp_path / "work"
        working_dir.mkdir()

        manager = TaskManager(working_directory=working_dir)

        # Check that ~/.hrisa/tasks and logs directories exist
        assert manager.task_dir.exists()
        assert manager.log_dir.exists()
        assert manager.task_dir.is_dir()
        assert manager.log_dir.is_dir()

    @patch('subprocess.Popen')
    @patch('builtins.open', new_callable=mock_open)
    def test_create_task(self, mock_file, mock_popen, tmp_path):
        """Test creating a background task."""
        # mock_popen is already the mocked Popen class
        mock_process = Mock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        manager = TaskManager(working_directory=tmp_path)
        task = manager.create_task("echo hello")

        assert task.task_id == "task-1"
        assert task.command == "echo hello"
        assert task.pid == 12345
        assert "task-1" in manager.tasks
        assert manager._task_counter == 1

        # Verify subprocess was called correctly
        mock_popen.assert_called_once()
        call_kwargs = mock_popen.call_args[1]
        assert call_kwargs["shell"] is True
        assert call_kwargs["cwd"] == tmp_path

    @patch('subprocess.Popen')
    @patch('builtins.open', new_callable=mock_open)
    def test_create_multiple_tasks(self, mock_file, mock_popen, tmp_path):
        """Test creating multiple tasks increments counter."""
        # mock_popen is already the mocked Popen class
        mock_process = Mock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        manager = TaskManager(working_directory=tmp_path)

        task1 = manager.create_task("command1")
        task2 = manager.create_task("command2")
        task3 = manager.create_task("command3")

        assert task1.task_id == "task-1"
        assert task2.task_id == "task-2"
        assert task3.task_id == "task-3"
        assert len(manager.tasks) == 3
        assert manager._task_counter == 3

    def test_get_task_exists(self, tmp_path):
        """Test getting an existing task."""
        manager = TaskManager(working_directory=tmp_path)

        # Manually add a task
        mock_process = Mock(spec=subprocess.Popen)
        mock_process.pid = 12345
        log_file = manager.log_dir / "task-1.log"
        task = BackgroundTask("task-1", "echo test", mock_process, log_file)
        manager.tasks["task-1"] = task

        retrieved_task = manager.get_task("task-1")
        assert retrieved_task is task
        assert retrieved_task.task_id == "task-1"

    def test_get_task_not_found(self, tmp_path):
        """Test getting a non-existent task."""
        manager = TaskManager(working_directory=tmp_path)

        task = manager.get_task("nonexistent")
        assert task is None

    def test_list_tasks_empty(self, tmp_path):
        """Test listing tasks when none exist."""
        manager = TaskManager(working_directory=tmp_path)

        tasks = manager.list_tasks()
        assert tasks == []

    def test_list_tasks_with_tasks(self, tmp_path):
        """Test listing tasks."""
        manager = TaskManager(working_directory=tmp_path)

        # Add some tasks
        mock_process1 = Mock(spec=subprocess.Popen)
        mock_process1.pid = 111
        task1 = BackgroundTask("task-1", "cmd1", mock_process1, manager.log_dir / "task-1.log")
        manager.tasks["task-1"] = task1

        mock_process2 = Mock(spec=subprocess.Popen)
        mock_process2.pid = 222
        task2 = BackgroundTask("task-2", "cmd2", mock_process2, manager.log_dir / "task-2.log")
        manager.tasks["task-2"] = task2

        tasks = manager.list_tasks()
        assert len(tasks) == 2
        assert task1 in tasks
        assert task2 in tasks

    def test_kill_task_exists(self, tmp_path):
        """Test killing an existing task."""
        manager = TaskManager(working_directory=tmp_path)

        # Add a task
        mock_process = Mock(spec=subprocess.Popen)
        mock_process.pid = 12345
        mock_process.poll.return_value = 0
        task = BackgroundTask("task-1", "sleep 100", mock_process, manager.log_dir / "task-1.log")
        manager.tasks["task-1"] = task

        result = manager.kill_task("task-1")
        assert result is True
        mock_process.terminate.assert_called_once()

    def test_kill_task_not_found(self, tmp_path):
        """Test killing a non-existent task."""
        manager = TaskManager(working_directory=tmp_path)

        result = manager.kill_task("nonexistent")
        assert result is False

    def test_cleanup_completed_no_tasks(self, tmp_path):
        """Test cleanup with no tasks."""
        manager = TaskManager(working_directory=tmp_path)

        count = manager.cleanup_completed()
        assert count == 0
        assert len(manager.tasks) == 0

    def test_cleanup_completed_removes_completed(self, tmp_path):
        """Test cleanup removes completed tasks."""
        manager = TaskManager(working_directory=tmp_path)

        # Add completed task
        mock_process1 = Mock(spec=subprocess.Popen)
        mock_process1.pid = 111
        mock_process1.poll.return_value = 0  # Completed
        task1 = BackgroundTask("task-1", "cmd1", mock_process1, manager.log_dir / "task-1.log")
        manager.tasks["task-1"] = task1

        # Add failed task
        mock_process2 = Mock(spec=subprocess.Popen)
        mock_process2.pid = 222
        mock_process2.poll.return_value = 1  # Failed
        task2 = BackgroundTask("task-2", "cmd2", mock_process2, manager.log_dir / "task-2.log")
        manager.tasks["task-2"] = task2

        # Add running task
        mock_process3 = Mock(spec=subprocess.Popen)
        mock_process3.pid = 333
        mock_process3.poll.return_value = None  # Running
        task3 = BackgroundTask("task-3", "cmd3", mock_process3, manager.log_dir / "task-3.log")
        manager.tasks["task-3"] = task3

        count = manager.cleanup_completed()

        # Should remove 2 tasks (completed and failed)
        assert count == 2
        assert len(manager.tasks) == 1
        assert "task-3" in manager.tasks
        assert "task-1" not in manager.tasks
        assert "task-2" not in manager.tasks

    def test_display_tasks_empty(self, tmp_path):
        """Test displaying tasks when none exist."""
        manager = TaskManager(working_directory=tmp_path)

        # Should not raise an error
        manager.display_tasks()
        # Output verification would require mocking console

    def test_display_tasks_with_tasks(self, tmp_path):
        """Test displaying tasks."""
        manager = TaskManager(working_directory=tmp_path)

        # Add a task
        mock_process = Mock(spec=subprocess.Popen)
        mock_process.pid = 12345
        mock_process.poll.return_value = None
        task = BackgroundTask("task-1", "echo test", mock_process, manager.log_dir / "task-1.log")
        manager.tasks["task-1"] = task

        # Should not raise an error
        manager.display_tasks()
        # Output verification would require mocking console

    def test_display_task_output_not_found(self, tmp_path):
        """Test displaying output for non-existent task."""
        manager = TaskManager(working_directory=tmp_path)

        # Should not raise an error
        manager.display_task_output("nonexistent")
        # Output verification would require mocking console

    def test_display_task_output_success(self, tmp_path):
        """Test displaying output for existing task."""
        manager = TaskManager(working_directory=tmp_path)

        # Add a task with output
        mock_process = Mock(spec=subprocess.Popen)
        mock_process.pid = 12345
        mock_process.poll.return_value = 0
        log_file = manager.log_dir / "task-1.log"
        log_file.write_text("Task output here")
        task = BackgroundTask("task-1", "echo test", mock_process, log_file)
        manager.tasks["task-1"] = task

        # Should not raise an error
        manager.display_task_output("task-1")
        # Output verification would require mocking console


# Run with: pytest tests/test_task_manager.py -v
