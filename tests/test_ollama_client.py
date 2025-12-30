"""Tests for Ollama client."""

import pytest
from hrisa_code.core.conversation import OllamaClient, OllamaConfig, Message


def test_ollama_config_defaults():
    """Test OllamaConfig default values."""
    config = OllamaConfig()
    assert config.model == "codellama"
    assert config.host == "http://localhost:11434"
    assert config.temperature == 0.7


def test_ollama_config_custom():
    """Test OllamaConfig with custom values."""
    config = OllamaConfig(
        model="mistral",
        host="http://example.com:8080",
        temperature=0.5,
    )
    assert config.model == "mistral"
    assert config.host == "http://example.com:8080"
    assert config.temperature == 0.5


def test_message_creation():
    """Test Message model."""
    msg = Message(role="user", content="Hello")
    assert msg.role == "user"
    assert msg.content == "Hello"
    assert msg.tool_calls is None


def test_ollama_client_initialization():
    """Test OllamaClient initialization."""
    config = OllamaConfig()
    client = OllamaClient(config)
    assert client.config == config
    assert len(client.conversation_history) == 0


def test_add_message():
    """Test adding messages to conversation history."""
    config = OllamaConfig()
    client = OllamaClient(config)

    client.add_message("user", "Hello")
    assert len(client.conversation_history) == 1
    assert client.conversation_history[0].role == "user"
    assert client.conversation_history[0].content == "Hello"

    client.add_message("assistant", "Hi there!")
    assert len(client.conversation_history) == 2


def test_clear_history():
    """Test clearing conversation history."""
    config = OllamaConfig()
    client = OllamaClient(config)

    client.add_message("user", "Hello")
    client.add_message("assistant", "Hi")
    assert len(client.conversation_history) == 2

    client.clear_history()
    assert len(client.conversation_history) == 0
