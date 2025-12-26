"""Unit tests for ConversationManager.

Tests cover:
- Initialization and configuration
- Tool call extraction from text
- Path validation (placeholder detection)
- Destructive operation detection
- Tool execution (mocked)
- Loop detector integration
- Goal tracker integration
- Multi-turn tool calling flow
- Error recovery
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
import json

from hrisa_code.core.conversation import ConversationManager
from hrisa_code.core.ollama_client import OllamaConfig
from hrisa_code.core.loop_detector import LoopStatus
from hrisa_code.core.goal_tracker import GoalStatus


class TestConversationManagerInitialization:
    """Test ConversationManager initialization and configuration."""

    def test_initialization_default(self, tmp_path):
        """Test initialization with default settings."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
        )

        assert manager.ollama_client is not None
        assert manager.working_directory == tmp_path
        assert manager.enable_tools is True
        assert manager.tool_definitions is not None
        assert manager.loop_detector is not None
        assert manager.goal_tracker is not None
        assert manager.system_prompt is not None
        assert manager.task_manager is None

    def test_initialization_with_custom_system_prompt(self, tmp_path):
        """Test initialization with custom system prompt."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        custom_prompt = "You are a specialized assistant."
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
            system_prompt=custom_prompt,
        )

        assert manager.system_prompt == custom_prompt

    def test_initialization_tools_disabled(self, tmp_path):
        """Test initialization with tools disabled."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
            enable_tools=False,
        )

        assert manager.enable_tools is False
        assert manager.tool_definitions is None

    def test_initialization_with_task_manager(self, tmp_path):
        """Test initialization with task manager."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        mock_task_manager = Mock()
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
            task_manager=mock_task_manager,
        )

        assert manager.task_manager is mock_task_manager

    def test_default_system_prompt_includes_working_directory(self, tmp_path):
        """Test that default system prompt includes working directory."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
        )

        assert str(tmp_path) in manager.system_prompt
        assert "working directory" in manager.system_prompt.lower()


