"""Conversation manager for handling chat sessions with tool execution."""

import json
import difflib
import time
from typing import Optional, List, Dict, Any
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text
from rich.spinner import Spinner

from hrisa_code.core.ollama_client import OllamaClient, OllamaConfig
from hrisa_code.core.loop_detector import LoopDetector, LoopStatus
from hrisa_code.core.goal_tracker import GoalTracker, GoalStatus
from hrisa_code.core.approval_manager import (
    ApprovalManager,
    ApprovalType,
    create_file_write_request,
    create_file_delete_request,
    create_command_request,
    create_git_commit_request,
    create_git_push_request,
)
from hrisa_code.tools.file_operations import AVAILABLE_TOOLS, get_all_tool_definitions


class ConversationManager:
    """Manages conversation flow and tool execution."""

    def __init__(
        self,
        ollama_config: OllamaConfig,
        working_directory: Path,
        system_prompt: Optional[str] = None,
        enable_tools: bool = True,
        task_manager=None,
        auto_approve: bool = False,
    ):
        """Initialize the conversation manager.

        Args:
            ollama_config: Configuration for Ollama client
            working_directory: Working directory for file operations
            system_prompt: Optional system prompt
            enable_tools: Whether to enable tool calling (some models don't support it)
            task_manager: Optional TaskManager for background execution
            auto_approve: If True, automatically approve all operations (for testing)
        """
        self.ollama_client = OllamaClient(ollama_config)
        self.working_directory = working_directory
        self.system_prompt = system_prompt or self._get_default_system_prompt()
        self.console = Console()
        self.enable_tools = enable_tools
        self.tool_definitions = get_all_tool_definitions() if enable_tools else None
        self.task_manager = task_manager

        # Track last tool execution results for error recovery
        self.last_tool_results: list[dict] = []
        self.last_tools_had_errors: bool = False

        # Loop detection to prevent unproductive repeated tool calls
        self.loop_detector = LoopDetector(
            max_identical_calls=3,
            warning_threshold=2,
            history_window=10
        )

        # Goal tracking to detect task completion
        # Use the same model as the main conversation (no need for separate evaluation model)
        self.goal_tracker = GoalTracker(
            ollama_client=self.ollama_client,
            evaluation_model=ollama_config.model,  # Use main model
            check_frequency=3  # Check every 3 rounds
        )

        # Approval manager for write operations
        self.approval_manager = ApprovalManager(auto_approve=auto_approve)

    def _extract_tool_calls_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract tool calls from text response (for models that output JSON as text).

        Some models like qwen2.5-coder:32b output tool calls as JSON text instead of
        using Ollama's structured tool calling API. This function extracts those calls.

        Args:
            text: Response text that may contain JSON tool calls

        Returns:
            List of tool calls in Ollama's expected format
        """
        import re

        tool_calls = []

        # Pattern to match JSON objects with "name" and "arguments" keys
        # This handles the format: {"name": "tool_name", "arguments": {...}}
        # Using a more flexible pattern to handle nested braces in arguments
        pattern = r'\{\s*"name"\s*:\s*"([^"]+)"\s*,\s*"arguments"\s*:\s*(\{[^}]*(?:\{[^}]*\}[^}]*)*\})\s*\}'

        matches = re.finditer(pattern, text, re.DOTALL)

        for match in matches:
            try:
                # Extract the full JSON string
                json_str = match.group(0)
                parsed = json.loads(json_str)

                # Validate it has the expected structure
                if "name" in parsed and "arguments" in parsed:
                    # Verify the tool exists in our tool definitions
                    if parsed["name"] in AVAILABLE_TOOLS:
                        # Convert to Ollama's tool call format
                        tool_calls.append({
                            "function": {
                                "name": parsed["name"],
                                "arguments": parsed["arguments"]
                            }
                        })
                        self.console.print(f"[dim]→ Detected text-based tool call: {parsed['name']}[/dim]")
            except (json.JSONDecodeError, KeyError) as e:
                # Skip malformed JSON
                self.console.print(f"[dim]→ Skipped malformed tool call: {e}[/dim]")
                continue

        return tool_calls

    def _get_default_system_prompt(self) -> str:
        """Get the default system prompt.

        Returns:
            Default system prompt
        """
        return f"""You are a helpful coding assistant running locally. You have access to various tools to help with coding tasks.

