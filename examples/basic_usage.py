"""Basic usage example for Hrisa Code library."""

import asyncio
from pathlib import Path
from hrisa_code.core.ollama_client import OllamaClient, OllamaConfig
from hrisa_code.core.conversation import ConversationManager
from hrisa_code.core.config import Config


async def simple_chat_example():
    """Simple chat example."""
    print("=== Simple Chat Example ===\n")

    # Create Ollama client
    config = OllamaConfig(model="codellama", temperature=0.7)
    client = OllamaClient(config)

    # Chat with the model
    response = await client.chat("What is Python?")
    print(f"Question: What is Python?")
    print(f"Answer: {response}\n")


async def streaming_example():
    """Streaming response example."""
    print("=== Streaming Example ===\n")

    config = OllamaConfig(model="codellama")
    client = OllamaClient(config)

    print("Question: Explain list comprehension in Python")
    print("Answer: ", end="", flush=True)

    async for chunk in client.chat_stream("Explain list comprehension in Python"):
        print(chunk, end="", flush=True)

    print("\n")


async def conversation_example():
    """Example with conversation manager and tools."""
    print("=== Conversation with Tools Example ===\n")

    # Load configuration
    config = Config()

    # Create conversation manager
    ollama_config = OllamaConfig(
        model=config.model.name,
        temperature=config.model.temperature,
    )

    conversation = ConversationManager(
        ollama_config=ollama_config,
        working_directory=Path.cwd(),
    )

    # Have a conversation
    questions = [
        "List files in the current directory",
        "What files did you find?",
    ]

    for question in questions:
        print(f"User: {question}")
        response = await conversation.process_message(question)
        print(f"Assistant: {response}\n")


async def list_models_example():
    """List available models."""
    print("=== List Models Example ===\n")

    config = OllamaConfig()
    client = OllamaClient(config)

    models = await client.list_models()
    print("Available models:")
    for model in models:
        print(f"  - {model}")
    print()


async def main():
    """Run all examples."""
    try:
        # Simple chat
        await simple_chat_example()

        # Streaming
        await streaming_example()

        # List models
        await list_models_example()

        # Conversation with tools
        # Uncomment to try (requires tools to be fully implemented)
        # await conversation_example()

    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure Ollama is running:")
        print("  ollama serve")


if __name__ == "__main__":
    asyncio.run(main())
