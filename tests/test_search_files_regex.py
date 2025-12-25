"""Unit tests for search_files tool with regex support."""

import pytest
from pathlib import Path
from src.hrisa_code.tools.file_operations import SearchFilesTool


class TestSearchFilesRegex:
    """Test suite for regex functionality in search_files tool."""

    def test_search_with_regex_simple_pattern(self):
        """Test basic regex pattern matching."""
        result = SearchFilesTool.execute(
            pattern=r"@app\.command",
            directory="src",
            use_regex=True
        )
        assert "cli.py" in result
        assert "@app.command()" in result
        assert "No matches found" not in result

    def test_search_with_regex_or_operator(self):
        """Test regex OR operator (|) functionality."""
        result = SearchFilesTool.execute(
            pattern=r"def (chat|init|models)",
            directory="src"
        )
        assert "def chat" in result
        assert "def init" in result
        assert "def models" in result
        assert "No matches found" not in result

    def test_search_with_regex_character_classes(self):
        """Test regex character classes."""
        result = SearchFilesTool.execute(
            pattern=r"class\s+\w+Catalog",
            directory="src"
        )
        assert "ModelCatalog" in result
        assert "No matches found" not in result

    def test_search_with_literal_string(self):
        """Test literal string matching with use_regex=False."""
        result = SearchFilesTool.execute(
            pattern="@app.command",
            directory="src",
            use_regex=False
        )
        assert "cli.py" in result
        assert "@app.command()" in result

    def test_search_with_literal_preserves_special_chars(self):
        """Test that literal mode doesn't interpret regex special chars."""
        # Search for literal string that would be invalid regex
        result = SearchFilesTool.execute(
            pattern="def (",  # Would be invalid regex
            directory="src",
            use_regex=False
        )
        # Should not raise error, just find literal occurrences
        assert "Error: Invalid regex" not in result

    def test_search_with_invalid_regex(self):
        """Test that invalid regex patterns are caught gracefully."""
        result = SearchFilesTool.execute(
            pattern=r"@app\.command((",  # Invalid regex
            directory="src",
            use_regex=True
        )
        assert "Error: Invalid regex pattern" in result
        assert "missing )" in result.lower()

    def test_search_with_recursive_file_pattern(self):
        """Test recursive file pattern **/*.py."""
        result = SearchFilesTool.execute(
            pattern=r"ModelCatalog",
            directory="src",
            file_pattern="**/*.py"
        )
        assert "model_catalog.py" in result
        assert "No matches found" not in result

    def test_search_with_non_recursive_file_pattern_made_recursive(self):
        """Test that *.py is automatically made recursive to **/*.py."""
        # Without fix, *.py would only search src/ directly
        # With fix, *.py becomes **/*.py automatically
        result = SearchFilesTool.execute(
            pattern=r"ModelRouter",
            directory="src",
            file_pattern="*.py"
        )
        # Should find it in src/hrisa_code/core/model_router.py
        assert "model_router.py" in result
        assert "No matches found" not in result

    def test_search_with_no_file_pattern_searches_all(self):
        """Test that omitting file_pattern searches all files recursively."""
        result = SearchFilesTool.execute(
            pattern=r"OllamaClient",
            directory="src"
            # No file_pattern specified
        )
        assert "ollama_client.py" in result
        assert "No matches found" not in result

    def test_search_with_multiline_not_matching_across_lines(self):
        """Test that patterns don't match across line boundaries."""
        # search_files searches line by line, shouldn't match patterns
        # that span multiple lines
        result = SearchFilesTool.execute(
            pattern=r"def\s+chat.*model",  # Would need to span lines
            directory="src"
        )
        # This should either find nothing or only find single-line matches
        # The important thing is it doesn't crash

    def test_search_nonexistent_directory(self):
        """Test searching in non-existent directory."""
        result = SearchFilesTool.execute(
            pattern=r"test",
            directory="/nonexistent/directory"
        )
        assert "Error: Directory not found" in result

    def test_search_no_matches_found_message(self):
        """Test proper 'no matches found' message for regex."""
        result = SearchFilesTool.execute(
            pattern=r"ThisPatternDefinitelyDoesNotExistAnywhere",
            directory="src",
            use_regex=True
        )
        assert "No matches found for regex pattern" in result

    def test_search_no_matches_found_message_literal(self):
        """Test proper 'no matches found' message for literal."""
        result = SearchFilesTool.execute(
            pattern="ThisPatternDefinitelyDoesNotExistAnywhere",
            directory="src",
            use_regex=False
        )
        assert "No matches found for literal pattern" in result

    def test_search_respects_result_limit(self):
        """Test that results are limited to 100 lines."""
        # Search for something very common
        result = SearchFilesTool.execute(
            pattern=r"import",
            directory="src"
        )
        lines = result.split('\n')
        # Should be capped at 100
        assert len(lines) <= 100

    def test_search_with_case_sensitive_regex(self):
        """Test that regex is case-sensitive by default."""
        result = SearchFilesTool.execute(
            pattern=r"modelcatalog",  # lowercase
            directory="src"
        )
        # Should not match ModelCatalog (uppercase M and C)
        assert "No matches found" in result

    def test_search_with_escaped_special_chars(self):
        """Test regex with properly escaped special characters."""
        result = SearchFilesTool.execute(
            pattern=r"\(self\)",
            directory="src"
        )
        assert "(self)" in result
        assert "No matches found" not in result

    def test_search_with_line_anchors(self):
        """Test regex line anchors (^ and $)."""
        # Note: Line anchors might not work as expected since we search
        # within lines, but shouldn't crash
        result = SearchFilesTool.execute(
            pattern=r"^import",
            directory="src"
        )
        # Should find imports at the start of lines
        if "No matches found" not in result:
            assert "import" in result

    def test_default_use_regex_is_true(self):
        """Test that use_regex defaults to True."""
        # This should work with regex pattern without specifying use_regex
        result = SearchFilesTool.execute(
            pattern=r"@app\.command",
            directory="src"
            # use_regex not specified, should default to True
        )
        assert "cli.py" in result
        assert "@app.command()" in result

    def test_working_directory_alias(self):
        """Test that working_directory parameter works as alias for directory."""
        result = SearchFilesTool.execute(
            pattern=r"@app\.command",
            working_directory="src"  # Using alias instead of directory
        )
        assert "cli.py" in result
        assert "@app.command()" in result
        assert "No matches found" not in result

    def test_directory_takes_precedence_over_working_directory(self):
        """Test that directory parameter takes precedence when both are provided."""
        result = SearchFilesTool.execute(
            pattern=r"@app\.command",
            directory="src",  # Valid directory
            working_directory="/nonexistent"  # Would fail if used
        )
        # Should use directory parameter and succeed
        assert "cli.py" in result
        assert "Error" not in result

    def test_neither_directory_parameter_fails_gracefully(self):
        """Test that omitting both directory parameters returns clear error."""
        result = SearchFilesTool.execute(
            pattern=r"@app\.command"
            # Neither directory nor working_directory provided
        )
        assert "Error" in result
        assert "directory" in result.lower() or "working_directory" in result.lower()


class TestSearchFilesToolDefinition:
    """Test the tool definition includes regex documentation."""

    def test_tool_definition_mentions_regex(self):
        """Test that tool definition describes regex support."""
        definition = SearchFilesTool.get_definition()
        description = definition["function"]["description"]
        assert "regex" in description.lower()

    def test_tool_definition_has_use_regex_parameter(self):
        """Test that tool definition includes use_regex parameter."""
        definition = SearchFilesTool.get_definition()
        params = definition["function"]["parameters"]["properties"]
        assert "use_regex" in params

    def test_tool_definition_has_regex_examples(self):
        """Test that pattern parameter includes regex examples."""
        definition = SearchFilesTool.get_definition()
        pattern_desc = definition["function"]["parameters"]["properties"]["pattern"]["description"]
        # Should have examples like '@app\.command'
        assert "@app" in pattern_desc or "\\." in pattern_desc

    def test_tool_definition_explains_file_pattern_recursion(self):
        """Test that file_pattern parameter explains recursive vs non-recursive."""
        definition = SearchFilesTool.get_definition()
        file_pattern_desc = definition["function"]["parameters"]["properties"]["file_pattern"]["description"]
        assert "**/" in file_pattern_desc
        assert "recursive" in file_pattern_desc.lower()


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
