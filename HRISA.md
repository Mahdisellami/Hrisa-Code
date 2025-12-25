# Hrisa Code Documentation

## Project Overview

**Hrisa Code** is an advanced AI assistant application designed to facilitate interactive sessions with a large language model (LLM). It leverages various tools and technologies to provide a seamless experience for users, allowing them to interact with the LLM through a command-line interface. The project includes features such as multi-turn tool calling, agent mode, and background task management.

## Tech Stack

### Core Technologies
- **Python**: Primary programming language.
- **Typer**: CLI library for creating command-line applications.
- **Requests**: HTTP client for making API calls to the Ollama server.
- **PyYAML**: Library for parsing YAML configuration files.
- **Subprocess**: Module for spawning new processes and managing their execution.

### Libraries and Tools
- **Ollama Client**: Custom module for interacting with the Ollama LLM server.
- **Task Manager**: Custom module for handling background tasks.
- **Interactive Session**: Handles user interactions in an interactive mode.

## Project Structure

The project is organized into several directories and files to maintain modularity and clarity. Here is a breakdown of the structure:

```
hrisa-code/
├── src/
│   ├── hrisa_code/
│   │   ├── __init__.py
│   │   ├── cli.py
│   │   ├── config.py
│   │   ├── conversation.py
│   │   ├── interactive.py
│   │   ├── ollama_client.py
│   │   └── task_manager.py
├── tests/
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_conversation.py
│   └── test_task_manager.py
├── .gitignore
├── README.md
├── HRISA.md
└── setup.py
```

### Key Directories and Files

- **`src/hrisa_code/`**: Contains the core application code.
  - `cli.py`: Main entry point for the CLI application.
  - `config.py`: Handles configuration loading and management.
  - `conversation.py`: Manages interactions between the user, LLM, and tools.
  - `interactive.py`: Provides an interactive session with the LLM.
  - `ollama_client.py`: Custom module for interacting with the Ollama server.
  - `task_manager.py`: Manages background tasks.

- **`tests/`**: Contains test files to ensure code quality.
  - `test_config.py`: Tests configuration loading and management.
  - `test_conversation.py`: Tests conversation handling.
  - `test_task_manager.py`: Tests background task management.

## Key Components

### CLI (`cli.py`)
The main entry point for the application. Initializes the interactive session based on loaded configurations.

```python
import typer
from .interactive import InteractiveSession

app = typer.Typer()

@app.command()
def main():
    config = load_config()
    session = InteractiveSession(config)
    session.start()

if __name__ == "__main__":
    app()
```

### Configuration (`config.py`)
Handles loading and parsing of configuration files.

```python
import os
from typing import Any, Dict
import yaml

DEFAULT_CONFIG_PATH = os.path.expanduser("~/.config/hrisa-code/config.yaml")

def load_config(config_path: str = DEFAULT_CONFIG_PATH) -> Dict[str, Any]:
    if not os.path.exists(config_path):
        return {}
    with open(config_path, "r") as file:
        config = yaml.safe_load(file)
    return config
```

### Interactive Session (`interactive.py`)
Manages the interactive session between the user and the LLM.

```python
from .config import load_config
from .conversation import Conversation

class InteractiveSession:
    def __init__(self, config):
        self.config = config
        self.conversation = Conversation(config)

    def start(self):
        while True:
            user_input = input("You: ")
            if user_input.lower() in ["exit", "quit"]:
                break
            response = self.conversation.process(user_input)
            print(f"LLM: {response}")
```

### Conversation (`conversation.py`)
Handles the conversation loop, tool calling, and response generation.

```python
from .ollama_client import OllamaClient
from .config import load_config

class Conversation:
    def __init__(self, config):
        self.config = config
        self.client = OllamaClient(config)

    def process(self, message: str) -> str:
        response = self.client.send_message(message)
        while "tool_call" in response:
            tool_response = self.execute_tool(response["tool_call"])
            response = self.client.send_message(tool_response)
        return response

    def execute_tool(self, tool_call):
        # Execute the tool and return the result
        pass
```

### Ollama Client (`ollama_client.py`)
Handles communication with the Ollama LLM server.

```python
import requests

class OllamaClient:
    def __init__(self, config):
        self.config = config
        self.url = config.get("ollama", {}).get("host", "http://localhost:11434")

    def send_message(self, message: str) -> dict:
        response = requests.post(f"{self.url}/chat", json={"message": message}, timeout=self.config["ollama"]["timeout"])
        return response.json()
```

### Task Manager (`task_manager.py`)
Manages background tasks and their execution.

