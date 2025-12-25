# Hrisa Code

A CLI coding assistant powered by local LLMs via Ollama. Inspired by Claude Code, but running entirely on your machine with your choice of open-source models.

## Features

- **Local LLM Integration**: Uses Ollama to run models like CodeLlama, DeepSeek Coder, Mistral, and more
- **Interactive Chat**: Natural conversation interface for coding assistance
- **Multi-Turn Tool Calling**: Claude Code-style autonomous multi-step task completion
- **Agent Mode**: Autonomous agent for complex multi-step tasks with reflection and error recovery
- **Text-Based Tool Parsing**: Compatible with models like qwen2.5-coder:32b that output tool calls as text
- **HRISA.md Generation**: Automated comprehensive repository documentation with multi-step orchestration
- **Background Tasks**: Execute long-running commands asynchronously with process management
- **File Operations**: Read, write, and search files in your project
- **Command Execution**: Run shell commands with assistant guidance
- **Flexible Configuration**: Project-specific or global configuration files
- **Rich Terminal UI**: Beautiful output with syntax highlighting and structured displays
- **Conversation History**: Save and load previous sessions
- **Tool Calling**: Extensible tool system for adding new capabilities

## Prerequisites

- Python 3.10 or higher
- [Ollama](https://ollama.ai/) installed and running
- At least one LLM model pulled in Ollama (e.g., `codellama`, `deepseek-coder`)

## Installation

Choose your preferred installation method:

### Option 1: Docker (Recommended for Beginners)

Complete isolated environment with Ollama included:

```bash
# Clone the repository
git clone https://github.com/yourusername/Hrisa-Code.git
cd Hrisa-Code

# Start services
make docker-up

# Pull models
make docker-pull

# Start chatting!
make docker-chat
```

See [docs/DOCKER.md](docs/DOCKER.md) for detailed Docker usage.

### Option 2: Local Installation with venv

```bash
# Clone the repository
git clone https://github.com/yourusername/Hrisa-Code.git
cd Hrisa-Code

# Set up virtual environment and install
make setup

# Or manually:
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

### Option 3: Local Installation with uv (Fast)

```bash
# Clone the repository
git clone https://github.com/yourusername/Hrisa-Code.git
cd Hrisa-Code

# Set up with uv
make setup-uv

# Or manually:
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

### Quick Start (Local Installation)

After local installation:

```bash
# 1. Make sure Ollama is running
ollama serve

# 2. Pull a coding model (if you haven't already)
ollama pull codellama

# 3. Initialize configuration (optional)
hrisa init

# 4. Start chatting!
hrisa chat
```

## Usage

### Quick Commands with Make

```bash
# Local development
make setup              # Set up venv
make test               # Run tests
make format             # Format code
make lint               # Lint code

# Docker
make docker-up          # Start services
make docker-chat        # Start chat
make docker-models      # List models
make docker-down        # Stop services
```

### Interactive Chat

Start an interactive coding session:

```bash
# Local installation
hrisa chat

# Docker
make docker-chat

# With specific model
hrisa chat --model deepseek-coder
make docker-chat MODEL=deepseek-coder

# Use a specific working directory
hrisa chat --working-dir /path/to/project
```

### Commands

Within the chat session:

- `/help` - Show available commands
- `/clear` - Clear conversation history
- `/save` - Save conversation to file
- `/config` - Show current configuration
- `/exit` - Exit the session (or press Ctrl+D)

### List Available Models

```bash
# List all Ollama models
hrisa models

# Connect to Ollama on a different host
hrisa models --host http://192.168.1.100:11434
```

### Initialize Configuration

```bash
# Create project-specific config (.hrisa/config.yaml)
hrisa init

# Create global config (~/.config/hrisa-code/config.yaml)
hrisa init --global
```

## Configuration

Hrisa Code looks for configuration in this order:

1. Project-specific: `.hrisa/config.yaml`
2. User-level: `~/.config/hrisa-code/config.yaml`
3. Default settings

Example configuration:

```yaml
model:
  name: codellama
  temperature: 0.7
  top_p: 0.9
  top_k: 40

ollama:
  host: http://localhost:11434
  timeout: 300

tools:
  enable_file_operations: true
  enable_command_execution: true
  enable_search: true
  command_timeout: 30
  max_file_size_mb: 10
```

See `examples/config.example.yaml` for a complete configuration file.

## Architecture

Hrisa Code is built with a modular architecture:

```
src/hrisa_code/
├── cli.py                 # CLI entry point
├── core/
│   ├── ollama_client.py   # Ollama API client
│   ├── conversation.py    # Conversation management
│   ├── interactive.py     # Interactive session handler
│   └── config.py          # Configuration management
├── tools/
│   └── file_operations.py # File and command tools
└── mcp/
    └── ...                # MCP integration (future)
```

### Key Components

- **OllamaClient**: Handles communication with Ollama, manages conversation history
- **ConversationManager**: Orchestrates tool execution and LLM interaction
- **InteractiveSession**: Manages the user interface and command handling
- **Tools**: Extensible system for file operations, command execution, and more

## Recommended Models

For coding tasks, these models work well:

- **codellama** (7B, 13B, 34B): General purpose coding
- **deepseek-coder** (6.7B, 33B): Strong coding capabilities
- **mistral**: Good general purpose model
- **llama3**: Latest Meta model with strong reasoning

Pull a model:

```bash
ollama pull codellama
ollama pull deepseek-coder
```

## Development

### Setup Development Environment

**Using Make (Recommended):**

```bash
# Set up environment
make setup              # or: make setup-uv

# Run tests
make test
make test-cov          # with coverage

# Code quality
make format            # Format with black
make lint              # Lint with ruff
make type-check        # Type check with mypy
make check             # Run all checks

# Clean up
make clean
```

**Manual Commands:**

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type checking
mypy src/
```

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for complete development guide.

### Project Structure

```
Hrisa-Code/
├── src/hrisa_code/        # Main package
├── tests/                 # Test files
├── docs/                  # Documentation
├── examples/              # Example configs and scripts
├── pyproject.toml         # Project metadata and dependencies
└── README.md              # This file
```

## Roadmap

### Completed ✅
- [x] Basic CLI interface
- [x] Ollama integration
- [x] File operation tools
- [x] Interactive chat session
- [x] Configuration system
- [x] Multi-turn tool calling (Claude Code style)
- [x] Agent mode with autonomous task execution
- [x] Background task execution
- [x] HRISA.md generation with orchestration
- [x] Text-based tool call parsing

### In Progress 🔄
- [ ] Full MCP (Model Context Protocol) integration
- [ ] Enhanced tool calling with streaming
- [ ] Git integration tools
- [ ] Code analysis tools

### Future Work 🚀
- [ ] **Meta-Orchestration System** - General-purpose workflow orchestration
  - [ ] Complexity detection module
  - [ ] Dynamic planning module
  - [ ] Adaptive execution engine
- [ ] Project context awareness
- [ ] Multi-file editing capabilities
- [ ] Plugin system for custom tools

**See [FUTURE.md](FUTURE.md) for detailed architecture and implementation plans!**

## Comparison with Claude Code

| Feature | Hrisa Code | Claude Code |
|---------|------------|-------------|
| LLM Provider | Local (Ollama) | Anthropic (Claude) |
| Cost | Free | Pay per use |
| Privacy | Fully local | Cloud-based |
| Models | Open source | Proprietary |
| Speed | Depends on hardware | Fast (cloud) |
| Offline | Yes | No |
| Tool System | Basic | Advanced |

## Troubleshooting

### Ollama Connection Issues

```bash
# Check if Ollama is running
ollama list

# Start Ollama server
ollama serve

# Test connection
curl http://localhost:11434/api/tags
```

### Model Not Found

```bash
# List available models
ollama list

# Pull a model
ollama pull codellama
```

### Configuration Issues

```bash
# Check current configuration
hrisa chat
# Then use /config command

# Recreate configuration
hrisa init --global
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Inspired by [Claude Code](https://claude.com/claude-code) from Anthropic
- Built with [Ollama](https://ollama.ai/) for local LLM inference
- Uses [Typer](https://typer.tiangolo.com/) for the CLI
- UI powered by [Rich](https://rich.readthedocs.io/)

## Links

- [Ollama Documentation](https://github.com/ollama/ollama)
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- [Aider](https://github.com/paul-gauthier/aider) - Another excellent local coding assistant
