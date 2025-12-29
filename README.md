# hrisa-code

A CLI coding assistant powered by local LLMs via Ollama

## Table of Contents
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Development](#development)
- [License](#license)

## Features

This tool provides a comprehensive CLI interface for interacting with local LLMs via Ollama, offering commands to initialize configurations, generate documentation, and manage models. It supports both traditional and progressive context-building approaches for generating detailed README, API, and contributor guidelines documents.

- **chat**: Start an interactive chat session with the coding assistant.
- **models**: List available Ollama models.
- **init**: Initialize Hrisa Code configuration and generate HRISA.md documentation.
- **readme**: Generate user-friendly README.md documentation.
- **contributing**: Generate comprehensive CONTRIBUTING.md contributor guidelines.
- **readme_progressive**: Generate README.md using progressive context-building (NEW APPROACH).
- **api_progressive**: Generate API.md using progressive context-building (NEW APPROACH).
- **contributing_progressive**: Generate CONTRIBUTING.md using progressive context-building (NEW APPROACH).
- **hrisa_progressive**: Generate HRISA.md using progressive context-building (NEW APPROACH).
- **api**: Generate comprehensive API.md reference documentation (OLD APPROACH).

## Prerequisites

- Python >=3.10
- pip package manager
- Runs entirely on your local machine using Ollama.
- No cloud-based costs or privacy concerns.
- Supports a variety of open-source models like qwen2.5, deepseek-coder, and codellama.
- Multi-model orchestration for optimized task performance.
- Basic CLI interface for running the assistant.
- Interactive chat sessions with multi-turn tool calling.
- Comprehensive set of tools for file operations (read, write, list, search).
- Git integration for repository management (status, diff, log, branch).
- Generates HRISA.md, README.md, CONTRIBUTING.md, and API.md with multi-step orchestration.
- Supports multi-model orchestration for better quality documentation.
- Autonomous task execution with background task support.
- Loop detection and goal tracking for efficient workflow management.
- Easy setup using Make or manual commands.
- Comprehensive testing, linting, and type-checking tools.
- **Ollama Connection Issues**:
- **Model Not Found**:
- Licensed under the MIT License.
- Inspired by Claude Code from Anthropic.
- Uses Ollama for LLM inference, Typer for CLI, and Rich for UI.

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/hrisa-code.git
cd hrisa-code

# Install dependencies
pip install -e ".[dev]"
```

## Usage

Start by running the `chat` command to interact with Hrisa Code for coding assistance. Use the `init` command to generate essential project documentation such as README.md and CONTRIBUTING.md.

### Commands

```bash
# Start an interactive chat session with the coding assistant.
hrisa-code chat
```

```bash
# List available Ollama models.
hrisa-code models
```

```bash
# Initialize Hrisa Code configuration and generate HRISA.md documentation.
hrisa-code init
```

```bash
# Generate user-friendly README.md documentation.
hrisa-code readme
```

```bash
# Generate comprehensive CONTRIBUTING.md contributor guidelines.
hrisa-code contributing
```

```bash
# Generate README.md using progressive context-building (NEW APPROACH).
hrisa-code readme_progressive
```

```bash
# Generate API.md using progressive context-building (NEW APPROACH).
hrisa-code api_progressive
```

```bash
# Generate CONTRIBUTING.md using progressive context-building (NEW APPROACH).
hrisa-code contributing_progressive
```

```bash
# Generate HRISA.md using progressive context-building (NEW APPROACH).
hrisa-code hrisa_progressive
```

```bash
# Generate comprehensive API.md reference documentation (OLD APPROACH).
hrisa-code api
```

## Development

See CONTRIBUTING.md for development guidelines.

## License

MIT License
