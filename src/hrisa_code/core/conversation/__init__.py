"""Conversation management and LLM interaction.

This module handles:
- LLM communication via Ollama
- Conversation history management
- Multi-turn tool calling
- Streaming responses
"""

from .conversation import ConversationManager
from .ollama_client import OllamaClient, OllamaConfig

__all__ = [
    "ConversationManager",
    "OllamaClient",
    "OllamaConfig",
]