Current working directory: {self.working_directory}

CRITICAL PATH RULES:
- ALWAYS use relative paths (e.g., "README.md", "src/main.py") or absolute paths starting with {self.working_directory}
- NEVER use placeholder paths like "/path/to/file" or "/path/to/directory"
- All file operations are relative to the working directory above
- If a file is not found, try different locations or ask the user for the correct path

Available tools:
- read_file(file_path, start_line?, end_line?): Read file contents
- write_file(file_path, content): Write content to files
- list_directory(directory_path, recursive?): List ALL files/dirs in a directory (NO file_pattern parameter!)
- search_files(pattern, directory, file_pattern?): Search for text INSIDE files, optionally filter by file_pattern like "*.py"
- execute_command(command, background?): Execute shell commands (working_directory is automatically set - DO NOT provide it)
  - Set background=true for long-running operations (tests, builds, dev servers) to run asynchronously
  - Returns task ID immediately when background=true - tell user to check status with /task <id>

CRITICAL TOOL USAGE RULES:
1. To list files by pattern (*.py, *.js, etc.): Use execute_command with "ls *.py" or "find . -name '*.py'"
2. list_directory does NOT support file_pattern - it lists EVERYTHING in a directory
3. search_files is for searching TEXT INSIDE files, not for listing files by name
4. Use background=true for long-running commands to avoid blocking

EXAMPLES:
❌ WRONG: list_directory(directory_path=".", file_pattern="*.py")  # file_pattern doesn't exist!
❌ WRONG: execute_command(command="ls *.py", working_directory="/home/user/current_directory")  # NO placeholder paths!
✓ RIGHT: execute_command(command="ls *.py")  # working_directory is auto-set
✓ RIGHT: execute_command(command="find . -name '*.py'")
✓ RIGHT: execute_command(command="pytest tests/", background=true)  # Long-running test in background

Guidelines:
1. Use tools efficiently - avoid redundant tool calls
2. Don't read files you just created (you already know the content)
3. Don't verify operations unnecessarily (trust tool results)
4. Be concise and direct in your responses
5. When a tool fails, DON'T make up information or hallucinate - try a different approach or ask the user
6. Focus on solving the user's problem with real tool results, not invented content
7. Use background=true for commands that take >5 seconds:
   - Test suites: pytest, npm test, cargo test
   - Build commands: npm run build, cargo build, make
   - Dev servers: npm start, python -m http.server
   - Long operations: Large file processing, database migrations

