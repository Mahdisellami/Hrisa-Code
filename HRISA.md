# Hrisa Code Documentation (HRISA.md)

## Project Overview

Hrisa Code is an AI-assisted development tool designed to facilitate interaction with large language models (LLMs) for various tasks such as code generation, documentation creation, and more. It leverages Typer for CLI command handling, Pydantic for configuration management, and provides a flexible framework for defining and using tools.

## Tech Stack

- **Programming Language:** Python
- **Command Line Interface:** Typer
- **Configuration Management:** Pydantic
- **HTTP Client:** HTTPX
- **Testing Framework:** pytest

### Libraries & Tools Used:

1. **Typer** - For building the command-line interface.
2. **Pydantic** - For data validation and settings management using Python type annotations.
3. **HTTPX** - Asynchronous HTTP client for making requests to LLMs.
4. **pytest** - For writing unit tests and integration tests.

## Project Structure

The project is organized into several directories:

```
Hrisa-Code/
├── src/
│   └── hrisa_code/
│       ├── cli.py
│       ├── config.py
│       ├── interactive.py
│       ├── ollama_client.py
│       ├── conversation.py
│       ├── agent.py (optional)
│       ├── task_manager.py (optional)
│       ├── __init__.py
│       └── tools/
│           ├── __init__.py
│           └── tool_name.py
├── tests/
│   ├── test_cli.py
│   ├── test_config.py
│   └── ...
├── pyproject.toml
└── README.md
```

### Directory Layout:

