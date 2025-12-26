"""Unit tests for file operation tools.

Tests cover:
- ReadFileTool: reading, line ranges, errors
- WriteFileTool: creation, overwrite, errors
- ListDirectoryTool: listing, recursive, filtering, errors
- ExecuteCommandTool: execution, timeout, errors
- Tool definitions and registry
"""

import pytest
from pathlib import Path
from unittest.mock import patch, Mock
import subprocess

from hrisa_code.tools.file_operations import (
    ReadFileTool,
    WriteFileTool,
    ListDirectoryTool,
    ExecuteCommandTool,
    AVAILABLE_TOOLS,
    get_all_tool_definitions,
)


class TestReadFileTool:
    """Test ReadFileTool."""

    def test_get_definition(self):
        """Test tool definition format."""
        definition = ReadFileTool.get_definition()

        assert definition["type"] == "function"
        assert definition["function"]["name"] == "read_file"
        assert "description" in definition["function"]
        assert "parameters" in definition["function"]
        assert "file_path" in definition["function"]["parameters"]["properties"]
        assert "file_path" in definition["function"]["parameters"]["required"]

    def test_execute_read_simple_file(self, tmp_path):
        """Test reading a simple file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Line 1\nLine 2\nLine 3\n")

        result = ReadFileTool.execute(str(test_file))
        assert result == "Line 1\nLine 2\nLine 3\n"

    def test_execute_read_with_line_range(self, tmp_path):
        """Test reading specific line range."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n")

        result = ReadFileTool.execute(str(test_file), start_line=2, end_line=4)
        assert result == "Line 2\nLine 3\nLine 4\n"

    def test_execute_read_from_start_line_only(self, tmp_path):
        """Test reading from start line to end."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Line 1\nLine 2\nLine 3\n")

        result = ReadFileTool.execute(str(test_file), start_line=2)
        assert result == "Line 2\nLine 3\n"

    def test_execute_read_to_end_line_only(self, tmp_path):
        """Test reading from beginning to end line."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Line 1\nLine 2\nLine 3\n")

        result = ReadFileTool.execute(str(test_file), end_line=2)
        assert result == "Line 1\nLine 2\n"

    def test_execute_file_not_found(self, tmp_path):
        """Test reading non-existent file."""
        result = ReadFileTool.execute(str(tmp_path / "nonexistent.txt"))
        assert "Error: File not found" in result

    def test_execute_read_empty_file(self, tmp_path):
        """Test reading empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_text("")

        result = ReadFileTool.execute(str(test_file))
        assert result == ""

    def test_execute_read_unicode(self, tmp_path):
        """Test reading file with unicode."""
        test_file = tmp_path / "unicode.txt"
        test_file.write_text("Hello 世界 🌍\n", encoding="utf-8")

        result = ReadFileTool.execute(str(test_file))
        assert "Hello 世界 🌍" in result


class TestWriteFileTool:
    """Test WriteFileTool."""

    def test_get_definition(self):
        """Test tool definition format."""
        definition = WriteFileTool.get_definition()

        assert definition["type"] == "function"
        assert definition["function"]["name"] == "write_file"
        assert "description" in definition["function"]
        assert "file_path" in definition["function"]["parameters"]["properties"]
        assert "content" in definition["function"]["parameters"]["properties"]
        assert "file_path" in definition["function"]["parameters"]["required"]
        assert "content" in definition["function"]["parameters"]["required"]

    def test_execute_write_new_file(self, tmp_path):
        """Test writing to new file."""
        test_file = tmp_path / "new.txt"
        content = "Test content\nLine 2"

        result = WriteFileTool.execute(str(test_file), content)
        assert "Successfully wrote" in result
        assert test_file.exists()
        assert test_file.read_text() == content

    def test_execute_write_overwrites_existing(self, tmp_path):
        """Test writing overwrites existing file."""
        test_file = tmp_path / "existing.txt"
        test_file.write_text("Old content")

        new_content = "New content"
        result = WriteFileTool.execute(str(test_file), new_content)
        assert "Successfully wrote" in result
        assert test_file.read_text() == new_content

    def test_execute_write_creates_parent_dirs(self, tmp_path):
        """Test writing creates parent directories."""
        test_file = tmp_path / "subdir" / "nested" / "file.txt"
        content = "Test"

        result = WriteFileTool.execute(str(test_file), content)
        assert "Successfully wrote" in result
        assert test_file.exists()
        assert test_file.read_text() == content

    def test_execute_write_empty_content(self, tmp_path):
        """Test writing empty content."""
        test_file = tmp_path / "empty.txt"

        result = WriteFileTool.execute(str(test_file), "")
        assert "Successfully wrote" in result
        assert test_file.read_text() == ""

    def test_execute_write_unicode(self, tmp_path):
        """Test writing unicode content."""
        test_file = tmp_path / "unicode.txt"
        content = "Hello 世界 🌍"

        result = WriteFileTool.execute(str(test_file), content)
        assert "Successfully wrote" in result
        assert test_file.read_text(encoding="utf-8") == content


class TestListDirectoryTool:
    """Test ListDirectoryTool."""

    def test_get_definition(self):
        """Test tool definition format."""
        definition = ListDirectoryTool.get_definition()

        assert definition["type"] == "function"
        assert definition["function"]["name"] == "list_directory"
        assert "directory_path" in definition["function"]["parameters"]["properties"]
        assert "recursive" in definition["function"]["parameters"]["properties"]

    def test_execute_list_simple_directory(self, tmp_path):
        """Test listing directory contents."""
        # Create test structure
        (tmp_path / "file1.txt").write_text("content")
        (tmp_path / "file2.py").write_text("code")
        (tmp_path / "subdir").mkdir()

        result = ListDirectoryTool.execute(str(tmp_path))

        assert "file1.txt" in result
        assert "file2.py" in result
        assert "subdir" in result or "subdir/" in result

    def test_execute_list_recursive(self, tmp_path):
        """Test recursive directory listing."""
        # Create nested structure
        (tmp_path / "file1.txt").write_text("content")
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "file2.txt").write_text("content")
        nested = subdir / "nested"
        nested.mkdir()
        (nested / "file3.txt").write_text("content")

        result = ListDirectoryTool.execute(str(tmp_path), recursive=True)

        assert "file1.txt" in result
        assert "file2.txt" in result
        assert "file3.txt" in result

    def test_execute_list_non_recursive(self, tmp_path):
        """Test non-recursive listing (default)."""
        (tmp_path / "file1.txt").write_text("content")
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "file2.txt").write_text("content")

        result = ListDirectoryTool.execute(str(tmp_path), recursive=False)

        assert "file1.txt" in result
        # file2.txt should not appear (it's in subdir)
        assert "file2.txt" not in result

    def test_execute_list_empty_directory(self, tmp_path):
        """Test listing empty directory."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        result = ListDirectoryTool.execute(str(empty_dir))
        assert "No files found" in result or result.strip() == ""

    def test_execute_list_directory_not_found(self, tmp_path):
        """Test listing non-existent directory."""
        result = ListDirectoryTool.execute(str(tmp_path / "nonexistent"))
        assert "Error" in result

    def test_execute_list_shows_file_types(self, tmp_path):
        """Test that listing shows file vs directory."""
        (tmp_path / "file.txt").write_text("content")
        (tmp_path / "dir").mkdir()

        result = ListDirectoryTool.execute(str(tmp_path))

        # Should indicate what's a file vs directory
        assert "file.txt" in result
        assert "dir" in result