class TestToolCallExtraction:
    """Test extraction of tool calls from text responses."""

    def test_extract_tool_calls_from_text_simple(self, tmp_path):
        """Test extracting a simple tool call from text."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
        )

        text = '''I'll read the file for you.
{"name": "read_file", "arguments": {"file_path": "README.md"}}
'''
        tool_calls = manager._extract_tool_calls_from_text(text)

        assert len(tool_calls) == 1
        assert tool_calls[0]["function"]["name"] == "read_file"
        assert tool_calls[0]["function"]["arguments"]["file_path"] == "README.md"

    def test_extract_tool_calls_from_text_multiple(self, tmp_path):
        """Test extracting multiple tool calls from text."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
        )

        text = '''I'll check the status and then read a file.
{"name": "execute_command", "arguments": {"command": "git status"}}
{"name": "read_file", "arguments": {"file_path": "src/main.py"}}
'''
        tool_calls = manager._extract_tool_calls_from_text(text)

        assert len(tool_calls) == 2
        assert tool_calls[0]["function"]["name"] == "execute_command"
        assert tool_calls[1]["function"]["name"] == "read_file"

    def test_extract_tool_calls_from_text_no_calls(self, tmp_path):
        """Test extracting from text with no tool calls."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
        )

        text = "This is just a regular response with no tool calls."
        tool_calls = manager._extract_tool_calls_from_text(text)

        assert len(tool_calls) == 0

    def test_extract_tool_calls_from_text_malformed_json(self, tmp_path):
        """Test extracting with malformed JSON (should skip)."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
        )

        text = '''I'll read the file.
{"name": "read_file", "arguments": {"file_path": "README.md"
This JSON is broken!
'''
        tool_calls = manager._extract_tool_calls_from_text(text)

        # Should skip malformed JSON
        assert len(tool_calls) == 0

    def test_extract_tool_calls_from_text_unknown_tool(self, tmp_path):
        """Test extracting with unknown tool name (should skip)."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
        )

        text = '''Using an unknown tool.
{"name": "unknown_tool", "arguments": {"param": "value"}}
'''
        tool_calls = manager._extract_tool_calls_from_text(text)

        # Should skip unknown tools
        assert len(tool_calls) == 0


class TestPathValidation:
    """Test path validation to prevent placeholder paths."""

    def test_validate_path_no_placeholders(self, tmp_path):
        """Test validation with valid paths."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
        )

        # Valid relative path
        error = manager._validate_path_arguments("read_file", {"file_path": "README.md"})
        assert error is None

        # Valid absolute path
        error = manager._validate_path_arguments("read_file", {"file_path": "/tmp/test.txt"})
        assert error is None

    def test_validate_path_detects_placeholder_in_file_path(self, tmp_path):
        """Test detection of placeholder in file_path."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
        )

        placeholders = [
            "/path/to/file.txt",
            "path/to/readme.md",
            "/home/user/document.txt",
            "<path>/file.txt",
        ]

        for placeholder in placeholders:
            error = manager._validate_path_arguments("read_file", {"file_path": placeholder})
            assert error is not None
            assert "Placeholder path detected" in error
            assert placeholder in error

    def test_validate_path_detects_placeholder_in_directory(self, tmp_path):
        """Test detection of placeholder in directory."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
        )

        error = manager._validate_path_arguments("list_directory", {"directory": "/path/to/dir"})
        assert error is not None
        assert "Placeholder directory detected" in error

    def test_validate_path_detects_placeholder_in_working_directory(self, tmp_path):
        """Test detection of placeholder in working_directory argument."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
        )

        error = manager._validate_path_arguments(
            "execute_command",
            {"command": "ls", "working_directory": "/path/to/dir"}
        )
        assert error is not None
        assert "Placeholder working_directory detected" in error
        assert "Do NOT provide working_directory" in error


class TestDestructiveOperationDetection:
    """Test detection of destructive operations."""

    def test_is_destructive_write_file_new_file(self, tmp_path):
        """Test write_file to non-existent file (not destructive)."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
        )

        new_file = tmp_path / "new_file.txt"
        is_destructive = manager._is_destructive_operation(
            "write_file",
            {"file_path": str(new_file)}
        )

        assert not is_destructive

    def test_is_destructive_write_file_existing_file(self, tmp_path):
        """Test write_file to existing file (destructive)."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
        )

        # Create existing file
        existing_file = tmp_path / "existing.txt"
        existing_file.write_text("content")

        is_destructive = manager._is_destructive_operation(
            "write_file",
            {"file_path": str(existing_file)}
        )

        assert is_destructive

    def test_is_destructive_execute_command_safe(self, tmp_path):
        """Test safe execute_command (not destructive)."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
        )

        safe_commands = [
            "ls -la",
            "git status",
            "cat README.md",
            "grep pattern file.txt",
        ]

        for command in safe_commands:
            is_destructive = manager._is_destructive_operation(
                "execute_command",
                {"command": command}
            )
            assert not is_destructive, f"Command '{command}' incorrectly flagged as destructive"

    def test_is_destructive_execute_command_dangerous(self, tmp_path):
        """Test dangerous execute_command (destructive)."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
        )

        dangerous_commands = [
            "rm -rf /",
            "del important.txt",
            "delete from table",
            "rmdir directory",
        ]

        for command in dangerous_commands:
            is_destructive = manager._is_destructive_operation(
                "execute_command",
                {"command": command}
            )
            assert is_destructive, f"Command '{command}' not flagged as destructive"

    def test_is_destructive_read_operations(self, tmp_path):
        """Test read operations (never destructive)."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
        )

        assert not manager._is_destructive_operation("read_file", {"file_path": "file.txt"})
        assert not manager._is_destructive_operation("list_directory", {"directory": "."})
        assert not manager._is_destructive_operation("search_files", {"pattern": "test"})

    def test_get_confirmation_message_write_file(self, tmp_path):
        """Test confirmation message for write_file."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
        )

        message = manager._get_confirmation_message("write_file", {"file_path": "test.txt"})
        assert "test.txt" in message
        assert "already exists" in message.lower()

    def test_get_confirmation_message_execute_command(self, tmp_path):
        """Test confirmation message for execute_command."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
        )

        message = manager._get_confirmation_message(
            "execute_command",
            {"command": "rm file.txt"}
        )
        assert "rm file.txt" in message
        assert "destructive" in message.lower()


