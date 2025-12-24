# Architecture Guide

## Overview

Hrisa Code is designed as a modular CLI application that connects local LLMs (via Ollama) with file system operations and command execution.

## High-Level Architecture

```
┌─────────────┐
│     CLI     │  (Typer + Rich)
└──────┬──────┘
       │
       v
┌─────────────────┐
│  Interactive    │
│    Session      │
└──────┬──────────┘
       │
       v
┌─────────────────┐
│  Conversation   │
│    Manager      │
└──────┬──────────┘
       │
       ├──────────────┬─────────────┐
       v              v             v
┌──────────┐   ┌──────────┐  ┌──────────┐
│  Ollama  │   │  Tools   │  │  Config  │
│  Client  │   │  System  │  │  Manager │
└──────────┘   └──────────┘  └──────────┘
       │              │
       v              v
┌──────────┐   ┌──────────────┐
│  Ollama  │   │ File System  │
│  Server  │   │ + Shell      │
└──────────┘   └──────────────┘
```

## Core Components

### 1. CLI Layer (`cli.py`)

Entry point for the application. Built with Typer for elegant command-line interfaces.

**Responsibilities:**
- Parse command-line arguments
- Handle top-level commands (`chat`, `models`, `init`)
- Display help and version information

**Key Commands:**
```python
hrisa chat [--model MODEL] [--working-dir DIR]
hrisa models [--host HOST]
hrisa init [--global]
```

### 2. Interactive Session (`core/interactive.py`)

Manages the user interaction loop and command handling.

**Responsibilities:**
- Display welcome and help messages
- Handle user input with prompt toolkit
- Route special commands (`/help`, `/clear`, `/save`)
- Coordinate with ConversationManager for LLM interactions

**Features:**
- Command history (stored in `~/.hrisa/history.txt`)
- Auto-suggestions from history
- Rich formatting for output

### 3. Conversation Manager (`core/conversation.py`)

Orchestrates the conversation flow and tool execution.

**Responsibilities:**
- Manage conversation state
- Execute tool calls requested by the LLM
- Format and display tool results
- Save/load conversation history

**Key Methods:**
```python
async def process_message(user_message: str) -> str
async def process_message_stream(user_message: str)
def clear_history()
def save_conversation(file_path: Path)
```

### 4. Ollama Client (`core/ollama_client.py`)

Handles all communication with the Ollama server.

**Responsibilities:**
- Make API calls to Ollama
- Manage conversation history
- Stream responses
- Handle model configuration

**Key Methods:**
```python
async def chat(message: str, system_prompt: str, tools: List)
async def chat_stream(message: str, system_prompt: str, tools: List)
async def list_models()
```

**Configuration:**
```python
OllamaConfig(
    model: str,
    host: str,
    temperature: float,
    top_p: float,
    top_k: int
)
```

### 5. Configuration Manager (`core/config.py`)

Manages application configuration with a fallback chain.

**Configuration Priority:**
1. Project-specific: `.hrisa/config.yaml`
2. User-level: `~/.config/hrisa-code/config.yaml`
3. Defaults

**Structure:**
```python
Config:
  - model: ModelConfig
  - ollama: OllamaServerConfig
  - tools: ToolsConfig
  - system_prompt: Optional[str]
```

### 6. Tools System (`tools/file_operations.py`)

Extensible tool system for various operations.

**Current Tools:**
- `read_file`: Read file contents with optional line ranges
- `write_file`: Write content to files
- `list_directory`: List directory contents
- `execute_command`: Run shell commands
- `search_files`: Search for patterns in files

**Tool Definition Format:**
```python
{
    "type": "function",
    "function": {
        "name": "tool_name",
        "description": "What the tool does",
        "parameters": {
            "type": "object",
            "properties": {...},
            "required": [...]
        }
    }
}
```

## Data Flow

### 1. User Input Flow

