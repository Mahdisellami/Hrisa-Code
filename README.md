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

This tool offers a robust CLI interface for interacting with local LLMs via Ollama, enabling users to generate various documentation files and manage configurations efficiently. It includes commands for initializing the project, generating READMEs, API references, and contributor guidelines using both traditional and progressive context-building approaches.

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

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/hrisa-code.git
cd hrisa-code

# Install dependencies
pip install -e ".[dev]"
```

## Usage

Start by running the `chat` command to interact with the coding assistant, or use the `models` command to list available Ollama models. For initialization and documentation generation, commands like `init`, `readme`, and `contributing` provide a streamlined setup process.

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

### Execution Modes

The interactive chat session supports three execution modes that you can cycle through using SHIFT+TAB or the `/agent` command:

#### Normal Mode (Default)
Standard conversation with the LLM. Tools are available but no autonomous behavior. The assistant responds to each message individually.

#### Agent Mode
Autonomous multi-step execution. The agent will:
- Break down complex tasks automatically
- Explore the codebase proactively
- Execute multiple steps until completion
- Self-reflect and adapt its approach

Use this mode for tasks requiring multiple independent actions.

#### Plan Mode
Plan-driven execution with intelligent progress tracking. The system will:
- Analyze task complexity automatically
- Generate a step-by-step execution plan
- Execute steps with visual progress feedback
- Adapt the plan based on discoveries during execution
- Handle errors with recovery strategies

Use this mode for complex tasks that benefit from upfront planning and structured execution.

To switch modes:
1. Press SHIFT+TAB in the chat interface
2. Or type `/agent` to cycle: normal → agent → plan → normal
3. Each mode automatically resets to normal after completing a task

## Development

See CONTRIBUTING.md for development guidelines.

## License

MIT License
