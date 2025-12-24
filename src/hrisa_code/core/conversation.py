"""Conversation manager for handling chat sessions with tool execution."""

import json
from typing import Optional, List, Dict, Any
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax

from hrisa_code.core.ollama_client import OllamaClient, OllamaConfig
from hrisa_code.tools.file_operations import AVAILABLE_TOOLS, get_all_tool_definitions


class ConversationManager:
    """Manages conversation flow and tool execution."""

    def __init__(
        self,
        ollama_config: OllamaConfig,
        working_directory: Path,
        system_prompt: Optional[str] = None,
        enable_tools: bool = True,
    ):
        """Initialize the conversation manager.

        Args:
            ollama_config: Configuration for Ollama client
            working_directory: Working directory for file operations
            system_prompt: Optional system prompt
            enable_tools: Whether to enable tool calling (some models don't support it)
        """
        self.ollama_client = OllamaClient(ollama_config)
        self.working_directory = working_directory
        self.system_prompt = system_prompt or self._get_default_system_prompt()
        self.console = Console()
        self.enable_tools = enable_tools
        self.tool_definitions = get_all_tool_definitions() if enable_tools else None

    def _get_default_system_prompt(self) -> str:
        """Get the default system prompt.

        Returns:
            Default system prompt
        """
        return f"""You are a helpful coding assistant running locally. You have access to various tools to help with coding tasks.

Current working directory: {self.working_directory}

Available tools:
- read_file: Read file contents
- write_file: Write content to files
- list_directory: List directory contents
- execute_command: Execute shell commands
- search_files: Search for patterns in files

Guidelines:
1. Use tools efficiently - avoid redundant tool calls
2. Don't read files you just created (you already know the content)
3. Don't verify operations unnecessarily (trust tool results)
4. Be concise and direct in your responses
5. Focus on solving the user's problem, not explaining what you did

The system automatically handles:
- Confirmations for destructive operations (don't ask yourself)
- Displaying tool calls and results to the user
- Error handling and retries

Your job: Choose the right tool, use it once, respond clearly."""

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
            return f"⚠️  File '{file_path}' already exists. Overwrite it?"

        if tool_name == "execute_command":
            command = arguments.get("command", "")
            return f"⚠️  Execute potentially destructive command: '{command}'?"

        return "⚠️  This operation may be destructive. Continue?"

    def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute a tool with given arguments.

        Args:
            tool_name: Name of the tool to execute
            arguments: Arguments for the tool

        Returns:
            Tool execution result
        """
        if tool_name not in AVAILABLE_TOOLS:
            return f"Error: Unknown tool '{tool_name}'"

        tool_class = AVAILABLE_TOOLS[tool_name]

        # Add working directory context for relevant tools
        if tool_name in ["execute_command"] and "working_directory" not in arguments:
            arguments["working_directory"] = str(self.working_directory)

        try:
            result = tool_class.execute(**arguments)
            return result
        except Exception as e:
            return f"Error executing tool '{tool_name}': {str(e)}"

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
                title="🔧 Tool Call",
                border_style="cyan",
            )
        )

    def _display_tool_result(self, result: str) -> None:
        """Display a tool result to the user.

        Args:
            result: Tool execution result
        """
        # Truncate very long results
        display_result = result if len(result) < 1000 else result[:1000] + "\n... (truncated)"

        self.console.print(
            Panel(
                display_result,
                title="📋 Tool Result",
                border_style="green",
            )
        )

    async def process_message(self, user_message: str) -> str:
        """Process a user message and handle any tool calls.

        Args:
            user_message: The user's message

        Returns:
            The assistant's response
        """
        # Show thinking indicator
        with self.console.status("[bold blue]🤔 Thinking...[/bold blue]"):
            # Get initial response from LLM
            raw_response = await self.ollama_client.chat_raw(
                message=user_message,
                system_prompt=self.system_prompt,
                tools=self.tool_definitions if self.enable_tools else None,
            )

        # Check if the response includes tool calls
        if raw_response.get("message", {}).get("tool_calls"):
            tool_calls = raw_response["message"]["tool_calls"]

            # Execute each tool call
            tool_results = []
            for tool_call in tool_calls:
                function = tool_call.get("function", {})
                tool_name = function.get("name")
                arguments = function.get("arguments", {})

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
                        result = "❌ Operation cancelled by user"
                        self._display_tool_result(result)
                        tool_results.append({
                            "tool_call_id": tool_call.get("id", ""),
                            "role": "tool",
                            "content": result,
                        })
                        continue

                # Display tool call to user
                self._display_tool_call(tool_name, arguments)

                # Execute the tool with status indicator
                with self.console.status(f"[bold cyan]🔧 Executing {tool_name}...[/bold cyan]"):
                    result = self._execute_tool(tool_name, arguments)

                # Display result to user
                self._display_tool_result(result)

                tool_results.append({
                    "tool_call_id": tool_call.get("id", ""),
                    "role": "tool",
                    "content": result,
                })

            # Send tool results back to LLM for final response
            with self.console.status("[bold green]✨ Generating response...[/bold green]"):
                final_response = await self.ollama_client.chat_with_tools_result(
                    tool_results=tool_results,
                    system_prompt=self.system_prompt,
                )

            return final_response
        else:
            # No tool calls, return direct response
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