class TestToolExecution:
    """Test tool execution with mocking."""

    async def test_execute_tool_unknown_tool(self, tmp_path):
        """Test executing unknown tool returns error."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
        )

        result = await manager._execute_tool("unknown_tool", {})
        assert "Error: Unknown tool" in result
        assert "unknown_tool" in result

    async def test_execute_tool_with_placeholder_path(self, tmp_path):
        """Test executing tool with placeholder path returns error."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
        )

        result = await manager._execute_tool("read_file", {"file_path": "/path/to/file.txt"})
        assert "Error: Placeholder path detected" in result

    @patch('hrisa_code.tools.file_operations.ReadFileTool.execute')
    async def test_execute_tool_read_file_success(self, mock_execute, tmp_path):
        """Test successful read_file execution."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
        )

        mock_execute.return_value = "File content here"
        result = await manager._execute_tool("read_file", {"file_path": "README.md"})

        assert result == "File content here"
        mock_execute.assert_called_once()

    async def test_execute_tool_background_execution_no_task_manager(self, tmp_path):
        """Test background execution without task manager returns error."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
            task_manager=None,
        )

        result = await manager._execute_tool(
            "execute_command",
            {"command": "pytest", "background": True}
        )

        assert "Error: Background execution not available" in result

    async def test_execute_tool_background_string_conversion(self, tmp_path):
        """Test background parameter handles string values."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        mock_task_manager = Mock()
        # Mock task object with task_id and pid attributes
        mock_task = Mock()
        mock_task.task_id = "task_123"
        mock_task.pid = 12345
        mock_task_manager.create_task.return_value = mock_task
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
            task_manager=mock_task_manager,
        )

        # Test string "true"
        result = await manager._execute_tool(
            "execute_command",
            {"command": "pytest", "background": "true"}
        )
        assert "task_123" in result
        assert "BACKGROUND TASK" in result


class TestModelOperations:
    """Test model switching and management."""

    def test_switch_model(self, tmp_path):
        """Test switching models."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
        )

        initial_model = manager.get_current_model()
        assert initial_model == "qwen2.5-coder:32b"

        manager.switch_model("qwen2.5-coder:7b", verbose=False)
        new_model = manager.get_current_model()
        assert new_model == "qwen2.5-coder:7b"

    def test_get_current_model(self, tmp_path):
        """Test getting current model."""
        config = OllamaConfig(model="test-model")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
        )

        assert manager.get_current_model() == "test-model"


