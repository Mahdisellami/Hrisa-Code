# Quick Start Guide

## Installation

### 1. Install Ollama

First, install Ollama from [ollama.ai](https://ollama.ai/):

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Or download from https://ollama.ai/download
```

### 2. Start Ollama

```bash
ollama serve
```

### 3. Pull a Model

```bash
# Recommended for coding
ollama pull qwen2.5:72b

# Or try these alternatives
ollama pull qwen2.5-coder:32b
ollama pull deepseek-coder
ollama pull mistral
```

### 4. Install Hrisa Code

```bash
cd Hrisa-Code
pip install -e .
```

### 5. Initialize Configuration

```bash
# Create a configuration file
hrisa init

# Or use global config
hrisa init --global
```

### 6. Start Chatting

```bash
hrisa chat
```

## First Steps

Once in the chat:

1. Try asking about your code:
   ```
   > Can you read and explain the file src/main.py?
   ```

2. Request file operations:
   ```
   > Create a new file called hello.py with a simple hello world function
   ```

3. Execute commands:
   ```
   > Run pytest to check if all tests pass
   ```

4. Search your codebase:
   ```
   > Find all files that contain the word "TODO"
   ```

## Configuration

Edit `.hrisa/config.yaml` to customize:

```yaml
model:
  name: qwen2.5:72b
  temperature: 0.7

tools:
  enable_file_operations: true
  enable_command_execution: true
```

## Troubleshooting

### "Connection refused" error

Make sure Ollama is running:
```bash
ollama serve
```

### "Model not found" error

Pull the model you want to use:
```bash
ollama pull codellama
```

### Check what models you have

```bash
hrisa models
# or
ollama list
```

## Next Steps

- Read the [Architecture Guide](ARCHITECTURE.md) to understand how it works
- Check out [examples/](../examples/) for configuration examples
- Try different models to see which works best for your use case