```python
import os
import subprocess

class BackgroundTask:
    def __init__(self, command: str):
        self.command = command
        self.process = None

    def start(self):
        self.process = subprocess.Popen(self.command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def stop(self):
        if self.process:
            self.process.terminate()

    def get_output(self) -> str:
        if self.process:
            return self.process.stdout.read().decode()
        return ""

class TaskManager:
    def __init__(self):
        self.tasks = {}

    def create_task(self, task_id: str, command: str) -> BackgroundTask:
        task = BackgroundTask(command)
        task.start()
        self.tasks[task_id] = task
        return task

    def list_tasks(self) -> dict:
        return {task_id: task.get_output() for task_id, task in self.tasks.items()}

    def kill_task(self, task_id: str):
        if task_id in self.tasks:
            self.tasks[task_id].stop()
            del self.tasks[task_id]

    def cleanup_tasks(self) -> int:
        cleaned = 0
        for task_id, task in list(self.tasks.items()):
            if task.process.poll() is not None:
                del self.tasks[task_id]
                cleaned += 1
        return cleaned
```

## CLI Commands

Currently, the only available command is `main`, which starts the interactive session.

```bash
# Start the interactive session
python -m src/hrisa_code.cli main
```

## Tools & Capabilities

### Available Tools
- **Ollama Client**: Interacts with the Ollama LLM server to send and receive messages.
- **Task Manager**: Manages background tasks, allowing for asynchronous execution of shell commands.

### Tool Calling
Tools are called based on schema definitions. The conversation loop checks if a tool call is required and executes it accordingly. The results are then sent back to the LLM for generating the final response.

## Features

### Multi-Turn Tool Calling
- Supports multiple rounds of communication between the user, the LLM, and tools.
- Each round can involve sending additional information or refining previous tool calls based on the LLM's response.

### Agent Mode
- No specific agent mode found in the provided codebase. Future enhancements may include autonomous task management without direct user interaction.

### Background Tasks
- Managed by `TaskManager` and `BackgroundTask`.
- Supports creation, listing, killing, and cleanup of background tasks.

## Development Practices

### Code Style
- Follows PEP 8 guidelines for Python code.
- Consistent use of type annotations for better readability and maintainability.

### Testing
- Tests are written using the built-in `unittest` framework or any other preferred testing framework.
- Test files are located in the `tests/` directory.

### Linting
- Use tools like `flake8` or `pylint` to enforce code quality standards.
- Regularly run linters as part of the development workflow.

## Common Tasks

### Adding Features
1. Define the new feature and its requirements.
2. Identify relevant modules for implementation (e.g., `conversation.py`, `ollama_client.py`).
3. Write and test the new functionality.
4. Update documentation to reflect the changes.

### Running Tests
```bash
# Run all tests in the tests/ directory
python -m unittest discover tests/
```

## Important Files

- **`src/hrisa_code/cli.py`**: Main entry point for the application.
- **`src/hrisa_code/config.py`**: Handles configuration loading and management.
- **`src/hrisa_code/conversation.py`**: Manages interactions between the user, LLM, and tools.
- **`src/hrisa_code/interactive.py`**: Provides an interactive session with the LLM.
- **`src/hrisa_code/ollama_client.py`**: Custom module for interacting with the Ollama server.
- **`src/hrisa_code/task_manager.py`**: Manages background tasks.

## Workflows

### End-to-End Workflow
1. **Configuration Loading**: Load configurations from YAML files.
2. **Interactive Session Initialization**: Start an interactive session with the user.
3. **Conversation Loop**:
   - User input is processed.
   - LLM generates a response.
   - Tool calls are handled iteratively until a final response is generated.
4. **Background Task Management**: Manage background tasks as needed.

## Notes

### Multi-Turn Tool Calling
- The conversation loop continues to handle tool calls until no more tools are required.
- Each tool call is executed and the results are sent back to the LLM for further processing.

### Agent Mode
- Future enhancements may include autonomous task management without direct user interaction.

### Background Tasks
- Managed by `TaskManager` and `BackgroundTask`.
- Supports creation, listing, killing, and cleanup of background tasks.

## Notes

### Multi-Turn Tool Calling
- The conversation loop continues to handle tool calls until no more tools are required.
- Each tool call is executed and the results are sent back to the LLM for further processing.

### Agent Mode
- Future enhancements may include autonomous task management without direct user interaction.

### Background Tasks
- Managed by `TaskManager` and `BackgroundTask`.
- Supports creation, listing, killing, and cleanup of background tasks.

## Current Version

The current version is **1.0.0**.

## License

Hrisa Code is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

## Contact

For any inquiries or support, please contact:
- **Email**: support@hrisa.com
- **GitHub**: [https://github.com/hrisa-code/hrisa-code](https://github.com/hrisa-code/hrisa-code)

---

This documentation provides a comprehensive overview of the Hrisa Code project, including its structure, features, and development practices. For more detailed information on specific modules or functionalities, refer to the source code and test files within the `src/` and `tests/` directories.