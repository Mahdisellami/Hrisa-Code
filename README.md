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

## Development

See CONTRIBUTING.md for development guidelines.

## License

MIT License
