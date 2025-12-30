"""Intelligent tool selection guidance system.

This module helps LLMs choose the right tools and use them correctly by:
1. Understanding tool capabilities and use cases
2. Validating parameters before execution
3. Suggesting corrections for invalid parameters
4. Providing hints about which tool to use
5. Detecting parameter type mismatches
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class ValidationStatus(Enum):
    """Status of parameter validation."""
    VALID = "valid"                      # All parameters are valid
    INVALID = "invalid"                  # Parameters are invalid
    MISSING_REQUIRED = "missing_required"  # Required parameters missing
    TYPE_MISMATCH = "type_mismatch"      # Parameter type doesn't match
    DEPRECATED = "deprecated"            # Tool or parameter is deprecated


@dataclass
class ParameterSuggestion:
    """Suggestion for fixing an invalid parameter.

    Attributes:
        parameter_name: Name of the parameter
        current_value: Current (invalid) value
        suggested_value: Suggested correct value
        reason: Why the current value is invalid
        example: Example of correct usage
    """
    parameter_name: str
    current_value: Any
    suggested_value: Optional[Any]
    reason: str
    example: str


@dataclass
class ToolValidationResult:
    """Result of validating a tool call.

    Attributes:
        status: Validation status
        is_valid: Whether the tool call is valid
        errors: List of validation errors
        warnings: List of warnings (non-blocking)
        suggestions: List of parameter suggestions
        corrected_arguments: Automatically corrected arguments (if possible)
    """
    status: ValidationStatus
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[ParameterSuggestion]
    corrected_arguments: Optional[Dict[str, Any]]


@dataclass
class ToolCapability:
    """Description of what a tool can do.

    Attributes:
        tool_name: Name of the tool
        use_cases: What this tool is good for
        limitations: What this tool cannot do
        common_mistakes: Common mistakes when using this tool
        related_tools: Alternative or complementary tools
        examples: Example use cases
    """
    tool_name: str
    use_cases: List[str]
    limitations: List[str]
    common_mistakes: List[str]
    related_tools: List[str]
    examples: List[str]


class ToolAdvisor:
    """Provides intelligent guidance for tool selection and usage.

    This class helps LLMs:
    - Choose the right tool for a task
    - Use tools with correct parameters
    - Recover from invalid tool calls
    - Understand tool limitations

    It acts as a "tool expert" that guides the LLM toward correct usage.
    """

    def __init__(self, available_tools: Dict[str, Any]):
        """Initialize the tool advisor.

        Args:
            available_tools: Dictionary of available tool classes
        """
        self.available_tools = available_tools
        self.tool_capabilities = self._build_capability_database()
        self.parameter_validators = self._build_parameter_validators()

    def _build_capability_database(self) -> Dict[str, ToolCapability]:
        """Build a database of tool capabilities and use cases.

        Returns:
            Dictionary mapping tool names to capabilities
        """
        capabilities = {
            "read_file": ToolCapability(
                tool_name="read_file",
                use_cases=[
                    "Reading source code files",
                    "Viewing configuration files",
                    "Reading documentation",
                    "Examining text files",
                ],
                limitations=[
                    "Cannot read binary files effectively",
                    "Not suitable for large files (>10000 lines)",
                    "Cannot list directory contents (use list_directory)",
                    "Cannot search file contents (use search_files)",
                ],
                common_mistakes=[
                    "Using read_file to find files (use search_files or list_directory)",
                    "Reading entire large files (use start_line/end_line)",
                    "Trying to read non-existent files without checking first",
                ],
                related_tools=["list_directory", "search_files"],
                examples=[
                    "read_file(file_path='src/main.py')",
                    "read_file(file_path='config.yaml', start_line=1, end_line=50)",
                ],
            ),
            "write_file": ToolCapability(
                tool_name="write_file",
                use_cases=[
                    "Creating new files",
                    "Overwriting existing files",
                    "Writing generated content",
                ],
                limitations=[
                    "Overwrites entire file (not for partial edits)",
                    "Requires user approval for existing files",
                    "Cannot create directories (directory must exist)",
                ],
                common_mistakes=[
                    "Not checking if file exists first",
                    "Trying to make small edits (use read_file + write_file)",
                    "Forgetting to include complete content",
                ],
                related_tools=["read_file", "delete_file"],
                examples=[
                    "write_file(file_path='new_file.py', content='# Code here')",
                ],
            ),
            "list_directory": ToolCapability(
                tool_name="list_directory",
                use_cases=[
                    "Listing files in a directory",
                    "Exploring project structure",
                    "Finding files by pattern",
                ],
                limitations=[
                    "Only lists one directory level (not recursive)",
                    "Does not search file contents",
                    "Limited filtering capabilities",
                ],
                common_mistakes=[
                    "Expecting recursive listing",
                    "Using when search_files would be better",
                ],
                related_tools=["search_files", "read_file"],
                examples=[
                    "list_directory(directory_path='src')",
                    "list_directory(directory_path='.')",
                ],
            ),
            "search_files": ToolCapability(
                tool_name="search_files",
                use_cases=[
                    "Finding files by name pattern",
                    "Searching for specific content in files",
                    "Locating files matching criteria",
                ],
                limitations=[
                    "May be slow for large codebases",
                    "Pattern matching only (not fuzzy search)",
                ],
                common_mistakes=[
                    "Using overly broad patterns",
                    "Not using grep when content search is needed",
                ],
                related_tools=["list_directory", "execute_command"],
                examples=[
                    "search_files(pattern='*.py', directory='src')",
                    "search_files(pattern='*test*', directory='tests')",
                ],
            ),
            "execute_command": ToolCapability(
                tool_name="execute_command",
                use_cases=[
                    "Running shell commands",
                    "Running tests",
                    "Building projects",
                    "Git operations",
                ],
                limitations=[
                    "Requires shell availability",
                    "May need user approval for destructive commands",
                    "Cannot handle interactive prompts well",
                ],
                common_mistakes=[
                    "Running long-running commands without background=true",
                    "Not checking command success before proceeding",
                    "Using when specific tool exists (e.g., git_status vs 'git status')",
                ],
                related_tools=["git_status", "git_diff", "git_log"],
                examples=[
                    "execute_command(command='pytest tests/')",
                    "execute_command(command='npm install')",
                    "execute_command(command='./run_server.sh', background=true)",
                ],
            ),
            "delete_file": ToolCapability(
                tool_name="delete_file",
                use_cases=[
                    "Removing files",
                    "Cleaning up generated files",
                ],
                limitations=[
                    "Cannot delete directories",
                    "Requires user approval",
                    "Cannot be undone",
                ],
                common_mistakes=[
                    "Not checking file exists first",
                    "Trying to delete important files",
                ],
                related_tools=["read_file", "write_file"],
                examples=[
                    "delete_file(file_path='temp_file.txt')",
                ],
            ),
            "git_status": ToolCapability(
                tool_name="git_status",
                use_cases=[
                    "Checking repository status",
                    "Seeing modified files",
                    "Checking branch info",
                ],
                limitations=[
                    "Only shows status, doesn't show changes",
                    "Requires git repository",
                ],
                common_mistakes=[
                    "Using when git_diff would be better (to see changes)",
                    "Not specifying directory parameter",
                ],
                related_tools=["git_diff", "git_log", "git_branch"],
                examples=[
                    "git_status(directory='.')",
                ],
            ),
            "git_diff": ToolCapability(
                tool_name="git_diff",
                use_cases=[
                    "Seeing code changes",
                    "Reviewing modifications",
                    "Understanding what changed",
                ],
                limitations=[
                    "Only shows unstaged changes by default",
                    "May be verbose for many changes",
                ],
                common_mistakes=[
                    "Forgetting to use cached=true for staged changes",
                    "Not limiting to specific files when needed",
                ],
                related_tools=["git_status", "git_log"],
                examples=[
                    "git_diff(directory='.', cached=false)",
                    "git_diff(directory='.', file_path='src/main.py')",
                ],
            ),
        }

        return capabilities

    def _build_parameter_validators(self) -> Dict[str, Any]:
        """Build parameter validation rules.

        Returns:
            Dictionary of validation rules per tool
        """
        validators = {
            "read_file": {
                "file_path": {"type": "string", "required": True, "must_exist": False},
                "start_line": {"type": "integer", "min": 1},
                "end_line": {"type": "integer", "min": 1},
            },
            "write_file": {
                "file_path": {"type": "string", "required": True},
                "content": {"type": "string", "required": True},
            },
            "list_directory": {
                "directory_path": {"type": "string", "required": True},
            },
            "search_files": {
                "pattern": {"type": "string", "required": True},
                "directory": {"type": "string", "required": True},
            },
            "execute_command": {
                "command": {"type": "string", "required": True},
                "working_directory": {"type": "string"},
                "background": {"type": "boolean"},
            },
            "delete_file": {
                "file_path": {"type": "string", "required": True},
            },
        }

        return validators

    def validate_tool_call(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> ToolValidationResult:
        """Validate a tool call before execution.

        Args:
            tool_name: Name of the tool to call
            arguments: Arguments for the tool

        Returns:
            ToolValidationResult with validation details
        """
        errors = []
        warnings = []
        suggestions = []
        corrected_arguments = None

        # Check if tool exists
        if tool_name not in self.available_tools:
            return ToolValidationResult(
                status=ValidationStatus.INVALID,
                is_valid=False,
                errors=[f"Unknown tool: {tool_name}"],
                warnings=[],
                suggestions=[],
                corrected_arguments=None,
            )

        # Get validation rules for this tool
        if tool_name not in self.parameter_validators:
            # No specific validators, assume valid
            return ToolValidationResult(
                status=ValidationStatus.VALID,
                is_valid=True,
                errors=[],
                warnings=[],
                suggestions=[],
                corrected_arguments=None,
            )

        validators = self.parameter_validators[tool_name]

        # Check required parameters
        for param_name, rules in validators.items():
            if rules.get("required", False) and param_name not in arguments:
                errors.append(f"Missing required parameter: {param_name}")
                suggestions.append(
                    ParameterSuggestion(
                        parameter_name=param_name,
                        current_value=None,
                        suggested_value=None,
                        reason=f"{param_name} is required for {tool_name}",
                        example=self._get_example_value(tool_name, param_name),
                    )
                )

        # Validate parameter types and values
        for param_name, param_value in arguments.items():
            if param_name not in validators:
                warnings.append(f"Unknown parameter: {param_name}")
                continue

            rules = validators[param_name]

            # Type checking
            expected_type = rules.get("type")
            if expected_type:
                type_valid, type_error = self._validate_type(
                    param_value, expected_type
                )
                if not type_valid:
                    errors.append(
                        f"Parameter '{param_name}': {type_error}"
                    )

            # Range checking for integers
            if expected_type == "integer" and isinstance(param_value, int):
                min_val = rules.get("min")
                max_val = rules.get("max")
                if min_val is not None and param_value < min_val:
                    errors.append(
                        f"Parameter '{param_name}' must be >= {min_val}"
                    )
                if max_val is not None and param_value > max_val:
                    errors.append(
                        f"Parameter '{param_name}' must be <= {max_val}"
                    )

        # Determine overall status
        if errors:
            status = ValidationStatus.MISSING_REQUIRED if any(
                "Missing required" in e for e in errors
            ) else ValidationStatus.INVALID
            is_valid = False
        else:
            status = ValidationStatus.VALID
            is_valid = True

        return ToolValidationResult(
            status=status,
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
            corrected_arguments=corrected_arguments,
        )

    def _validate_type(self, value: Any, expected_type: str) -> Tuple[bool, str]:
        """Validate that a value matches the expected type.

        Args:
            value: Value to validate
            expected_type: Expected type string

        Returns:
            Tuple of (is_valid, error_message)
        """
        type_map = {
            "string": str,
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict,
        }

        if expected_type not in type_map:
            return True, ""

        expected_python_type = type_map[expected_type]
        if not isinstance(value, expected_python_type):
            return False, f"expected {expected_type}, got {type(value).__name__}"

        return True, ""

    def _get_example_value(self, tool_name: str, param_name: str) -> str:
        """Get an example value for a parameter.

        Args:
            tool_name: Tool name
            param_name: Parameter name

        Returns:
            Example value string
        """
        examples = {
            ("read_file", "file_path"): "read_file(file_path='src/main.py')",
            ("write_file", "file_path"): "write_file(file_path='output.txt', content='...')",
            ("write_file", "content"): "write_file(file_path='output.txt', content='Hello world')",
            ("list_directory", "directory_path"): "list_directory(directory_path='src')",
            ("search_files", "pattern"): "search_files(pattern='*.py', directory='src')",
            ("execute_command", "command"): "execute_command(command='pytest tests/')",
        }

        return examples.get((tool_name, param_name), f"{tool_name}(...)")

    def suggest_tool_for_task(self, task_description: str) -> List[str]:
        """Suggest appropriate tools for a task.

        Args:
            task_description: Description of what needs to be done

        Returns:
            List of suggested tool names
        """
        task_lower = task_description.lower()
        suggestions = []

        # Simple keyword matching (could be enhanced with LLM)
        if any(word in task_lower for word in ["read", "view", "show", "see", "display"]):
            if "directory" in task_lower or "folder" in task_lower:
                suggestions.append("list_directory")
            elif "file" in task_lower:
                suggestions.append("read_file")

        if any(word in task_lower for word in ["write", "create", "generate"]):
            suggestions.append("write_file")

        if any(word in task_lower for word in ["find", "search", "locate"]):
            suggestions.append("search_files")

        if any(word in task_lower for word in ["run", "execute", "test", "build"]):
            suggestions.append("execute_command")

        if any(word in task_lower for word in ["git", "commit", "status", "diff"]):
            if "status" in task_lower:
                suggestions.append("git_status")
            elif "diff" in task_lower or "change" in task_lower:
                suggestions.append("git_diff")
            elif "log" in task_lower or "history" in task_lower:
                suggestions.append("git_log")

        return suggestions

    def get_tool_guidance(self, tool_name: str) -> Optional[ToolCapability]:
        """Get guidance for a specific tool.

        Args:
            tool_name: Name of the tool

        Returns:
            ToolCapability with usage guidance, or None if tool unknown
        """
        return self.tool_capabilities.get(tool_name)

    def format_validation_error_message(
        self, validation_result: ToolValidationResult, tool_name: str
    ) -> str:
        """Format a validation error message for the LLM.

        Args:
            validation_result: Validation result
            tool_name: Tool name

        Returns:
            Formatted error message
        """
        if validation_result.is_valid:
            return ""

        message = f"[TOOL VALIDATION ERROR] {tool_name} call has issues:\n\n"

        if validation_result.errors:
            message += "Errors:\n"
            for error in validation_result.errors:
                message += f"  • {error}\n"

        if validation_result.warnings:
            message += "\nWarnings:\n"
            for warning in validation_result.warnings:
                message += f"  • {warning}\n"

        if validation_result.suggestions:
            message += "\nSuggestions:\n"
            for suggestion in validation_result.suggestions:
                message += f"  • {suggestion.reason}\n"
                message += f"    Example: {suggestion.example}\n"

        # Add tool guidance
        capability = self.get_tool_guidance(tool_name)
        if capability:
            message += f"\nTool Usage Guide for '{tool_name}':\n"
            message += f"  Use cases: {', '.join(capability.use_cases[:3])}\n"
            if capability.common_mistakes:
                message += f"  Common mistakes: {capability.common_mistakes[0]}\n"

        return message
