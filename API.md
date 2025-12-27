# Hrisa Code API Reference Documentation

## API Overview

This document provides comprehensive documentation for developers, integrators, and extension authors who are working with Hrisa Code. It covers all aspects of using the command-line interface (CLI), tools system, core APIs, configuration management, orchestrator customization, and error handling.

### Quick Links to Main Sections
- [CLI Reference](#cli-reference)
- [Tools Reference](#tools-reference)
- [Core API Reference](#core-api-reference)
- [Configuration Reference](#configuration-reference)
- [Orchestrator API](#orchestrator-api)
- [Extension Guide](#extension-guide)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Migration Guide](#migration-guide)

## CLI Reference

### Commands Overview

#### `hrisa init`
Syntax: `hrisa init [OPTIONS]`

**Description**: Initializes a new Hrisa project.

| Arguments | Type   | Default | Description |
|-----------|--------|---------|-------------|
| directory | str    | ./      | Project directory path. |

| Options  | Type | Default | Description |
|----------|------|---------|-------------|
| --force  | bool | False   | Force overwrite existing files. |

**Examples:**
```bash
hrisa init
hrisa init --force /path/to/new/project
```

#### `hrisa run`
Syntax: `hrisa run [OPTIONS] [ARGS]`

**Description**: Runs a specified workflow.

| Arguments | Type   | Default | Description |
|-----------|--------|---------|-------------|
| workflow  | str    |         | Workflow name to execute. |

| Options  | Type   | Default | Description |
|----------|--------|---------|-------------|
| --debug  | bool   | False   | Enable debug mode for verbose output. |

**Examples:**
```bash
hrisa run my_workflow
hrisa run my_workflow --debug
```

#### `hrisa list`
Syntax: `hrisa list [OPTIONS]`

**Description**: Lists available workflows and tools.

| Options  | Type    | Default | Description |
|----------|---------|---------|-------------|
| --tools  | bool    | False   | List available tools. |

**Examples:**
```bash
hrisa list
hrisa list --tools
```

#### `hrisa config`
Syntax: `hrisa config [OPTIONS] [ARGS]`

**Description**: Manages configuration settings.

| Arguments | Type   | Default | Description |
|-----------|--------|---------|-------------|
| action    | str    |         | Action to perform (view, edit). |

| Options  | Type    | Default | Description |
|----------|---------|---------|-------------|
| --path   | str     | .hrisa/config.yaml | Path to the configuration file. |

**Examples:**
```bash
hrisa config view
hrisa config edit --path ~/.config/hrisa-code/config.yaml
```

### Exit Codes

- `0`: Success
- `1`: Generic error
- `2`: Invalid command
- `3`: Configuration error

## Tools Reference

### Tool System Overview

Hrisa Code uses a modular tool system to perform various operations. Tools are organized into categories and can be easily extended by developers.

### Tools Categories

#### File Operations
- **read_file**
  - **Description**: Reads the content of a specified file.
  - **JSON Schema**:
    ```json
    {
      "tool": "read_file",
      "description": "Reads the content of a specified file.",
      "params": {
        "file_path": {
          "type": "string",
          "description": "Path to the file to be read."
        }
      },
      "return_type": "string"
    }
    ```
  - **Parameters**:
    | Name      | Type   | Default | Description |
    |-----------|--------|---------|-------------|
    | file_path | str    |         | Path to the file to be read. |

  - **Return Format**: `str`

  - **Example Tool Call**:
    ```json
    {
      "tool": "read_file",
      "params": {
        "file_path": "./src/hrisa_code/core/__init__.py"
      }
    }
    ```

  - **Error Conditions**: File not found, permission denied.

#### Command Execution
- **execute_command**
  - **Description**: Executes a shell command.
  - **JSON Schema**:
    ```json
    {
      "tool": "execute_command",
      "description": "Executes a shell command.",
      "params": {
        "command": {
          "type": "string",
          "description": "Shell command to execute."
        }
      },
      "return_type": "str"
    }
    ```
  - **Parameters**:
    | Name      | Type   | Default | Description |
    |-----------|--------|---------|-------------|
    | command   | str    |         | Shell command to execute. |

  - **Return Format**: `str`

  - **Example Tool Call**:
    ```json
    {
      "tool": "execute_command",
      "params": {
        "command": "ls -l"
      }
    }
    ```

  - **Error Conditions**: Command not found, execution error.

### How to Add Custom Tools

1. **Define the Tool Function**:
   Create a new function in `tools/` or an appropriate subdirectory.
2. **Create a JSON Schema**:
   Define the schema for the tool in a separate file.
3. **Register the Tool**:
   Add the tool to the `AVAILABLE_TOOLS` registry in the main script or configuration file.
4. **Implement Execution Logic**:
   Ensure the tool can be executed correctly by handling all necessary parameters and return types.
5. **Write Tests**:
   Include test cases for the new tool in the `tests/` directory.
6. **Documentation**:
   Update the API reference with details about the new tool.

## Core API Reference

### Organized by Module

#### Module: `core.config`

##### Class: `Config`
- **Import Path**: `hrisa_code.core.config.Config`
- **Class Signature**: `class Config(BaseModel)`
- **Description**: Base configuration class.
- **Parameters**:
  | Name           | Type     | Default | Description |
  |----------------|----------|---------|-------------|
  | model          | ModelConfig |         | Model-specific configurations. |
  | ollama         | OllamaServerConfig |         | Ollama server configurations. |
  | tools          | ToolsConfig |         | Tool-specific configurations. |
  | system_prompt  | Optional[str] | None   | Custom system prompt. |

- **Returns**: `None`

- **Raises**:
  - `ValidationError`: If configuration data is invalid.

- **Usage Example**:
  ```python
  from hrisa_code.core.config import Config

  config = Config(
      model=ModelConfig(name="gpt-4"),
      ollama=OllamaServerConfig(host="https://ollama.example.com"),
      tools=ToolsConfig(enabled=True),
      system_prompt="You are a helpful assistant."
  )
  ```

##### Class: `ModelConfig`
- **Import Path**: `hrisa_code.core.config.ModelConfig`
- **Class Signature**: `class ModelConfig(BaseModel)`
- **Description**: Configuration for the language model.
- **Parameters**:
  | Name        | Type   | Default     | Description |
  |-------------|--------|-------------|-------------|
  | name        | str    | "qwen2.5:72b" | Name of the language model. |
  | temperature | float  | 0.7         | Controls randomness in generated text. |
  | top_p       | float  | 0.9         | Cumulative probability threshold for nucleus sampling. |
  | top_k       | int    | 40          | Number of highest probability vocabulary tokens to keep for top-k filtering. |

- **Returns**: `None`

- **Raises**:
  - `ValidationError`: If configuration data is invalid.

- **Usage Example**:
  ```python
  from hrisa_code.core.config import ModelConfig

  model_config = ModelConfig(name="gpt-4", temperature=0.5, top_p=0.8)
  ```

#### Module: `core.tools`

##### Function: `read_file`
- **Import Path**: `hrisa_code.core.tools.read_file`
- **Function Signature**: `def read_file(file_path: str) -> str`
- **Description**: Reads the content of a specified file.
- **Parameters**:
  | Name      | Type   | Default | Description |
  |-----------|--------|---------|-------------|
  | file_path | str    |         | Path to the file to be read. |

- **Returns**: `str`

- **Raises**:
  - `FileNotFoundError`: If the file does not exist.
  - `PermissionError`: If the file cannot be accessed.

- **Usage Example**:
  ```python
  from hrisa_code.core.tools import read_file

  content = read_file("./src/hrisa_code/core/__init__.py")
  print(content)
  ```

##### Function: `execute_command`
- **Import Path**: `hrisa_code.core.tools.execute_command`
- **Function Signature**: `def execute_command(command: str) -> str`
- **Description**: Executes a shell command.
- **Parameters**:
  | Name      | Type   | Default | Description |
  |-----------|--------|---------|-------------|
  | command   | str    |         | Shell command to execute. |

- **Returns**: `str`

- **Raises**:
  - `OSError`: If the command execution fails.

- **Usage Example**:
  ```python
  from hrisa_code.core.tools import execute_command

  output = execute_command("ls -l")
  print(output)
  ```

## Configuration Reference

### Configuration Management

Hrisa Code uses a configuration file to manage settings for the language model, Ollama server, and tools. The default configuration path is `.hrisa/config.yaml`.

#### Default Configuration
```yaml
model:
  name: qwen2.5:72b
  temperature: 0.7
  top_p: 0.9
  top_k: 40
ollama:
  host: http://localhost:8000
tools:
  enabled: true
system_prompt: "You are a helpful assistant."
```

#### Custom Configuration

To customize the configuration, you can edit the `.hrisa/config.yaml` file or use the `hrisa config edit` command.

**Examples:**
```bash
hrisa config edit --path ~/.config/hrisa-code/config.yaml
```

## Orchestrator API

### Orchestrator Customization

Hrisa Code uses an orchestrator to manage and execute workflows. Developers can customize the orchestrator by defining new workflows and tools.

#### Workflow Definition

Workflows are defined in YAML files located in the `workflows/` directory.

**Example Workflow:**
```yaml
name: my_workflow
steps:
  - tool: read_file
    params:
      file_path: ./src/hrisa_code/core/__init__.py
  - tool: execute_command
    params:
      command: echo "Workflow completed."
```

#### Customizing Workflows

To add a new workflow, create a YAML file in the `workflows/` directory and define the steps using available tools.

**Example Workflow File (`my_workflow.yaml`):**
```yaml
name: my_custom_workflow
steps:
  - tool: read_file
    params:
      file_path: ./src/hrisa_code/core/__init__.py
  - tool: execute_command
    params:
      command: echo "Custom workflow completed."
```

## Extension Guide

### Extending Hrisa Code

Developers can extend Hrisa Code by adding new tools, workflows, and configurations.

#### Adding New Tools

1. **Define the Tool Function**:
   Create a new function in `tools/` or an appropriate subdirectory.
2. **Create a JSON Schema**:
   Define the schema for the tool in a separate file.
3. **Register the Tool**:
   Add the tool to the `AVAILABLE_TOOLS` registry in the main script or configuration file.

**Example New Tool (`my_tool.py`):**
```python
from typing import Any

def my_tool(param1: str, param2: int) -> str:
    return f"Processed {param1} with {param2}"
```

**JSON Schema for `my_tool`:**
```json
{
  "tool": "my_tool",
  "description": "Processes a string and an integer.",
  "params": {
    "param1": {
      "type": "string",
      "description": "Input string."
    },
    "param2": {
      "type": "integer",
      "description": "Input integer."
    }
  },
  "return_type": "string"
}
```

#### Adding New Workflows

1. **Define the Workflow**:
   Create a new YAML file in the `workflows/` directory.
2. **Use Available Tools**:
   Define steps using available tools.

**Example New Workflow (`my_custom_workflow.yaml`):**
```yaml
name: my_custom_workflow
steps:
  - tool: read_file
    params:
      file_path: ./src/hrisa_code/core/__init__.py
  - tool: my_tool
    params:
      param1: "example"
      param2: 42
```

## Error Handling

### Common Errors

Hrisa Code handles various errors gracefully and provides informative error messages.

#### File Not Found Error

**Error Message**: `FileNotFoundError`
**Description**: Raised when a specified file does not exist.
**Example**:
```python
try:
    content = read_file("./non_existent_file.txt")
except FileNotFoundError as e:
    print(f"Error: {e}")
```

#### Permission Denied Error

**Error Message**: `PermissionError`
**Description**: Raised when the program does not have permission to access a file.
**Example**:
```python
try:
    content = read_file("/protected/file.txt")
except PermissionError as e:
    print(f"Error: {e}")
```

#### Command Execution Error

**Error Message**: `OSError`
**Description**: Raised when a shell command execution fails.
**Example**:
```python
try:
    output = execute_command("non_existent_command")
except OSError as e:
    print(f"Error: {e}")
```

## Examples

### Example Workflow Definition

**Workflow File (`my_workflow.yaml`):**
```yaml
name: my_workflow
steps:
  - tool: read_file
    params:
      file_path: ./src/hrisa_code/core/__init__.py
  - tool: execute_command
    params:
      command: echo "Workflow completed."
```

### Example Configuration File

**Configuration File (`config.yaml`):**
```yaml
model:
  name: gpt-4
  temperature: 0.5
  top_p: 0.8
  top_k: 32
ollama:
  host: https://ollama.example.com
tools:
  enabled: true
system_prompt: "You are a helpful assistant."
```

## Migration Guide

### Migrating to New Versions

When upgrading Hrisa Code, follow the migration guide to ensure compatibility and take advantage of new features.

#### Breaking Changes in v2.0

- **Configuration File Format**:
  The configuration file format has changed from JSON to YAML.
  - **Old Configuration (`config.json`)**:
    ```json
    {
      "model": {
        "name": "qwen2.5:72b",
        "temperature": 0.7,
        "top_p": 0.9,
        "top_k": 40
      },
      "ollama": {
        "host": "http://localhost:8000"
      },
      "tools": {
        "enabled": true
      },
      "system_prompt": "You are a helpful assistant."
    }
    ```
  - **New Configuration (`config.yaml`)**:
    ```yaml
    model:
      name: qwen2.5:72b
      temperature: 0.7
      top_p: 0.9
      top_k: 40
    ollama:
      host: http://localhost:8000
    tools:
      enabled: true
    system_prompt: "You are a helpful assistant."
    ```

- **Tool Registration**:
  Tools are now registered using a JSON schema instead of a list.
  - **Old Tool Registration (`tools.py`)**:
    ```python
    AVAILABLE_TOOLS = {
        "read_file": read_file,
        "execute_command": execute_command
    }
    ```
  - **New Tool Registration (`tools.py`)**:
    ```python
    AVAILABLE_TOOLS = [
        {
            "tool": "read_file",
            "description": "Reads the content of a specified file.",
            "params": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to be read."
                }
            },
            "return_type": "string"
        },
        {
            "tool": "execute_command",
            "description": "Executes a shell command.",
            "params": {
                "command": {
                    "type": "string",
                    "description": "Shell command to execute."
                }
            },
            "return_type": "str"
        }
    ]
    ```

By following this migration guide, you can ensure a smooth upgrade process and take full advantage of the latest features in Hrisa Code.