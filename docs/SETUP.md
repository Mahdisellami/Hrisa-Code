# Hrisa Code Setup Guide

Comprehensive guide for installing and setting up Hrisa Code on macOS, Linux, and Windows.

## Table of Contents

- [Quick Start](#quick-start)
- [Platform-Specific Setup](#platform-specific-setup)
  - [macOS](#macos)
  - [Linux](#linux)
  - [Windows](#windows)
- [Setup Wizard](#setup-wizard)
- [Manual Setup](#manual-setup)
- [Troubleshooting](#troubleshooting)

## Quick Start

The fastest way to get started with Hrisa Code:

```bash
# Clone the repository
git clone https://github.com/yourusername/hrisa-code.git
cd hrisa-code

# Run platform-specific setup
make setup              # macOS/Linux
.\scripts\setup-windows.ps1  # Windows PowerShell

# Run setup wizard
hrisa setup

# Start using Hrisa Code
hrisa chat
```

## Platform-Specific Setup

### macOS

#### Prerequisites

1. **Install Homebrew** (if not already installed):
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Install Python 3.10+**:
   ```bash
   brew install python@3.11
   ```

3. **Install Ollama**:
   ```bash
   brew install ollama
   # Or download from: https://ollama.ai/
   ```

#### Setup Script

```bash
cd hrisa-code
make setup              # Automated setup with venv
# Or: make setup-uv     # Faster setup with uv
```

#### What the Script Does

1. Checks Python version (3.10+ required)
2. Creates virtual environment in `venv/`
3. Installs all dependencies from `pyproject.toml`
4. Provides next steps guidance

#### Starting Ollama

```bash
# Start Ollama service (runs in background)
ollama serve

# Or install as a service (recommended)
brew services start ollama
```

### Linux

#### Prerequisites

1. **Install Python 3.10+**:
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install python3.11 python3.11-venv python3-pip

   # Fedora/RHEL
   sudo dnf install python3.11 python3-pip

   # Arch
   sudo pacman -S python python-pip
   ```

2. **Install Ollama**:
   ```bash
   curl https://ollama.ai/install.sh | sh
   ```

3. **Install Git** (if not present):
   ```bash
   # Ubuntu/Debian
   sudo apt install git

   # Fedora/RHEL
   sudo dnf install git

   # Arch
   sudo pacman -S git
   ```

#### Setup Script

```bash
cd hrisa-code
./scripts/setup-venv.sh   # Standard setup
# Or: ./scripts/setup-uv.sh  # Faster with uv
```

#### Starting Ollama

```bash
# Start as service (recommended)
sudo systemctl start ollama
sudo systemctl enable ollama  # Start on boot

# Or run manually
ollama serve
```

### Windows

#### Prerequisites

1. **Install Python 3.10+**:
   - Download from: https://www.python.org/downloads/
   - **Important**: Check "Add Python to PATH" during installation

2. **Install Ollama**:
   - Download installer from: https://ollama.ai/
   - Run installer and follow prompts

3. **Install Git** (optional but recommended):
   - Download from: https://git-scm.com/download/windows
   - Use default settings

#### Setup Scripts

**PowerShell (Recommended)**:
```powershell
cd hrisa-code
.\scripts\setup-windows.ps1
```

**Command Prompt**:
```cmd
cd hrisa-code
.\scripts\setup-windows.bat
```

#### Important Windows Notes

- **Execution Policy**: If PowerShell script fails, run:
  ```powershell
  Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```

- **Python Location**: Ensure Python is in PATH. Test with:
  ```cmd
  python --version
  ```

- **Virtual Environment Activation**:
  ```powershell
  # PowerShell
  .\venv\Scripts\Activate.ps1

  # CMD
  .\venv\Scripts\activate.bat
  ```

#### Starting Ollama

```cmd
# Open a separate terminal and run:
ollama serve

# Or use Windows Task Scheduler to auto-start
```

## Setup Wizard

After installing dependencies, run the comprehensive setup wizard:

### Interactive Mode (Recommended)

```bash
hrisa setup
```

The wizard will:
1. ✓ Check Python version (3.10+ required)
2. ✓ Verify Git installation
3. ✓ Check Curl availability
4. ✓ Detect Docker (optional)
5. ✓ Verify Ollama installation
6. ✓ Check if Ollama service is running
7. ✓ Prompt to install PDF libraries
8. ✓ Prompt to pull required models
9. ✓ Display summary with fix commands

### Auto-Install Mode

```bash
hrisa setup --auto-install
```

Automatically installs all missing dependencies without prompting.

### Specify Models

```bash
hrisa setup --models "qwen2.5-coder:7b,qwen2.5:72b"
```

Install specific Ollama models during setup.

### What Gets Checked

| Component | Type | Description |
|-----------|------|-------------|
| Python 3.10+ | Critical | Required to run Hrisa Code |
| Ollama | Critical | Required for local LLM execution |
| Ollama Service | Critical | Must be running to use Hrisa Code |
| Git | Optional | Needed for git operations |
| Curl | Optional | Used by Docker healthchecks |
| Docker | Optional | For containerized deployment |
| PDF Libraries | Optional | For document processing support |
| Ollama Models | Critical | At least one model required |

### Setup Output Example

```
══════════════════════════════════════
  Hrisa Code Setup
  Platform: darwin
  Mode: Interactive
══════════════════════════════════════

Step 1: System Dependencies
  ✓ Python Version - Already installed
  ✓ Git - Installed at /usr/bin/git
  ✓ Curl - Already installed
  ○ Docker (Optional) - Not found (optional)

Step 2: Ollama Setup
  ✓ Ollama - Installed at /usr/local/bin/ollama
  ✓ Ollama Service - Running

Step 3: Optional Libraries
  ✓ PDF Libraries - Already installed

Step 4: Ollama Models
  ✓ Ollama Models - Pulling qwen2.5-coder:7b...

Setup Summary
┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┓
┃ Component         ┃ Status   ┃ Notes              ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━┩
│ Python Version    │ ✓ Success│                    │
│ Git               │ ✓ Success│                    │
│ Curl              │ ✓ Success│                    │
│ Docker (Optional) │ ○ Skipped│ Not found          │
│ Ollama            │ ✓ Success│                    │
│ Ollama Service    │ ✓ Success│                    │
│ PDF Libraries     │ ✓ Success│ Already installed  │
│ Ollama Models     │ ✓ Success│                    │
└───────────────────┴──────────┴────────────────────┘

Setup complete! Hrisa Code is ready to use.

Next steps:
  1. Run hrisa init to generate configuration
  2. Run hrisa chat to start coding assistant
  3. See hrisa --help for all commands
```

## Manual Setup

If you prefer manual setup or the scripts don't work:

### 1. Create Virtual Environment

```bash
# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
.\venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install --upgrade pip
pip install -e ".[dev]"
```

### 3. Install Ollama

- **macOS**: `brew install ollama` or download from https://ollama.ai/
- **Linux**: `curl https://ollama.ai/install.sh | sh`
- **Windows**: Download installer from https://ollama.ai/

### 4. Start Ollama

```bash
ollama serve
```

### 5. Pull a Model

```bash
# Smaller model (good for most tasks)
ollama pull qwen2.5-coder:7b

# Larger models (better quality, more resources)
ollama pull qwen2.5-coder:32b
ollama pull qwen2.5:72b
```

### 6. Verify Installation

```bash
hrisa check --auto-fix
```

### 7. Initialize Configuration

```bash
hrisa init
```

## Troubleshooting

### Python Version Issues

**Problem**: "Python 3.10+ required"

**Solutions**:
- **macOS**: `brew install python@3.11`
- **Linux**: `sudo apt install python3.11` (Ubuntu/Debian)
- **Windows**: Download from https://www.python.org/downloads/

### Ollama Not Found

**Problem**: "Ollama not found"

**Solutions**:
- **macOS**: `brew install ollama`
- **Linux**: `curl https://ollama.ai/install.sh | sh`
- **Windows**: Download from https://ollama.ai/
- Verify with: `ollama --version`

### Ollama Service Not Running

**Problem**: "Ollama service not responding"

**Solutions**:
- **macOS**: `ollama serve` (or `brew services start ollama`)
- **Linux**: `sudo systemctl start ollama` (or `ollama serve`)
- **Windows**: Run `ollama serve` in separate terminal
- Check if port 11434 is available: `lsof -i :11434` (Unix) or `netstat -an | findstr 11434` (Windows)

### Model Pull Failures

**Problem**: "Failed to pull model"

**Solutions**:
1. Check internet connection
2. Verify Ollama is running: `ollama list`
3. Check disk space (models can be 4-40GB)
4. Try smaller model first: `ollama pull qwen2.5-coder:7b`
5. Use direct pull: `ollama pull qwen2.5-coder:7b --verbose`

### PDF Libraries Installation Fails

**Problem**: "Failed to install PDF libraries"

**Solutions**:
```bash
# Activate virtual environment first
source venv/bin/activate  # or .\venv\Scripts\activate (Windows)

# Install manually
pip install pypdf

# If still fails, try upgrading pip
pip install --upgrade pip setuptools wheel
pip install pypdf
```

### Virtual Environment Issues

**Problem**: "Permission denied" or activation fails

**Solutions**:

**Windows PowerShell**:
```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
.\venv\Scripts\Activate.ps1
```

**macOS/Linux**:
```bash
chmod +x venv/bin/activate
source venv/bin/activate
```

### Git Not Found

**Problem**: "Git not found"

**Solutions**:
- **macOS**: `brew install git` or install Xcode Command Line Tools
- **Linux**: `sudo apt install git` (Ubuntu/Debian)
- **Windows**: Download from https://git-scm.com/download/windows
- Verify with: `git --version`

### Docker Issues (Optional)

**Problem**: "Docker not responding"

**Solutions**:
- Install Docker Desktop: https://docker.com
- Start Docker service
- Note: Docker is optional for native setup

### Port Conflicts

**Problem**: "Port 11434 already in use"

**Solutions**:
1. Check what's using the port:
   ```bash
   # macOS/Linux
   lsof -i :11434

   # Windows
   netstat -ano | findstr 11434
   ```

2. Kill the conflicting process or use different port:
   ```bash
   OLLAMA_HOST=http://localhost:11435 ollama serve
   ```

3. Update config to use new port in `.hrisa/config.yaml`

### Import Errors

**Problem**: "ModuleNotFoundError: No module named 'hrisa_code'"

**Solutions**:
1. Ensure virtual environment is activated:
   ```bash
   source venv/bin/activate  # macOS/Linux
   .\venv\Scripts\activate   # Windows
   ```

2. Reinstall in development mode:
   ```bash
   pip install -e ".[dev]"
   ```

3. Verify installation:
   ```bash
   pip list | grep hrisa-code
   ```

## Next Steps

After successful setup:

1. **Run Checks**: `hrisa check`
2. **Initialize Config**: `hrisa init`
3. **Start Chat**: `hrisa chat`
4. **Explore Commands**: `hrisa --help`
5. **Read Documentation**: Check `docs/` directory

## Getting Help

- **Documentation**: See `docs/` directory
- **Issues**: https://github.com/yourusername/hrisa-code/issues
- **Discussions**: https://github.com/yourusername/hrisa-code/discussions
- **CLI Help**: `hrisa --help` or `hrisa <command> --help`

## Platform Requirements Summary

### Minimum Requirements

| Platform | Python | Ollama | Disk Space |
|----------|--------|--------|------------|
| macOS | 3.10+ | Latest | 10GB+ |
| Linux | 3.10+ | Latest | 10GB+ |
| Windows | 3.10+ | Latest | 10GB+ |

### Recommended Requirements

| Platform | Python | RAM | Disk Space | GPU |
|----------|--------|-----|------------|-----|
| macOS | 3.11+ | 16GB | 50GB+ | Optional |
| Linux | 3.11+ | 16GB | 50GB+ | Optional (CUDA) |
| Windows | 3.11+ | 16GB | 50GB+ | Optional (CUDA) |

### Supported Ollama Models

- **Small (4-8GB)**: qwen2.5-coder:7b, codellama:7b, deepseek-coder:6.7b
- **Medium (15-20GB)**: qwen2.5-coder:14b, codellama:13b
- **Large (20-40GB)**: qwen2.5-coder:32b, qwen2.5:72b, codellama:34b

Choose model size based on available RAM and disk space.