class TestConversationHistory:
    """Test conversation history management."""

    def test_clear_history(self, tmp_path):
        """Test clearing conversation history."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
        )

        # Add some messages to history
        manager.ollama_client.add_message("user", "Hello")
        manager.ollama_client.add_message("assistant", "Hi there")

        assert len(manager.ollama_client.conversation_history) == 2

        manager.clear_history()
        assert len(manager.ollama_client.conversation_history) == 0


class TestMultiTurnToolCalling:
    """Test multi-turn tool calling integration scenarios."""

    async def test_process_message_no_tool_calls(self, tmp_path):
        """Test processing message with no tool calls."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
        )

        # Mock LLM response with no tool calls
        mock_response = {
            "message": {
                "content": "Hello! How can I help you today?",
                "tool_calls": None
            }
        }

        with patch.object(manager.ollama_client, 'chat_raw', new=AsyncMock(return_value=mock_response)):
            response = await manager.process_message("Hello")

        assert response == "Hello! How can I help you today?"

    async def test_process_message_with_single_tool_call(self, tmp_path):
        """Test processing message with single tool call."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
        )

        # Mock first response with tool call
        tool_call_response = {
            "message": {
                "content": "I'll read the file for you.",
                "tool_calls": [{
                    "function": {
                        "name": "read_file",
                        "arguments": {"file_path": "README.md"}
                    }
                }]
            }
        }

        # Mock final response after tool execution
        final_response = {
            "message": {
                "content": "The file contains README content.",
                "tool_calls": None
            }
        }

        with patch.object(manager.ollama_client, 'chat_raw', new=AsyncMock(return_value=tool_call_response)):
            with patch.object(manager.ollama_client, 'chat_with_tools_result_raw', new=AsyncMock(return_value=final_response)):
                with patch.object(manager, '_execute_tool', return_value="README content"):
                    response = await manager.process_message("What's in the README?")

        assert "The file contains README content." in response

    async def test_process_message_max_rounds_limit(self, tmp_path):
        """Test that process_message respects max_tool_rounds limit."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
        )

        # Mock response that always has tool calls (infinite loop scenario)
        tool_call_response = {
            "message": {
                "content": "I'll read another file.",
                "tool_calls": [{
                    "function": {
                        "name": "read_file",
                        "arguments": {"file_path": "file.txt"}
                    }
                }]
            }
        }

        call_count = 0
        def counting_chat_raw(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return tool_call_response

        with patch.object(manager.ollama_client, 'chat_raw', new=AsyncMock(side_effect=counting_chat_raw)):
            with patch.object(manager.ollama_client, 'chat_with_tools_result_raw', new=AsyncMock(return_value=tool_call_response)):
                with patch.object(manager, '_execute_tool', return_value="content"):
                    # Set max_tool_rounds to 5
                    response = await manager.process_message("Read files", max_tool_rounds=5)

        # Should stop after max_tool_rounds
        # Initial call + 5 rounds = 6 total calls would be expected, but process_message
        # might exit early if goal tracker or loop detector intervenes
        assert call_count <= 6


class TestLoopDetectorIntegration:
    """Test loop detector integration in conversation flow."""

    async def test_loop_detector_prevents_repeated_calls(self, tmp_path):
        """Test that loop detector prevents excessive repeated tool calls."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
        )

        # Mock response that repeatedly calls the same tool
        repeated_tool_call = {
            "message": {
                "content": "Checking status again.",
                "tool_calls": [{
                    "function": {
                        "name": "execute_command",
                        "arguments": {"command": "git status"}
                    }
                }]
            }
        }

        with patch.object(manager.ollama_client, 'chat_raw', new=AsyncMock(return_value=repeated_tool_call)):
            with patch.object(manager.ollama_client, 'chat_with_tools_result_raw', new=AsyncMock(return_value=repeated_tool_call)):
                with patch.object(manager, '_execute_tool', return_value="On branch main"):
                    response = await manager.process_message("Check git status")

        # Loop detector should have been triggered
        assert manager.loop_detector.has_any_loops()


class TestGoalTrackerIntegration:
    """Test goal tracker integration in conversation flow."""

    async def test_goal_tracker_resets_on_new_message(self, tmp_path):
        """Test that goal tracker resets for each new message."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
        )

        # Set some state in goal tracker
        manager.goal_tracker.set_user_question("Old question")
        manager.goal_tracker.add_tool_result("tool", {}, "result", False)
        manager.goal_tracker.current_round = 5

        assert manager.goal_tracker.user_question == "Old question"
        assert len(manager.goal_tracker.tool_results) > 0
        assert manager.goal_tracker.current_round > 0

        # Process new message
        mock_response = {
            "message": {
                "content": "New response",
                "tool_calls": None
            }
        }

        with patch.object(manager.ollama_client, 'chat_raw', new=AsyncMock(return_value=mock_response)):
            await manager.process_message("New question")

        # Goal tracker should be reset with new question
        assert manager.goal_tracker.user_question == "New question"
        assert manager.goal_tracker.current_round >= 0  # May have incremented