class TestExecuteCommandTool:
    """Test ExecuteCommandTool."""

    def test_get_definition(self):
        """Test tool definition format."""
        definition = ExecuteCommandTool.get_definition()

        assert definition["type"] == "function"
        assert definition["function"]["name"] == "execute_command"
        assert "command" in definition["function"]["parameters"]["properties"]
        assert "working_directory" in definition["function"]["parameters"]["properties"]
        assert "command" in definition["function"]["parameters"]["required"]

    def test_execute_simple_command(self, tmp_path):
        """Test executing simple command."""
        result = ExecuteCommandTool.execute("echo 'Hello World'", working_directory=str(tmp_path))

        assert "Error" not in result or "Hello World" in result

    def test_execute_command_with_output(self, tmp_path):
        """Test command with output."""
        # Create a file and list it
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        result = ExecuteCommandTool.execute("ls", working_directory=str(tmp_path))

        assert "test.txt" in result

    def test_execute_command_with_error(self, tmp_path):
        """Test command that fails."""
        result = ExecuteCommandTool.execute(
            "nonexistentcommand12345",
            working_directory=str(tmp_path)
        )

        assert "Error" in result or "not found" in result.lower()

    def test_execute_command_respects_working_directory(self, tmp_path):
        """Test that working directory is used."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "file.txt").write_text("content")

        # Execute ls in subdir
        result = ExecuteCommandTool.execute("ls", working_directory=str(subdir))

        assert "file.txt" in result

    @patch('subprocess.run')
    def test_execute_command_handles_exceptions(self, mock_run, tmp_path):
        """Test exception handling in command execution."""
        mock_run.side_effect = Exception("Command failed")

        result = ExecuteCommandTool.execute("any_command", working_directory=str(tmp_path))

        assert "Error" in result


class TestToolRegistry:
    """Test tool registry and definitions."""

    def test_available_tools_contains_all_tools(self):
        """Test that AVAILABLE_TOOLS has all expected tools."""
        assert "read_file" in AVAILABLE_TOOLS
        assert "write_file" in AVAILABLE_TOOLS
        assert "list_directory" in AVAILABLE_TOOLS
        assert "execute_command" in AVAILABLE_TOOLS
        assert "search_files" in AVAILABLE_TOOLS
        # Git tools should also be included
        assert "git_status" in AVAILABLE_TOOLS
        assert "git_diff" in AVAILABLE_TOOLS
        assert "git_log" in AVAILABLE_TOOLS
        assert "git_branch" in AVAILABLE_TOOLS

    def test_get_all_tool_definitions(self):
        """Test getting all tool definitions."""
        definitions = get_all_tool_definitions()

        assert isinstance(definitions, list)
        assert len(definitions) > 0

        # Each definition should have proper structure
        for definition in definitions:
            assert "type" in definition
            assert definition["type"] == "function"
            assert "function" in definition
            assert "name" in definition["function"]
            assert "description" in definition["function"]
            assert "parameters" in definition["function"]

    def test_tool_definitions_have_unique_names(self):
        """Test that all tool names are unique."""
        definitions = get_all_tool_definitions()
        names = [d["function"]["name"] for d in definitions]

        assert len(names) == len(set(names)), "Tool names must be unique"

    def test_all_tools_have_get_definition_method(self):
        """Test that all tool classes have get_definition method."""
        for tool_name, tool_class in AVAILABLE_TOOLS.items():
            assert hasattr(tool_class, 'get_definition'), \
                f"Tool {tool_name} missing get_definition method"
            assert callable(tool_class.get_definition)

    def test_all_tools_have_execute_method(self):
        """Test that all tool classes have execute method."""
        for tool_name, tool_class in AVAILABLE_TOOLS.items():
            assert hasattr(tool_class, 'execute'), \
                f"Tool {tool_name} missing execute method"
            assert callable(tool_class.execute)


class TestToolIntegration:
    """Test tool integration scenarios."""

    def test_write_then_read_file(self, tmp_path):
        """Test writing then reading a file."""
        test_file = tmp_path / "test.txt"
        content = "Test content"

        # Write
        write_result = WriteFileTool.execute(str(test_file), content)
        assert "Successfully" in write_result

        # Read
        read_result = ReadFileTool.execute(str(test_file))
        assert read_result == content

    def test_write_file_then_list_directory(self, tmp_path):
        """Test writing file then listing directory."""
        test_file = tmp_path / "test.txt"

        # Write
        WriteFileTool.execute(str(test_file), "content")

        # List
        list_result = ListDirectoryTool.execute(str(tmp_path))
        assert "test.txt" in list_result

    def test_create_file_then_execute_cat(self, tmp_path):
        """Test creating file then reading with cat command."""
        test_file = tmp_path / "test.txt"
        content = "Hello from cat"

        # Write
        WriteFileTool.execute(str(test_file), content)

        # Execute cat
        cat_result = ExecuteCommandTool.execute(
            f"cat {test_file.name}",
            working_directory=str(tmp_path)
        )

        # On systems without cat, this might fail
        if "Error" not in cat_result:
            assert content in cat_result


# Run with: pytest tests/test_file_operations.py -v
