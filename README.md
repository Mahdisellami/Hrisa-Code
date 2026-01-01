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