The system automatically handles:
- Confirmations for destructive operations (don't ask yourself)
- Displaying tool calls and results to the user
- Error handling and retries

Your job: Choose the right tool with CORRECT paths, use it once, respond clearly based on ACTUAL results."""

    def _is_destructive_operation(self, tool_name: str, arguments: Dict[str, Any]) -> bool:
        """Check if a tool operation is potentially destructive.

        Args:
            tool_name: Name of the tool
            arguments: Tool arguments

        Returns:
            True if operation is destructive
        """
        # Write operations
        if tool_name == "write_file":
            file_path = Path(arguments.get("file_path", ""))
            # Destructive if file already exists
            return file_path.exists()

        # Command execution with dangerous patterns
        if tool_name == "execute_command":
            command = arguments.get("command", "").lower()
            dangerous_patterns = ["rm ", "del ", "delete", "rmdir", "format", "mkfs"]
            return any(pattern in command for pattern in dangerous_patterns)

        return False

    def _get_confirmation_message(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Get a confirmation message for a destructive operation.

        Args:
            tool_name: Name of the tool
            arguments: Tool arguments

        Returns:
            Confirmation message
        """
        if tool_name == "write_file":
            file_path = arguments.get("file_path", "")
            return f"[WARNING] File '{file_path}' already exists. Overwrite it?"

        if tool_name == "execute_command":
            command = arguments.get("command", "")
            return f"[WARNING] Execute potentially destructive command: '{command}'?"

        return "[WARNING] This operation may be destructive. Continue?"

    async def _check_approval(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[str]:
        """Check if operation requires approval and request it (async).

        Args:
            tool_name: Name of the tool
            arguments: Tool arguments

        Returns:
            Error message if operation denied, None if approved or doesn't need approval
        """
        # Check write_file operations
        if tool_name == "write_file":
            file_path = arguments.get("file_path", "")
            new_content = arguments.get("content", "")

            # Check if file exists (overwrite case)
            path = Path(file_path)
            old_content = None
            if path.exists():
                try:
                    old_content = path.read_text()
                except Exception:
                    pass  # If can't read, treat as new file

            # Create approval request
            request = create_file_write_request(
                file_path=file_path,
                new_content=new_content,
                old_content=old_content
            )

            # Request approval (await async call)
            if not await self.approval_manager.is_approved(request):
                return f"[DENIED] User denied write operation to: {file_path}"

        # Check delete_file operations
        elif tool_name == "delete_file":
            file_path = arguments.get("file_path", "")

            # Create approval request
            request = create_file_delete_request(file_path=file_path)

            # Request approval (await async call)
            if not await self.approval_manager.is_approved(request):
                return f"[DENIED] User denied delete operation for: {file_path}"

        # Check destructive commands
        elif tool_name == "execute_command":
            command = arguments.get("command", "")
            if self._is_command_destructive(command):
                request = create_command_request(command)

                if not await self.approval_manager.is_approved(request):
                    return f"[DENIED] User denied destructive command: {command}"

        # Check git_commit operations
        elif tool_name == "git_commit":
            message = arguments.get("message", "")
            directory = arguments.get("directory", str(self.working_directory))

            # Get list of files that will be committed
            # Try to get staged files, fall back to status if needed
            files = self._get_staged_files(directory)

            # Create approval request
            request = create_git_commit_request(message=message, files=files)

            if not await self.approval_manager.is_approved(request):
                return f"[DENIED] User denied git commit"

        # Check git_push operations
        elif tool_name == "git_push":
            remote = arguments.get("remote", "origin")
            branch = arguments.get("branch", self._get_current_branch(arguments.get("directory", str(self.working_directory))))

            # Create approval request
            request = create_git_push_request(branch=branch, remote=remote)

            if not await self.approval_manager.is_approved(request):
                return f"[DENIED] User denied git push to {remote}/{branch}"

        # Check git_pull operations
        elif tool_name == "git_pull":
            remote = arguments.get("remote", "origin")
            branch = arguments.get("branch", "")
            directory = arguments.get("directory", str(self.working_directory))

            # Create approval request using ApprovalRequest directly
            from hrisa_code.core.approval_manager import ApprovalRequest
            request = ApprovalRequest(
                operation_type=ApprovalType.GIT_PULL,
                description=f"Pull changes from {remote}",
                details={
                    "Remote": remote,
                    "Branch": branch if branch else "current branch",
                    "Warning": "This will merge remote changes into your local branch!"
                },
                command=f"git pull {remote} {branch}".strip()
            )

            if not await self.approval_manager.is_approved(request):
                return f"[DENIED] User denied git pull from {remote}"

        # Check git_stash operations
        elif tool_name == "git_stash":
            action = arguments.get("action", "save")

            # Only require approval for write operations (not list)
            if action != "list":
                from hrisa_code.core.approval_manager import ApprovalRequest

                if action == "save":
                    message = arguments.get("message", "")
                    description = f"Stash uncommitted changes"
                    details = {
                        "Action": "Save stash",
                        "Message": message if message else "(no message)",
                        "Warning": "This will clear your working directory!"
                    }
                elif action in ["pop", "apply"]:
                    stash_index = arguments.get("stash_index", 0)
                    description = f"{action.capitalize()} stashed changes"
                    details = {
                        "Action": f"{action.capitalize()} stash",
                        "Stash": f"stash@{{{stash_index}}}",
                        "Warning": f"This will apply stashed changes to your working directory!"
                    }
                elif action == "drop":
                    stash_index = arguments.get("stash_index", 0)
                    description = f"Drop stashed changes"
                    details = {
                        "Action": "Drop stash",
                        "Stash": f"stash@{{{stash_index}}}",
                        "Warning": "This operation cannot be undone!"
                    }
                else:
                    # Unknown action, still require approval
                    description = f"Execute git stash {action}"
                    details = {"Action": action}

                request = ApprovalRequest(
                    operation_type=ApprovalType.GIT_STASH,
                    description=description,
                    details=details,
                    command=f"git stash {action}"
                )

                if not await self.approval_manager.is_approved(request):
                    return f"[DENIED] User denied git stash {action}"

        return None

    def _is_command_destructive(self, command: str) -> bool:
        """Check if a command is potentially destructive.

        Args:
            command: Command to check

        Returns:
            True if command is destructive
        """
        command_lower = command.lower()
        dangerous_patterns = ["rm ", "del ", "delete", "rmdir", "format", "mkfs", "truncate", ">"]
        return any(pattern in command_lower for pattern in dangerous_patterns)

    def _get_staged_files(self, directory: str) -> List[str]:
        """Get list of staged files in git repository.

        Args:
            directory: Directory of the git repository

        Returns:
            List of staged file paths
        """
        import subprocess

        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                capture_output=True,
                text=True,
                cwd=directory,
                timeout=5,
            )

            if result.returncode == 0 and result.stdout.strip():
                files = result.stdout.strip().split("\n")
                return [f.strip() for f in files if f.strip()]

            # If no staged files, get all modified files
            result = subprocess.run(
                ["git", "status", "--short"],
                capture_output=True,
                text=True,
                cwd=directory,
                timeout=5,
            )

            if result.returncode == 0 and result.stdout.strip():
                # Parse git status short format
                files = []
                for line in result.stdout.strip().split("\n"):
                    if line.strip():
                        # Format is "XY filename" where X and Y are status codes
                        parts = line.strip().split(maxsplit=1)
                        if len(parts) >= 2:
                            files.append(parts[1])
                return files if files else ["(no files)"]

            return ["(no files)"]

        except Exception:
            return ["(unknown files)"]

    def _get_current_branch(self, directory: str) -> str:
        """Get current git branch name.

        Args:
            directory: Directory of the git repository

        Returns:
            Current branch name or "unknown"
        """
        import subprocess

        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                cwd=directory,
                timeout=5,
            )

            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()

            return "unknown"

        except Exception:
            return "unknown"

    def _validate_path_arguments(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[str]:
        """Validate that path arguments are not placeholders.

        Args:
            tool_name: Name of the tool
            arguments: Tool arguments

        Returns:
            Error message if validation fails, None otherwise
        """
        # Placeholder patterns to reject
        placeholder_patterns = [
            "/path/to/",
            "/path/",
            "path/to/",
            "/home/user/",
            "/usr/local/",
            "<path>",
            "${path}",
        ]

        # Check file_path argument
        if "file_path" in arguments:
            file_path = str(arguments["file_path"])
            for pattern in placeholder_patterns:
                if pattern in file_path:
                    return (
                        f"Error: Placeholder path detected: '{file_path}'\n"
                        f"Use relative paths (e.g., 'src/main.py') or search for the file first.\n"
                        f"Working directory: {self.working_directory}"
                    )

        # Check directory argument
        if "directory" in arguments:
            directory = str(arguments["directory"])
            for pattern in placeholder_patterns:
                if pattern in directory:
                    return (
                        f"Error: Placeholder directory detected: '{directory}'\n"
                        f"Use relative paths (e.g., '.', 'src/') or actual paths.\n"
                        f"Working directory: {self.working_directory}"
                    )

        # Check working_directory argument
        if "working_directory" in arguments:
            working_dir = str(arguments["working_directory"])
            for pattern in placeholder_patterns:
                if pattern in working_dir:
                    return (
                        f"Error: Placeholder working_directory detected: '{working_dir}'\n"
                        f"Do NOT provide working_directory - it's set automatically.\n"
                        f"Current working directory: {self.working_directory}"
                    )

        return None

    async def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute a tool with given arguments (async).

        Args:
            tool_name: Name of the tool to execute
            arguments: Arguments for the tool

        Returns:
            Tool execution result
        """
        if tool_name not in AVAILABLE_TOOLS:
            return f"Error: Unknown tool '{tool_name}'"

        # Validate path arguments
        validation_error = self._validate_path_arguments(tool_name, arguments)
        if validation_error:
            return validation_error

        # Check for approval on write operations (await async call)
        approval_result = await self._check_approval(tool_name, arguments)
        if approval_result:
            return approval_result  # Return denial message if not approved

        # Handle background execution for execute_command
        # Parse background parameter properly (handle both boolean and string values)
        background = arguments.get("background", False)
        if isinstance(background, str):
            background = background.lower() in ("true", "1", "yes")

        if tool_name == "execute_command" and background:
            if not self.task_manager:
                return "Error: Background execution not available (TaskManager not initialized)"

            # Extract command - always use actual working directory, ignore any provided one
            command = arguments.get("command", "")

            # Create background task (TaskManager already uses self.working_directory)
            try:
                task = self.task_manager.create_task(command)

                return (
                    f"[BACKGROUND TASK] Command started in background\n"
                    f"Task ID: {task.task_id}\n"
                    f"PID: {task.pid}\n"
                    f"Command: {command}\n\n"
                    f"Use /task {task.task_id} to view output\n"
                    f"Use /tasks to list all background tasks"
                )
            except Exception as e:
                return f"Error starting background task: {str(e)}"

        tool_class = AVAILABLE_TOOLS[tool_name]

        # Add working directory context for relevant tools
        if tool_name in ["execute_command"] and "working_directory" not in arguments:
            arguments["working_directory"] = str(self.working_directory)

        # Remove background flag before passing to tool (it's handled above)
        if "background" in arguments:
            arguments = {k: v for k, v in arguments.items() if k != "background"}

        try:
            result = tool_class.execute(**arguments)
            return result
        except Exception as e:
            return f"Error executing tool '{tool_name}': {str(e)}"

    def _display_diff(self, file_path: str, old_content: str, new_content: str) -> None:
        """Display a git-style diff for file changes with enhanced styling.

        Args:
            file_path: Path to the file being changed
            old_content: Original file content
            new_content: New file content
        """
        old_lines = old_content.splitlines(keepends=False) if old_content else []
        new_lines = new_content.splitlines(keepends=False)

        # Generate unified diff
        diff_lines = list(difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
            lineterm=''
        ))

        if not diff_lines:
            # No changes
            return

        # Format diff with enhanced colors (Claude Code style)
        diff_text = Text()
        line_count = 0
        max_lines = 50

        for line in diff_lines:
            if line_count >= max_lines:
                diff_text.append(f"\n... ({len(diff_lines) - max_lines} more lines)\n", style="yellow dim")
                break

            if line.startswith('---') or line.startswith('+++'):
                # File headers in bold
                diff_text.append(line + '\n', style="bold cyan")
            elif line.startswith('@@'):
                # Hunk headers in cyan with background
                diff_text.append(line + '\n', style="bold cyan on #1a1a1a")
            elif line.startswith('-'):
                # Removed lines: red text
                diff_text.append(line + '\n', style="bold red")
            elif line.startswith('+'):
                # Added lines: green text
                diff_text.append(line + '\n', style="bold green")
            else:
                # Context lines in dim white
                diff_text.append(line + '\n', style="dim")

            line_count += 1

        # Calculate stats
        additions = sum(1 for line in diff_lines if line.startswith('+') and not line.startswith('+++'))
        deletions = sum(1 for line in diff_lines if line.startswith('-') and not line.startswith('---'))

        title = f"► File Changes: {file_path}"
        if additions > 0 or deletions > 0:
            title += f" (+{additions} -{deletions})"

        self.console.print(
            Panel(
                diff_text,
                title=title,
                border_style="yellow",
                padding=(0, 1)
            )
        )

    def _display_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> None:
        """Display a tool call to the user.

        Args:
            tool_name: Name of the tool
            arguments: Tool arguments
        """
        self.console.print(
            Panel(
                f"[bold cyan]Tool:[/bold cyan] {tool_name}\n"
                f"[bold cyan]Arguments:[/bold cyan] {json.dumps(arguments, indent=2)}",
                title="► Tool Call",
                border_style="cyan",
            )
        )

    def _display_tool_result(self, result: str, tool_name: str = "", execution_time: float = 0.0, file_path: str = "") -> None:
        """Display a tool result to the user with enhanced formatting.

        Args:
            result: Tool execution result
            tool_name: Name of the tool that was executed
            execution_time: Time taken to execute the tool in seconds
            file_path: Optional file path for syntax highlighting
        """
        # Determine if result indicates success or error
        is_error = result.startswith("Error") or "failed" in result.lower()
        border_color = "red" if is_error else "green"
        status = "[ERROR]" if is_error else "[OK]"

        # Extract metadata based on tool type and result
        metadata_parts = []

        # Add execution time if available
        if execution_time > 0:
            metadata_parts.append(f"{execution_time:.2f}s")

        # Analyze result for metadata
        if tool_name == "read_file" and not is_error:
            lines = result.count('\n')
            chars = len(result)
            metadata_parts.extend([f"{chars} chars", f"{lines} lines"])
        elif tool_name == "write_file" and not is_error:
            metadata_parts.append("File written")
        elif tool_name == "list_directory" and not is_error:
            items = result.count('\n')
            metadata_parts.append(f"{items} items")
        elif tool_name == "execute_command" and not is_error:
            metadata_parts.append("Command executed")

        # Build title with metadata
        title_parts = [f"{status} Tool Result"]
        if metadata_parts:
            title_parts.append(f"({', '.join(metadata_parts)})")
        title = " ".join(title_parts)

        # Truncate very long results but show more than before
        if len(result) > 2000:
            display_result = result[:2000] + f"\n\n... (truncated, {len(result) - 2000} more chars)"
        else:
            display_result = result

        # Apply syntax highlighting for code files
        content_to_display = display_result
        if tool_name == "read_file" and not is_error and file_path:
            # Detect language from file extension
            file_ext = Path(file_path).suffix.lstrip('.')
            if file_ext:  # If we have an extension, try syntax highlighting
                try:
                    syntax = Syntax(
                        display_result,
                        file_ext,
                        theme="monokai",
                        line_numbers=True,
                        word_wrap=False,
                    )
                    content_to_display = syntax
                except Exception:
                    # If syntax highlighting fails, fall back to plain text
                    pass

        self.console.print(
            Panel(
                content_to_display,
                title=title,
                border_style=border_color,
            )
        )

    async def process_message(self, user_message: str, max_tool_rounds: int = 20) -> str:
        """Process a user message and handle any tool calls (Claude Code style).

        This implements Claude Code-style behavior where the LLM can make multiple
        rounds of tool calls within a single conversation turn, allowing autonomous
        multi-step task completion.

        Args:
            user_message: The user's message
            max_tool_rounds: Maximum tool calling rounds (default: 20)

        Returns:
            The assistant's response
        """

    async def process_message(self, user_message: str, max_tool_rounds: int = 20) -> str:
        """Process a user message and handle any tool calls (Claude Code style).

        This implements Claude Code-style behavior where the LLM can make multiple
        rounds of tool calls within a single conversation turn, allowing autonomous
        multi-step task completion.

        Args:
            user_message: The user's message
            max_tool_rounds: Maximum tool calling rounds (default: 20)

        Returns:
            The assistant's response
        """
        # Reset tool tracking
        self.last_tool_results = []
        self.last_tools_had_errors = False

        # Reset loop detector for new conversation turn
        self.loop_detector.reset()

        # Reset goal tracker and set user question
        self.goal_tracker.reset()
        self.goal_tracker.set_user_question(user_message)

        # Get initial response from LLM
        start_time = time.time()
        with self.console.status("[bold blue]Thinking...[/bold blue]", spinner="dots"):
            raw_response = await self.ollama_client.chat_raw(
                message=user_message,
                system_prompt=self.system_prompt,
                tools=self.tool_definitions if self.enable_tools else None,
            )
        elapsed = time.time() - start_time
        if elapsed > 0.5:
            self.console.print(f"[dim]Thought for {elapsed:.1f}s[/dim]")

        # Multi-turn tool calling loop (Claude Code style)
        tool_round = 0
        while tool_round < max_tool_rounds:
            # Check for structured tool calls (normal Ollama API format)
            has_structured_tool_calls = bool(raw_response.get("message", {}).get("tool_calls"))

            # If no structured tool calls, check for text-based tool calls
            # (for models like qwen2.5-coder:32b that output JSON as text)
            if not has_structured_tool_calls and self.enable_tools:
                content = raw_response.get("message", {}).get("content", "")
                if content:
                    extracted_tool_calls = self._extract_tool_calls_from_text(content)
                    if extracted_tool_calls:
                        # Inject extracted tool calls into raw_response
                        if "message" not in raw_response:
                            raw_response["message"] = {}
                        raw_response["message"]["tool_calls"] = extracted_tool_calls
                        has_structured_tool_calls = True

            # Exit loop if no tool calls found
            if not has_structured_tool_calls:
                break
            tool_round += 1

            if tool_round > 1:
                self.console.print(f"[dim]→ Tool round {tool_round}[/dim]")

            # Increment round counters for both trackers
            self.loop_detector.next_round()
            self.goal_tracker.next_round()

            tool_calls = raw_response["message"]["tool_calls"]

            # Execute each tool call
            tool_results = []
            for tool_call in tool_calls:
                function = tool_call.get("function", {})
                tool_name = function.get("name")
                arguments = function.get("arguments", {})

                # Check for loops before executing
                loop_status = self.loop_detector.check_loop(tool_name, arguments)

                # Handle loop detection
                if loop_status in (LoopStatus.WARNING, LoopStatus.DETECTED):
                    intervention_msg = self.loop_detector.get_intervention_message(
                        tool_name, arguments, loop_status
                    )

                    # Display warning/intervention to user
                    style = "yellow" if loop_status == LoopStatus.WARNING else "red bold"
                    self.console.print(f"\n[{style}]{intervention_msg}[/{style}]\n")

                    if loop_status == LoopStatus.DETECTED:
                        # Add intervention message as a system/tool result
                        tool_results.append({
                            "tool_call_id": tool_call.get("id", ""),
                            "role": "tool",
                            "content": intervention_msg,
                        })

                        # Skip this tool execution and let LLM respond to intervention
                        continue

                # Add this call to history (after loop check, so we track what we execute)
                self.loop_detector.add_call(tool_name, arguments)

                # Check if operation needs confirmation
                if self._is_destructive_operation(tool_name, arguments):
                    confirmation_msg = self._get_confirmation_message(tool_name, arguments)
                    self.console.print(f"\n[yellow]{confirmation_msg}[/yellow]")

                    # Get user confirmation using selection interface
                    import questionary

                    response = await questionary.select(
                        "What would you like to do?",
                        choices=["Continue", "Cancel"],
                        style=questionary.Style([
                            ("selected", "fg:cyan bold"),
                            ("pointer", "fg:cyan bold"),
                        ])
                    ).ask_async()

                    if response != "Continue":
                        result = "[CANCELLED] Operation cancelled by user"
                        self._display_tool_result(result, tool_name)
                        tool_results.append({
                            "tool_call_id": tool_call.get("id", ""),
                            "role": "tool",
                            "content": result,
                        })
                        continue

                # Display tool call to user
                self._display_tool_call(tool_name, arguments)

                # Show diff for write_file operations
                if tool_name == "write_file":
                    file_path_arg = arguments.get("file_path", "")
                    new_content = arguments.get("content", "")
                    if file_path_arg:
                        try:
                            path = Path(file_path_arg)
                            old_content = path.read_text() if path.exists() else ""
                            self._display_diff(file_path_arg, old_content, new_content)
                        except Exception:
                            # If diff fails, just continue with the write
                            pass

                # Execute the tool with timing and custom spinner
                tool_start = time.time()

                # Choose spinner based on tool type
                spinner_style = "line" if tool_name == "execute_command" else "arc"

                with self.console.status(
                    f"[bold cyan]Executing {tool_name}...[/bold cyan]",
                    spinner=spinner_style
                ):
                    result = await self._execute_tool(tool_name, arguments)

                execution_time = time.time() - tool_start

                # Display result to user with metadata
                file_path = arguments.get("file_path", "") if tool_name == "read_file" else ""
                self._display_tool_result(result, tool_name, execution_time, file_path)

                # Track tool result for error recovery
                tool_result_data = {
                    "tool_call_id": tool_call.get("id", ""),
                    "role": "tool",
                    "content": result,
                    "tool_name": tool_name,
                    "arguments": arguments,
                    "had_error": result.startswith("Error") or "failed" in result.lower(),
                }
                tool_results.append(tool_result_data)
                self.last_tool_results.append(tool_result_data)

                # Track if any tool had errors
                if tool_result_data["had_error"]:
                    self.last_tools_had_errors = True

                # Add to goal tracker for progress evaluation
                self.goal_tracker.add_tool_result(
                    tool_name=tool_name,
                    arguments=arguments,
                    result=result,
                    had_error=tool_result_data["had_error"]
                )

            # Check if status was immediately set to COMPLETE (e.g., user denial)
            # This takes precedence over periodic checks
            goal_status = self.goal_tracker.current_status

            # Otherwise, check goal progress periodically using LLM evaluation
            if goal_status == GoalStatus.UNKNOWN and self.goal_tracker.should_check_progress():
                goal_status = await self.goal_tracker.check_progress()

            # Handle intervention for any detected status (immediate or periodic)
            if goal_status in (GoalStatus.COMPLETE, GoalStatus.STUCK, GoalStatus.CLARIFICATION_NEEDED):
                intervention_msg = self.goal_tracker.get_intervention_message(goal_status)

                # Display intervention to user
                style = "green bold" if goal_status == GoalStatus.COMPLETE else "yellow"
                self.console.print(f"\n[{style}]{intervention_msg}[/{style}]\n")

                # Add intervention as tool result if goal is complete or stuck
                if goal_status in (GoalStatus.COMPLETE, GoalStatus.STUCK):
                    tool_results.append({
                        "tool_call_id": "",
                        "role": "tool",
                        "content": intervention_msg,
                    })

            # Send tool results back to LLM and check for more tool calls
            # If goal is COMPLETE, don't provide tools - force a final response
            tools_for_next_round = None if goal_status == GoalStatus.COMPLETE else self.tool_definitions

            response_start = time.time()
            with self.console.status(
                "[bold green]Generating response...[/bold green]",
                spinner="dots2"
            ):
                raw_response = await self.ollama_client.chat_with_tools_result_raw(
                    tool_results=tool_results,
                    system_prompt=self.system_prompt,
                    tools=tools_for_next_round,
                )
            response_time = time.time() - response_start
            if response_time > 0.5:
                self.console.print(f"[dim]Generated response in {response_time:.1f}s[/dim]")

            # Loop continues if raw_response has more tool_calls

        # Exited loop - either no more tool calls or hit max rounds
        if tool_round >= max_tool_rounds:
            self.console.print(
                f"[yellow]Reached max tool rounds ({max_tool_rounds})[/yellow]"
            )

        # Return final text response
        return raw_response.get("message", {}).get("content", "")

    async def process_message_stream(self, user_message: str) -> None:
        """Process a user message and stream the response.

        Args:
            user_message: The user's message
        """
        # For tool-enabled mode, use non-streaming to handle tool calls properly
        # Streaming + tool calling is complex because we need complete tool call data
        if self.enable_tools and self.tool_definitions:
            response = await self.process_message(user_message)
            if response:
                self.console.print("[bold blue]Assistant:[/bold blue]")
                self.console.print(response)
        else:
            # No tools, can stream normally
            self.console.print("[bold blue]Assistant:[/bold blue]")

            full_response = ""
            async for chunk in self.ollama_client.chat_stream(
                message=user_message,
                system_prompt=self.system_prompt,
                tools=None,
            ):
                self.console.print(chunk, end="")
                full_response += chunk

            self.console.print()  # New line after response

    def clear_history(self) -> None:
        """Clear the conversation history."""
        self.ollama_client.clear_history()
        self.console.print("[yellow]Conversation history cleared[/yellow]")

    def save_conversation(self, file_path: Path) -> None:
        """Save the conversation to a file.

        Args:
            file_path: Path to save the conversation
        """
        conversation_data = {
            "messages": [msg.dict() for msg in self.ollama_client.conversation_history],
            "system_prompt": self.system_prompt,
            "working_directory": str(self.working_directory),
        }

        with open(file_path, "w") as f:
            json.dump(conversation_data, f, indent=2)

        self.console.print(f"[green]Conversation saved to {file_path}[/green]")

    def load_conversation(self, file_path: Path) -> None:
        """Load a conversation from a file.

        Args:
            file_path: Path to load the conversation from
        """
        with open(file_path, "r") as f:
            conversation_data = json.load(f)

        self.ollama_client.conversation_history = [
            self.ollama_client.Message(**msg) for msg in conversation_data["messages"]
        ]

        self.console.print(f"[green]Conversation loaded from {file_path}[/green]")

    def switch_model(self, model_name: str, verbose: bool = True) -> None:
        """Switch to a different model while preserving conversation history.

        Args:
            model_name: Name of the model to switch to
            verbose: Whether to print a message about the switch
        """
        old_model = self.ollama_client.get_current_model()
        self.ollama_client.switch_model(model_name)

        if verbose:
            self.console.print(
                f"[dim]→ Switched model: {old_model} → {model_name}[/dim]"
            )

    def get_current_model(self) -> str:
        """Get the currently active model name.

        Returns:
            Current model name
        """
        return self.ollama_client.get_current_model()
