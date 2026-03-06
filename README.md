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
- Ollama (for local LLM execution)
- Git (optional, for version control operations)

## Installation

### Quick Setup (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/hrisa-code.git
cd hrisa-code

# Run platform-specific setup script
# macOS/Linux:
make setup

# Windows (PowerShell):
.\scripts\setup-windows.ps1

# Windows (CMD):
.\scripts\setup-windows.bat
```

### Manual Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Run setup wizard
hrisa setup
```

## Usage

### Initial Setup

After installation, run the comprehensive setup wizard:

```bash
# Interactive setup (recommended for first-time users)
hrisa setup

# Auto-install everything without prompting
hrisa setup --auto-install

# Specify models to install
hrisa setup --models "qwen2.5-coder:7b,qwen2.5:72b"
```

The setup wizard will:
- Verify Python, Git, Curl, and Docker installations
- Check Ollama installation and service status
- Install PDF libraries for document support
- Pull required Ollama models
- Provide platform-specific fix commands for any issues

### Core Commands

```bash
# Run pre-flight checks
hrisa check

# Start an interactive chat session
hrisa chat

# List available Ollama models
hrisa models

# Initialize configuration and generate HRISA.md
hrisa init
```

### Web UI (NEW!)

Manage multiple GenAI agents through a visual web interface:

#### Local Installation

```bash
# Install web dependencies
pip install -e ".[web]"

# Start the web UI server
hrisa web

# Access the dashboard
open http://localhost:8000
```

#### Docker Deployment (Recommended)

Deploy with Docker Compose for a complete setup with Ollama:

```bash
# Quick start - deploys Ollama + Web UI
./deploy.sh start

# Pull recommended models
./deploy.sh pull-models

# Access the web UI
open http://localhost:8000
```

See [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) for complete Docker guide.

**Features:**
- 🤖 Create and manage multiple agents simultaneously
- ⏱️ Real-time progress tracking with WebSocket updates
- 🔴 Automatic stuck detection (alerts when agents need help)
- 💬 Send instructions to guide stuck agents
- 📊 Visual dashboard with statistics and filters
- 📝 View complete conversation history and outputs

See [docs/WEB_UI.md](docs/WEB_UI.md) for complete documentation.

**Quick Example:**
1. Start server: `hrisa web` (or `./deploy.sh start` for Docker)
2. Open browser to http://localhost:8000
3. Click "Create New Agent"
4. Enter task: "Generate comprehensive README.md"
5. Watch real-time progress on dashboard
6. Send instructions if agent gets stuck

```bash
# Generate user-friendly README.md documentation
hrisa readme

# Generate comprehensive CONTRIBUTING.md contributor guidelines
hrisa contributing

# Generate comprehensive API.md reference documentation
hrisa api

# Generate README.md using progressive context-building (NEW)
hrisa readme_progressive

# Generate API.md using progressive context-building (NEW)
hrisa api_progressive

# Generate CONTRIBUTING.md using progressive context-building (NEW)
hrisa contributing_progressive

# Generate HRISA.md using progressive context-building (NEW)
hrisa hrisa_progressive
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

#### Plan Mode (NEW - Q2 2025 Enhancements)
Plan-driven execution with intelligent progress tracking and optimized efficiency. The system will:
- Analyze task complexity automatically (SIMPLE/MODERATE/COMPLEX)
- Generate a step-by-step execution plan with clear rationale
- Execute steps with animated visual feedback (spinners for all operations)
- Pass previous step results to next steps (40-50% reduction in redundant tool calls)
- Validate tool parameters before execution (70% reduction in errors)
- Adapt the plan based on discoveries during execution
- Handle errors with recovery strategies
- Display persistent mode indicator in bottom status bar

**Recent Improvements (v0.2.0):**
- **Step Context Passing**: Each step receives results from previous steps, eliminating redundant searches
- **Parameter Checklists**: Built-in validation reduces tool call errors by 70%
- **Enhanced Heuristics**: 8 task-specific patterns (analyze, implement, find, fix, refactor, optimize, document, test)
- **Quality Validation**: Rejects poor quality plans, ensures multi-step decomposition
- **Visual Feedback**: Animated spinners for all LLM operations, persistent mode display

**Performance Metrics:**
- Tool calls per task: Reduced from 6-8 to 3-4 (40-50% improvement)
- Parameter errors: Reduced from 2-3 to 0-1 per task (70% improvement)
- Self-correction rounds: Reduced from 2-3 to 1 per step (60% improvement)

Use this mode for complex tasks that benefit from upfront planning and structured execution.

To switch modes:
1. Press SHIFT+TAB in the chat interface
2. Or type `/agent` to cycle: normal → agent → plan → normal
3. Mode persists until you manually switch (no auto-reset)

### Plan Mode User Guide

#### When to Use Plan Mode

Plan Mode is ideal for tasks that:
- Require multiple steps to complete
- Benefit from upfront planning and structure
- Involve exploration followed by analysis
- Need coordination across multiple files
- Have clear success criteria

**Good Examples:**
```
"Find all TODO comments in the codebase and summarize them"
"Refactor the authentication module for better testability"
"Optimize the database query performance"
"Add comprehensive documentation to the API endpoints"
"Write tests for the user service"
```

#### What to Expect

1. **Complexity Analysis** (2-3 seconds)
   - System analyzes your task
   - Determines complexity: SIMPLE, MODERATE, or COMPLEX
   - Decides on number of steps needed

2. **Plan Generation** (3-5 seconds)
   - Creates step-by-step execution plan
   - Each step has clear purpose and expected tools
   - Shows dependencies between steps

3. **Step Execution** (variable time)
   - Visual spinner shows current activity
   - Each step uses results from previous steps
   - No redundant searches or operations
   - Progress displayed in real-time

4. **Completion**
   - Final summary of what was accomplished
   - All step results compiled
   - Mode remains active for next task

#### Tips for Best Results

- **Be specific**: "Find TODO comments in src/" vs "Look at code"
- **State the goal clearly**: What outcome do you want?
- **Use action verbs**: find, analyze, refactor, optimize, document, test
- **Watch the bottom toolbar**: Shows current mode at all times
- **Trust the process**: Spinners indicate active work, even if no output yet

#### Understanding Plan Steps

Plans typically follow these patterns:

**Find/Search Tasks** (3 steps):
1. Locate files matching criteria
2. Extract and analyze content
3. Compile and summarize findings

**Refactor Tasks** (3-4 steps):
1. Analyze current implementation
2. Design improved structure
3. Implement refactoring
4. Verify functionality preserved (if MODERATE/COMPLEX)

**Optimization Tasks** (3-4 steps):
1. Profile and identify bottlenecks
2. Design optimization strategy
3. Implement optimizations
4. Measure improvements (if MODERATE/COMPLEX)

**Documentation Tasks** (3 steps):
1. Review code and identify gaps
2. Analyze code behavior
3. Write comprehensive documentation

**Testing Tasks** (4 steps):
1. Analyze code to test
2. Design test cases
3. Implement tests
4. Run and verify coverage

## Development

See CONTRIBUTING.md for development guidelines.

## License

MIT License
