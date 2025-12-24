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

        response = await self.client.chat(
            model=self.config.model,
            messages=messages,
            tools=tools,
            options=options,
        )

        # Extract response
        assistant_message = response["message"]["content"]
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
        async for chunk in await self.client.chat(
            model=self.config.model,
            messages=messages,
            tools=tools,
            options=options,
            stream=True,
        ):
            if "message" in chunk and "content" in chunk["message"]:
                content = chunk["message"]["content"]
                full_response += content
                yield content

        # Add complete response to history
        self.add_message("assistant", full_response)

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
