# hrisa-code API Reference

A CLI coding assistant powered by local LLMs via Ollama

## API Overview

This document provides comprehensive API documentation for developers, integrators, and extension authors.

### Quick Links
- [CLI Reference](#cli-reference)
- [Tools Reference](#tools-reference)
- [Core API Reference](#core-api-reference)
- [Configuration Reference](#configuration-reference)
- [Extension Guide](#extension-guide)

## CLI Reference

### Command: `chat`

**Description**: Start an interactive chat session with the coding assistant.

**Usage**:
```bash
hrisa-code chat [OPTIONS]
```

### Command: `models`

**Description**: List available Ollama models.

**Usage**:
```bash
hrisa-code models [OPTIONS]
```

### Command: `init`

**Description**: Initialize Hrisa Code configuration and generate HRISA.md documentation.

**Usage**:
```bash
hrisa-code init [OPTIONS]
```

### Command: `readme`

**Description**: Generate user-friendly README.md documentation.

**Usage**:
```bash
hrisa-code readme [OPTIONS]
```

### Command: `contributing`

**Description**: Generate comprehensive CONTRIBUTING.md contributor guidelines.

**Usage**:
```bash
hrisa-code contributing [OPTIONS]
```

### Command: `readme_progressive`

**Description**: Generate README.md using progressive context-building (NEW APPROACH).

**Usage**:
```bash
hrisa-code readme_progressive [OPTIONS]
```

### Command: `api_progressive`

**Description**: Generate API.md using progressive context-building (NEW APPROACH).

**Usage**:
```bash
hrisa-code api_progressive [OPTIONS]
```

### Command: `contributing_progressive`

**Description**: Generate CONTRIBUTING.md using progressive context-building (NEW APPROACH).

**Usage**:
```bash
hrisa-code contributing_progressive [OPTIONS]
```

### Command: `hrisa_progressive`

**Description**: Generate HRISA.md using progressive context-building (NEW APPROACH).

**Usage**:
```bash
hrisa-code hrisa_progressive [OPTIONS]
```

### Command: `api`

**Description**: Generate comprehensive API.md reference documentation (OLD APPROACH).

**Usage**:
```bash
hrisa-code api [OPTIONS]
```

## Tools Reference

### Available Tools

The system provides the following tools for file operations, git integration, and command execution:

#### `GitStatusTool`

**Source**: `git_operations.py`

**Description**: Tool for checking git repository status.

#### `GitDiffTool`

**Source**: `git_operations.py`

**Description**: Tool for showing git differences.

#### `GitLogTool`

**Source**: `git_operations.py`

**Description**: Tool for viewing git commit history.

#### `GitBranchTool`

**Source**: `git_operations.py`

**Description**: Tool for managing git branches.

#### `GitCommitTool`

**Source**: `git_operations.py`

**Description**: Tool for creating git commits.

#### `GitPushTool`

**Source**: `git_operations.py`

**Description**: Tool for pushing commits to remote repository.

#### `GitPullTool`

**Source**: `git_operations.py`

**Description**: Tool for pulling changes from remote repository.

#### `GitStashTool`

**Source**: `git_operations.py`

**Description**: Tool for stashing uncommitted changes.

#### `ReadFileTool`

**Source**: `file_operations.py`

**Description**: Tool for reading file contents.

#### `WriteFileTool`

**Source**: `file_operations.py`

**Description**: Tool for writing to files.

#### `ListDirectoryTool`

**Source**: `file_operations.py`

**Description**: Tool for listing directory contents.

#### `ExecuteCommandTool`

**Source**: `file_operations.py`

**Description**: Tool for executing shell commands.

#### `SearchFilesTool`

**Source**: `file_operations.py`

**Description**: Tool for searching files using grep.

#### `FindFilesTool`

**Source**: `file_operations.py`

**Description**: Tool for finding files by name pattern (not content).

#### `DeleteFileTool`

**Source**: `file_operations.py`

**Description**: Tool for deleting files.

## Core API Reference

The core API consists of several key modules:

### Module: `hrisa_code.core.config`

Configuration management with Pydantic models

See source code at `src/hrisa_code/core/config.py` for complete API details.

### Module: `hrisa_code.core.conversation`

Conversation orchestration and tool execution

See source code at `src/hrisa_code/core/conversation.py` for complete API details.

### Module: `hrisa_code.core.ollama_client`

Async Ollama API client

See source code at `src/hrisa_code/core/ollama_client.py` for complete API details.

### Module: `hrisa_code.core.agent`

Autonomous task execution

See source code at `src/hrisa_code/core/agent.py` for complete API details.

### Module: `hrisa_code.core.task_manager`

Background process management

See source code at `src/hrisa_code/core/task_manager.py` for complete API details.

### Usage

Import core classes directly from hrisa_code.core to utilize the project's fundamental components such as config, conversation, ollama_client, agent, and task_manager in your application. Developers can then instantiate and configure these modules to integrate seamlessly with their existing codebase, leveraging the predefined functionalities for configuration management, conversational flows, client interactions, agent operations, and task handling.

## Configuration Reference

### Configuration File Locations

Configuration is loaded from:
1. Project-specific: `.hrisa/config.yaml`
2. User-level: `~/.config/hrisa-code/config.yaml`
3. Default settings (built-in)

### Configuration Sections

#### Model Configuration

- `name`: Model name (e.g., qwen2.5:72b)
- `temperature`: Temperature for generation (0.0-1.0)
- `top_p`: Top-p sampling parameter
- `top_k`: Top-k sampling parameter

#### Ollama Configuration

- `host`: Ollama server URL (default: http://localhost:11434)
- `timeout`: Request timeout in seconds

#### Tools Configuration

- `enable_file_operations`: Enable file read/write tools
- `enable_command_execution`: Enable shell command execution
- `enable_search`: Enable search operations

### Example Configuration

```yaml
model:
  name: qwen2.5:72b
  temperature: 0.7
  top_p: 0.9
  top_k: 40

ollama:
  host: http://localhost:11434
  timeout: 300

tools:
  enable_file_operations: true
  enable_command_execution: true
```

## Extension Guide

See CONTRIBUTING.md for information on extending the API.

## Error Handling

Common exceptions and error codes will be documented here.