```
User Input
    ↓
Interactive Session (validates input)
    ↓
Is it a command? → Yes → Handle Command
    ↓ No
Conversation Manager
    ↓
Ollama Client (sends to LLM)
    ↓
LLM Response (may include tool calls)
    ↓
Conversation Manager (executes tools)
    ↓
Display Response
```

### 2. Tool Execution Flow

```
LLM requests tool execution
    ↓
Conversation Manager parses request
    ↓
Look up tool in AVAILABLE_TOOLS
    ↓
Execute tool with parameters
    ↓
Capture result
    ↓
Display to user
    ↓
Send result back to LLM (for context)
```

## Configuration System

### Configuration Loading

```python
def load_with_fallback(project_dir: Optional[Path]) -> Config:
    # 1. Try project config
    if project_dir:
        project_config = project_dir / ".hrisa" / "config.yaml"
        if project_config.exists():
            return load(project_config)

    # 2. Try user config
    user_config = Path.home() / ".config" / "hrisa-code" / "config.yaml"
    if user_config.exists():
        return load(user_config)

    # 3. Use defaults
    return Config()
```

### Configuration Override

Command-line arguments can override config file settings:

```bash
# Uses model from config
hrisa chat

# Overrides model
hrisa chat --model deepseek-coder
```

## Extensibility

### Adding New Tools

1. Create a new tool class in `tools/`:

```python
class MyNewTool:
    @staticmethod
    def get_definition() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "my_tool",
                "description": "What it does",
                "parameters": {...}
            }
        }

    @staticmethod
    def execute(**kwargs) -> str:
        # Implementation
        return result
```

2. Register it in `AVAILABLE_TOOLS`:

```python
AVAILABLE_TOOLS = {
    "my_tool": MyNewTool,
    # ... other tools
}
```

### Adding New Commands

Add a new command in `cli.py`:

```python
@app.command()
def mycommand(
    arg: str = typer.Argument(...),
) -> None:
    """Description of the command."""
    # Implementation
```

## Future Enhancements

### 1. MCP Integration

Planned integration with Model Context Protocol for:
- Standardized tool definitions
- Better interoperability
- Enhanced capabilities

### 2. Advanced Context Management

- Automatic detection of relevant files
- Smart context window management
- Project structure awareness

### 3. Multi-Agent System

- Specialized agents for different tasks
- Agent coordination
- Parallel task execution

### 4. Plugin System

- Dynamic tool loading
- User-defined tools
- Community plugin marketplace

## Security Considerations

### Command Execution

- Commands run in user context
- No sandboxing (yet)
- Timeout protection (30s default)

**Recommendations:**
- Review commands before execution
- Use in trusted environments
- Don't run as root

### File Operations

- Limited to working directory and subdirectories
- File size limits (10MB default)
- No automatic destructive operations

### API Security

- Local-only Ollama connection by default
- No credentials stored
- Configuration files in user space

## Performance Considerations

### Response Speed

Depends on:
- Model size (larger = slower but smarter)
- Hardware (GPU vs CPU)
- Context window size

**Optimization:**
- Use smaller models for quick tasks
- Stream responses for better UX
- Limit conversation history

### Memory Usage

- Conversation history kept in memory
- Models loaded by Ollama
- Typical usage: 50-100MB (app) + model size

## Testing Strategy

### Unit Tests
- Tool execution
- Configuration loading
- Message formatting

### Integration Tests
- CLI commands
- Ollama connectivity
- File operations

### Manual Testing
- Interactive sessions
- Various models
- Edge cases

## Monitoring and Debugging

### Logging

Currently minimal. Future additions:
- Debug mode
- Request/response logging
- Performance metrics

### Error Handling

- Connection errors → User-friendly messages
- Tool failures → Graceful degradation
- LLM errors → Retry logic

## Contributing

See the architecture when contributing:
1. Follow existing patterns
2. Add tools to the tools system
3. Keep CLI simple
4. Maintain modularity
5. Document new components