- **src/hrisa_code/** - Contains the source code of Hrisa Code.
  - **cli.py** - Main entry point for the CLI interface.
  - **config.py** - Configuration management using Pydantic models.
  - **interactive.py** - Handles interactive sessions with the LLM.
  - **ollama_client.py** - Manages interactions with the Ollama API.
  - **conversation.py** - Manages conversation flow and tool calling logic.
  - **agent.py (optional)** - If present, handles autonomous task execution.
  - **task_manager.py (optional)** - If present, manages background tasks and scheduling.
  - **tools/** - Contains various tools that the LLM can use.

- **tests/** - Contains test files for unit testing and integration testing of Hrisa Code components.

## Key Components

### Detailed Explanation of Each Module:

1. **cli.py**:
   - **Role:** Serves as the main entry point for the CLI application.
   - **Key Classes & Functions:**
     - `app`: Typer application instance.
     - `main()`: Main function that initializes and runs the CLI.
     - Command Handlers: Functions decorated with `@app.command()`.

2. **config.py**:
   - **Role:** Manages configuration settings using Pydantic models.
   - **Key Classes & Functions:**
     - `ConfigModel`: Pydantic model for configuration settings.
     - `load_config()`: Loads and validates the configuration from a file or environment variables.

3. **interactive.py**:
   - **Role:** Handles interactive sessions with the LLM.
   - **Key Classes & Functions:**
     - `InteractiveSession`: Manages the lifecycle of an interactive session.
     - Methods for sending user messages, receiving responses, and managing context.

4. **ollama_client.py**:
   - **Role:** Manages interactions with the Ollama API to fetch LLM responses.
   - **Key Classes & Functions:**
     - `OllamaClient`: HTTP client for communicating with the Ollama API.
     - Methods for sending prompts and receiving completions.

5. **conversation.py**:
   - **Role:** Manages conversation flow, including tool calling logic.
   - **Key Classes & Functions:**
     - `ConversationManager`: Orchestrates the conversation between user and LLM.
     - Tool calling mechanism to invoke tools defined in the `tools` module.

6. **agent.py (optional)**:
   - **Role:** Handles autonomous task execution based on predefined rules or triggers.
   - **Key Classes & Functions:**
     - `Agent`: Manages autonomous tasks.
     - Methods for scheduling and executing tasks.

7. **task_manager.py (optional)**:
   - **Role:** Manages background tasks, such as periodic data fetching or processing.
   - **Key Classes & Functions:**
     - `TaskManager`: Orchestrates the execution of background tasks.
     - Methods for scheduling, running, and monitoring tasks.

### How Modules Interact:

- **cli.py** initializes the application and routes commands to appropriate handlers.
- **config.py** provides configuration settings that are used throughout the application.
- **interactive.py** manages user interactions with the LLM.
- **ollama_client.py** fetches responses from the Ollama API based on prompts provided by `interactive.py`.
- **conversation.py** orchestrates the conversation flow, including tool calling logic.
- **agent.py** and **task_manager.py** (if present) handle autonomous and background tasks, respectively.

### Design Patterns Used:

1. **Single Responsibility Principle:** Each module has a single responsibility, making it easier to understand, test, and maintain.
2. **Dependency Injection:** Configuration settings are injected into modules that require them, promoting loose coupling.
3. **Command Pattern:** CLI commands are defined using decorators, allowing for easy addition of new commands.

## CLI Commands

### Available Commands:

1. **start**:
   - Description: Starts an interactive session with the LLM.
   - Usage: `hrisa start`

2. **configure**:
   - Description: Configures settings for Hrisa Code.
   - Usage: `hrisa configure`

3. **list-tools**:
   - Description: Lists all available tools that the LLM can use.
   - Usage: `hrisa list-tools`

4. **run-task**:
   - Description: Runs a specific task (if agent.py is present).
   - Usage: `hrisa run-task <task-name>`

5. **test**:
   - Description: Runs tests for the Hrisa Code project.
   - Usage: `hrisa test`

## Tools & Capabilities

### All Tools/Functions the LLM Can Use:

1. **Code Generation Tool**:
   - Schema: `ToolSchema`
   - Purpose: Generates code snippets based on user prompts.

2. **Documentation Tool**:
   - Schema: `ToolSchema`
   - Purpose: Generates documentation for provided code or modules.

3. **Translation Tool**:
   - Schema: `ToolSchema`
   - Purpose: Translates text between different languages.

### Configuration Options:

- **API Key**: API key for accessing the Ollama API.
- **Default Model**: Default model to use when interacting with the LLM.
- **Timeout**: Timeout duration for API requests.

## Features

### Major Features:

1. **Agent Mode**:
   - Description: Autonomous task execution based on rules or triggers.
   - Usage: Defined in `agent.py` (if present).

2. **Multi-Turn Tool Calling**:
   - Description: Supports multi-turn tool calling similar to Claude Code style.

3. **Background Tasks**:
   - Description: Periodic data fetching, processing, or other background operations.
   - Usage: Defined in `task_manager.py` (if present).

4. **Streaming Responses**:
   - Description: Streams LLM responses in real-time.

5. **Interactive Sessions**:
   - Description: Allows users to interact with the LLM in an interactive manner.

## Development Practices

### Code Style:

- Follows PEP 8 guidelines.
- Consistent use of type hints for better readability and maintainability.

### Testing:

- Unit tests are written using `pytest`.
- Test files are located in the `tests/` directory.

### Linting:

- Uses tools like `flake8` to enforce code style and identify potential issues.

## Common Tasks

### How to Add Features:

1. **Define a New Tool**:
   - Create a new file in the `tools/` directory.
   - Define a schema using Pydantic models.
   - Implement the tool logic.

2. **Add CLI Commands**:
   - Add a function in `cli.py`.
   - Decorate with `@app.command()` and provide usage instructions.

3. **Update Configuration Options**:
   - Modify `config.py` to include new settings.
   - Update documentation and configuration file examples accordingly.

### How to Run Tests:

- Execute the following command in the root directory:
  ```
  pytest
  ```

## Important Files

### Critical Files and Their Purposes:

1. **pyproject.toml**:
   - Description: Specifies project dependencies, build system requirements, and other metadata.
   - Purpose: Used by `poetry` for dependency management and packaging.

2. **README.md**:
   - Description: Project documentation.
   - Purpose: Provides an overview of the project, installation instructions, usage examples, etc.

3. **src/hrisa_code/cli.py**:
   - Description: Main entry point for the CLI application.
   - Purpose: Handles command-line arguments and dispatches to appropriate functions.

4. **src/hrisa_code/config.py**:
   - Description: Configuration management using Pydantic models.
   - Purpose: Loads and validates configuration settings.

## Workflows

### How the Application Works End-to-End:

1. **CLI Initialization**:
   - The `cli.py` module initializes the Typer application and sets up command handlers.

2. **Configuration Loading**:
   - Configuration settings are loaded from a file or environment variables using `config.py`.

3. **Interactive Session**:
   - When the user starts an interactive session, `interactive.py` manages the conversation with the LLM.
   - Prompts are sent to `ollama_client.py`, which fetches responses.

4. **Tool Calling**:
   - During the conversation, tools can be invoked using the schema defined in `conversation.py`.
   - Tool-specific logic is executed based on user input and tool configuration.

5. **Agent Mode (if present)**:
   - Autonomous tasks are scheduled and executed by `agent.py`.

6. **Background Tasks (if present)**:
   - Background operations are managed by `task_manager.py`.

## Code Patterns

### Common Patterns:

1. **Single Responsibility Principle**:
   - Each module has a single responsibility, promoting modularity and maintainability.

2. **Dependency Injection**:
   - Configuration settings are passed to modules that require them, reducing coupling.

3. **Command Pattern**:
   - CLI commands are defined using decorators for easy addition of new functionality.

## Notes for AI Assistants

### Important Guidelines:

1. **Follow PEP 8**:
   - Adhere to Python's official style guide for code consistency.

2. **Use Type Hints**:
   - Provide type hints for function parameters and return values to improve readability and maintainability.

3. **Write Tests**:
   - Write unit tests for new features and modifications to ensure functionality and prevent regressions.

4. **Document Changes**:
   - Update documentation (`README.md`) with details of any significant changes or additions.

## Version Information

### Current Version:

- **Version:** 1.0.0
- **Status:** Stable

This comprehensive guide covers all aspects of Hrisa Code, from project overview and tech stack to detailed module explanations and development practices. For further assistance, refer to the `README.md` file or contact the maintainers.

---

**End of Documentation**

Feel free to reach out with any questions or feedback!