"""Ollama client for interacting with local LLMs."""

from typing import AsyncIterator, Dict, List, Optional, Any
import ollama
from ollama import AsyncClient
from pydantic import BaseModel


class Message(BaseModel):
    """A message in the conversation."""

    role: str  # 'user', 'assistant', or 'system'
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None


class OllamaConfig(BaseModel):
    """Configuration for Ollama client."""

    model: str = "codellama"
    host: str = "http://localhost:11434"
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40


class OllamaClient:
    """Client for interacting with Ollama."""

    def __init__(self, config: OllamaConfig):
        """Initialize the Ollama client.

        Args:
            config: Configuration for the client
        """
        self.config = config
        self.client = AsyncClient(host=config.host)
        self.conversation_history: List[Message] = []

    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation history.

        Args:
            role: Role of the message sender ('user', 'assistant', 'system')
            content: Content of the message
        """
        self.conversation_history.append(Message(role=role, content=content))

    def clear_history(self) -> None:
        """Clear the conversation history."""
        self.conversation_history = []

    async def chat(
        self,
        message: str,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Send a chat message and get a response.

        Args:
            message: User message
            system_prompt: Optional system prompt
            tools: Optional list of tools for function calling

        Returns:
            Assistant's response
        """
        # Add user message to history
        self.add_message("user", message)

        # Prepare messages for Ollama
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # Add conversation history
        for msg in self.conversation_history:
            messages.append({"role": msg.role, "content": msg.content})

        # Make the request
        options = {
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "top_k": self.config.top_k,
        }

        # Try with tools first, fall back without tools if not supported
        try:
            response = await self.client.chat(
                model=self.config.model,
                messages=messages,
                tools=tools if tools else None,
                options=options,
            )
        except Exception as e:
            # If tools not supported, try without tools
            if "does not support tools" in str(e).lower() or "400" in str(e):
                response = await self.client.chat(
                    model=self.config.model,
                    messages=messages,
                    options=options,
                )
            else:
                raise

        # Extract response
        assistant_message = response.get("message", {}).get("content", "")
        if assistant_message:
            self.add_message("assistant", assistant_message)

        return assistant_message

    async def chat_stream(
        self,
        message: str,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> AsyncIterator[str]:
        """Send a chat message and stream the response.

        Args:
            message: User message
            system_prompt: Optional system prompt
            tools: Optional list of tools for function calling

        Yields:
            Chunks of the assistant's response
        """
        # Add user message to history
        self.add_message("user", message)

        # Prepare messages for Ollama
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # Add conversation history
        for msg in self.conversation_history:
            messages.append({"role": msg.role, "content": msg.content})

        # Make the streaming request
        options = {
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "top_k": self.config.top_k,
        }

        full_response = ""
        try:
            # Try with tools first
            async for chunk in await self.client.chat(
                model=self.config.model,
                messages=messages,
                tools=tools if tools else None,
                options=options,
                stream=True,
            ):
                if "message" in chunk and "content" in chunk["message"]:
                    content = chunk["message"]["content"]
                    full_response += content
                    yield content
        except Exception as e:
            # If tools not supported, try without tools
            if "does not support tools" in str(e).lower() or "400" in str(e):
                async for chunk in await self.client.chat(
                    model=self.config.model,
                    messages=messages,
                    options=options,
                    stream=True,
                ):
                    if "message" in chunk and "content" in chunk["message"]:
                        content = chunk["message"]["content"]
                        full_response += content
                        yield content
            else:
                raise

        # Add complete response to history
        self.add_message("assistant", full_response)

    async def chat_raw(
        self,
        message: str,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Send a chat message and get the raw response (including tool calls).

        Args:
            message: User message
            system_prompt: Optional system prompt
            tools: Optional list of tools for function calling

        Returns:
            Raw response from Ollama
        """
        # Add user message to history
        self.add_message("user", message)

        # Prepare messages for Ollama
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # Add conversation history
        for msg in self.conversation_history:
            messages.append({"role": msg.role, "content": msg.content})

        # Make the request
        options = {
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "top_k": self.config.top_k,
        }

        # Try with tools first, fall back without tools if not supported
        try:
            response = await self.client.chat(
                model=self.config.model,
                messages=messages,
                tools=tools if tools else None,
                options=options,
            )
        except Exception as e:
            # If tools not supported, try without tools
            if "does not support tools" in str(e).lower() or "400" in str(e):
                response = await self.client.chat(
                    model=self.config.model,
                    messages=messages,
                    options=options,
                )
            else:
                raise

        return response

    async def chat_with_tools_result_raw(
        self,
        tool_results: List[Dict[str, Any]],
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Continue conversation with tool results, returning raw response.

        Args:
            tool_results: Results from tool execution
            system_prompt: Optional system prompt
            tools: Optional list of tools for potential follow-up calls

        Returns:
            Full raw response dict from Ollama
        """
        # Prepare messages including tool results
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # Add conversation history
        for msg in self.conversation_history:
            messages.append({"role": msg.role, "content": msg.content})

        # Add tool results
        for result in tool_results:
            messages.append(result)

        # Make the request
        options = {
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "top_k": self.config.top_k,
        }

        response = await self.client.chat(
            model=self.config.model,
            messages=messages,
            options=options,
            tools=tools if tools else None,  # Include tools for potential follow-up calls
        )

        # Save the assistant message to history
        assistant_message = response.get("message", {}).get("content", "")
        if assistant_message:
            self.add_message("assistant", assistant_message)

        return response

    async def chat_with_tools_result(
        self,
        tool_results: List[Dict[str, Any]],
        system_prompt: Optional[str] = None,
    ) -> str:
        """Continue conversation with tool results.

        Args:
            tool_results: Results from tool execution
            system_prompt: Optional system prompt

        Returns:
            Assistant's final response
        """
        response = await self.chat_with_tools_result_raw(tool_results, system_prompt, tools=None)
        return response.get("message", {}).get("content", "")

    async def list_models(self) -> List[str]:
        """List available models.

        Returns:
            List of model names
        """
        models = await self.client.list()
        return [model["name"] for model in models.get("models", [])]

    async def pull_model(self, model_name: str) -> None:
        """Pull a model from Ollama.

        Args:
            model_name: Name of the model to pull
        """
        await self.client.pull(model_name)

    def switch_model(self, model_name: str, verbose: bool = True) -> None:
        """Switch to a different model.

        This changes the model used for future chat calls while preserving
        the conversation history.

        Args:
            model_name: Name of the model to switch to
            verbose: Whether to print a message about the switch (default: True)
        """
        self.config.model = model_name

    def get_current_model(self) -> str:
        """Get the currently active model name.

        Returns:
            Current model name
        """
        return self.config.model

    async def chat_simple(
        self,
        message: str,
        system_prompt: Optional[str] = None,
    ) -> str:
        """Send a simple chat message without maintaining conversation history.

        This is useful for one-off evaluations or checks that shouldn't be
        part of the main conversation flow (e.g., progress evaluation).

        Args:
            message: User message
            system_prompt: Optional system prompt

        Returns:
            Assistant's response
        """
        # Prepare messages (no conversation history)
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})

        # Make the request with minimal options for faster response
        options = {
            "temperature": 0.1,  # Low temperature for consistent evaluation
            "top_p": 0.9,
            "top_k": 40,
        }

        response = await self.client.chat(
            model=self.config.model,
            messages=messages,
            options=options,
        )

        return response.get("message", {}).get("content", "")