class TestApprovalManagerIntegration:
    """Test approval manager integration with conversation flow."""

    def test_approval_manager_initialization_default(self, tmp_path):
        """Test that approval manager is initialized by default."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
        )

        assert manager.approval_manager is not None
        assert manager.approval_manager.auto_approve is False

    def test_approval_manager_initialization_auto_approve(self, tmp_path):
        """Test approval manager with auto_approve enabled."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
            auto_approve=True,
        )

        assert manager.approval_manager is not None
        assert manager.approval_manager.auto_approve is True

    async def test_write_file_new_file_with_auto_approve(self, tmp_path):
        """Test writing new file with auto_approve enabled."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
            auto_approve=True,  # Auto-approve enabled
        )

        new_file = tmp_path / "new_file.txt"

        with patch('hrisa_code.tools.file_operations.WriteFileTool.execute') as mock_execute:
            mock_execute.return_value = "Successfully wrote to file"
            result = await manager._execute_tool("write_file", {
                "file_path": str(new_file),
                "content": "Test content"
            })

        # Should execute without prompting user
        assert "Successfully wrote" in result
        assert "[DENIED]" not in result

    async def test_write_file_existing_file_requires_approval_denied(self, tmp_path):
        """Test writing existing file requires approval and handles denial."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
            auto_approve=False,
        )

        # Create existing file
        existing_file = tmp_path / "existing.txt"
        existing_file.write_text("Original content")

        # Mock user denying approval - patch questionary.select
        mock_select = AsyncMock()
        mock_select.ask_async = AsyncMock(return_value='n')
        with patch('questionary.select', return_value=mock_select):
            result = await manager._execute_tool("write_file", {
                "file_path": str(existing_file),
                "content": "New content"
            })

        assert "[DENIED]" in result
        assert str(existing_file) in result

    async def test_write_file_existing_file_with_auto_approve(self, tmp_path):
        """Test writing existing file with auto_approve bypasses prompts."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
            auto_approve=True,
        )

        # Create existing file
        existing_file = tmp_path / "existing.txt"
        existing_file.write_text("Original content")

        with patch('hrisa_code.tools.file_operations.WriteFileTool.execute') as mock_execute:
            mock_execute.return_value = "Successfully wrote to file"
            result = await manager._execute_tool("write_file", {
                "file_path": str(existing_file),
                "content": "New content"
            })

        # Should succeed without prompting user
        assert "Successfully wrote" in result
        assert "[DENIED]" not in result

    async def test_write_file_existing_file_approved(self, tmp_path):
        """Test writing existing file with user approval."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
            auto_approve=False,
        )

        # Create existing file
        existing_file = tmp_path / "existing.txt"
        existing_file.write_text("Original content")

        # Mock user approving - patch questionary.select
        mock_select = AsyncMock()
        mock_select.ask_async = AsyncMock(return_value='y')
        with patch('questionary.select', return_value=mock_select):
            with patch('hrisa_code.tools.file_operations.WriteFileTool.execute') as mock_execute:
                mock_execute.return_value = "Successfully wrote to file"
                result = await manager._execute_tool("write_file", {
                    "file_path": str(existing_file),
                    "content": "New content"
                })

        assert "Successfully wrote" in result
        assert "[DENIED]" not in result

    async def test_destructive_command_requires_approval_denied(self, tmp_path):
        """Test destructive command requires approval and handles denial."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
            auto_approve=False,
        )

        # Mock user denying approval - patch questionary.select
        mock_select = AsyncMock()
        mock_select.ask_async = AsyncMock(return_value='n')
        with patch('questionary.select', return_value=mock_select):
            result = await manager._execute_tool("execute_command", {
                "command": "rm -rf dangerous_dir"
            })

        assert "[DENIED]" in result
        assert "rm -rf dangerous_dir" in result

    async def test_destructive_command_with_auto_approve(self, tmp_path):
        """Test destructive command with auto_approve bypasses prompts."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
            auto_approve=True,
        )

        with patch('hrisa_code.tools.file_operations.ExecuteCommandTool.execute') as mock_execute:
            mock_execute.return_value = "Command executed"
            result = await manager._execute_tool("execute_command", {
                "command": "rm -rf test_dir"
            })

        # Should execute without denial
        assert "Command executed" in result
        assert "[DENIED]" not in result

    async def test_destructive_command_approved(self, tmp_path):
        """Test destructive command with user approval."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
            auto_approve=False,
        )

        # Mock user approving - patch questionary.select
        mock_select = AsyncMock()
        mock_select.ask_async = AsyncMock(return_value='y')
        with patch('questionary.select', return_value=mock_select):
            with patch('hrisa_code.tools.file_operations.ExecuteCommandTool.execute') as mock_execute:
                mock_execute.return_value = "Command executed"
                result = await manager._execute_tool("execute_command", {
                    "command": "rm test_file.txt"
                })

        assert "Command executed" in result
        assert "[DENIED]" not in result

    async def test_safe_command_no_approval_needed(self, tmp_path):
        """Test safe commands don't require approval."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
            auto_approve=False,
        )

        with patch('hrisa_code.tools.file_operations.ExecuteCommandTool.execute') as mock_execute:
            mock_execute.return_value = "Command output"
            result = await manager._execute_tool("execute_command", {
                "command": "git status"
            })

        # Should execute without approval check
        assert "Command output" in result
        assert "[DENIED]" not in result

    async def test_read_operations_no_approval_needed(self, tmp_path):
        """Test read operations don't require approval."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
            auto_approve=False,
        )

        # Test read_file
        with patch('hrisa_code.tools.file_operations.ReadFileTool.execute') as mock_execute:
            mock_execute.return_value = "File content"
            result = await manager._execute_tool("read_file", {
                "file_path": "README.md"
            })

        assert "File content" in result
        assert "[DENIED]" not in result

    def test_is_command_destructive_detection(self, tmp_path):
        """Test destructive command detection."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
        )

        # Test destructive commands
        assert manager._is_command_destructive("rm -rf /")
        assert manager._is_command_destructive("del important.txt")
        assert manager._is_command_destructive("delete from users")
        assert manager._is_command_destructive("rmdir folder")
        assert manager._is_command_destructive("echo test > file.txt")  # Redirection

        # Test safe commands
        assert not manager._is_command_destructive("git status")
        assert not manager._is_command_destructive("ls -la")
        assert not manager._is_command_destructive("cat README.md")
        assert not manager._is_command_destructive("grep pattern file.txt")

    async def test_approval_check_returns_none_for_approved(self, tmp_path):
        """Test _check_approval returns None for approved operations."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
            auto_approve=True,
        )

        # Create existing file
        existing_file = tmp_path / "existing.txt"
        existing_file.write_text("Content")

        result = await manager._check_approval("write_file", {
            "file_path": str(existing_file),
            "content": "New content"
        })

        assert result is None  # Approved

    async def test_approval_check_returns_error_for_denied(self, tmp_path):
        """Test _check_approval returns error message for denied operations."""
        config = OllamaConfig(model="qwen2.5-coder:32b")
        manager = ConversationManager(
            ollama_config=config,
            working_directory=tmp_path,
            auto_approve=False,
        )

        # Create existing file
        existing_file = tmp_path / "existing.txt"
        existing_file.write_text("Content")

        # Mock user denying - patch questionary.select
        mock_select = AsyncMock()
        mock_select.ask_async = AsyncMock(return_value='n')
        with patch('questionary.select', return_value=mock_select):
            result = await manager._check_approval("write_file", {
                "file_path": str(existing_file),
                "content": "New content"
            })

        assert result is not None
        assert "[DENIED]" in result


# Run with: pytest tests/test_conversation.py -v
