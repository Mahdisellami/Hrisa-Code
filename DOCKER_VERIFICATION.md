# Docker Verification and Preinstallation Guide

This guide covers the comprehensive verification and preinstallation features added to Hrisa Code's Docker deployment.

## Overview

The Docker deployment now includes automatic verification and preinstallation of all dependencies:

- **PDF Libraries**: Automatically installed in all Docker images
- **Ollama Verification**: Health checks ensure Ollama is running before starting services
- **Model Verification**: Automatic checking and optional pulling of required models
- **Pre-flight Checks**: Comprehensive dependency verification on container startup
- **Cross-platform Support**: Works on macOS, Linux, and Windows

## Architecture

### Components

1. **docker-entrypoint.sh**: Smart entrypoint script that runs verification before starting services
2. **Dockerfiles**: Enhanced with PDF libraries and verification tools
3. **docker-compose.yml**: Configured with environment variables for verification
4. **deploy.sh**: Helper script with verification commands

### Verification Flow

```
Container Start
    ↓
Entrypoint Script
    ↓
1. Wait for Ollama Service (with timeout)
    ↓
2. Check Required Models
    ↓
3. Auto-pull Missing Models (if enabled)
    ↓
4. Run Pre-flight Checks (hrisa check)
    ↓
5. Start Main Application
```

## Environment Variables

Control verification behavior with these environment variables in `docker-compose.yml`:

### REQUIRED_MODELS
Comma-separated list of required Ollama models.

```yaml
environment:
  - REQUIRED_MODELS=qwen2.5-coder:7b,llama3.2:latest
```

**Default**: `qwen2.5-coder:7b,llama3.2:latest`

### AUTO_PULL_MODELS
Automatically pull missing models on startup.

```yaml
environment:
  - AUTO_PULL_MODELS=true
```

**Default**: `false` (manual pull required)
**Warning**: Setting to `true` may cause long startup times for large models.

### SKIP_VERIFICATION
Skip all verification checks on startup.

```yaml
environment:
  - SKIP_VERIFICATION=true
```

**Default**: `false` (verification enabled)
**Use Case**: For production when you're confident all dependencies are installed.

## Usage

### 1. Basic Deployment (with verification)

```bash
./deploy.sh start
```

The containers will:
- Wait for Ollama to be healthy
- Check for required models
- Run pre-flight checks
- Start services only if verification passes

### 2. Check System Requirements

```bash
./deploy.sh check
```

This command checks:
- Docker installation
- Docker Compose installation
- Docker daemon status
- Running services
- Available models
- Full verification suite

### 3. Run Verification Only

```bash
./deploy.sh verify
```

Runs the verification service without starting main services.

### 4. Pull Models

```bash
./deploy.sh pull-models
```

Pulls recommended models:
- qwen2.5-coder:7b
- llama3.2:latest

### 5. Auto-pull on Startup

Edit `docker-compose.yml`:

```yaml
services:
  web:
    environment:
      - AUTO_PULL_MODELS=true  # Enable auto-pull
```

Then start:

```bash
./deploy.sh start
```

**Note**: First startup may take 10-30 minutes depending on model sizes and connection speed.

## What Gets Verified

### System Dependencies
- ✓ Python 3.10+
- ✓ Git
- ✓ Curl
- ✓ Docker (when checking from host)

### Ollama
- ✓ Ollama service accessibility
- ✓ Required models availability
- ✓ Model pulling capability

### PDF Libraries
- ✓ pypdf installed and importable

### Application
- ✓ Hrisa Code CLI commands work
- ✓ Configuration is valid
- ✓ File system permissions

## Verification Output

### Successful Verification

```
========================================
  Hrisa Code - Docker Startup
========================================

[1/3] Waiting for Ollama service...
✓ Ollama service is ready

[2/3] Checking for required models...
✓ All required models are available

[3/3] Running pre-flight checks...
✓ Verification passed

========================================
  Hrisa Code Ready!
========================================
```

### Missing Models (with AUTO_PULL_MODELS=false)

```
[2/3] Checking for required models...
⚠ Missing models: llama3.2:latest
Models can be pulled using: docker exec <container> ollama pull <model>
```

**Fix**:
```bash
docker exec hrisa-ollama ollama pull llama3.2:latest
```

Or enable auto-pull:
```yaml
environment:
  - AUTO_PULL_MODELS=true
```

### Verification Failed

```
[3/3] Running pre-flight checks...
⚠ Some verification checks failed (non-critical)
```

Check logs:
```bash
docker-compose logs web
```

## Advanced Configuration

### Custom Models

Specify your own models:

```yaml
services:
  web:
    environment:
      - REQUIRED_MODELS=codellama:34b,deepseek-coder:6.7b,mistral:latest
```

### Skip Verification in Production

For production deployments where you've pre-verified everything:

```yaml
services:
  web:
    environment:
      - SKIP_VERIFICATION=true
```

### Faster Startup with Pre-pulled Models

1. Pull models once:
```bash
./deploy.sh pull-models
```

2. Deploy without auto-pull:
```yaml
environment:
  - AUTO_PULL_MODELS=false  # Models already available
```

## Troubleshooting

### Container Starts but Exits Immediately

**Cause**: Verification failed or timeout waiting for Ollama.

**Solution**:
```bash
# Check logs
docker-compose logs web

# Verify Ollama is running
docker-compose ps ollama

# Check Ollama health
docker exec hrisa-ollama ollama list
```

### Timeout Waiting for Ollama

**Cause**: Ollama service taking too long to start.

**Solution**:
Edit `docker-entrypoint.sh` and increase timeout:
```bash
MAX_WAIT=120  # Increase from 60 to 120 seconds
```

### Models Won't Pull Automatically

**Cause**: Network issues or model not found.

**Solution**:
```bash
# Pull manually
docker exec hrisa-ollama ollama pull qwen2.5-coder:7b

# Check available models
docker exec hrisa-ollama ollama list

# Test Ollama connection
curl http://localhost:11434/api/tags
```

### PDF Libraries Not Working

**Cause**: Build cache from old image.

**Solution**:
```bash
# Rebuild without cache
./deploy.sh stop
docker-compose build --no-cache web
./deploy.sh start
```

### Verification Checks Fail

**Cause**: Dependencies missing or misconfigured.

**Solution**:
```bash
# Run verification service
./deploy.sh verify

# Check specific component
docker-compose --profile verify run --rm verify

# Skip verification temporarily
docker-compose up -d
```

## Pre-flight Checks Reference

The `hrisa check` command runs these checks:

| Check | Type | Description |
|-------|------|-------------|
| Python Version | Critical | Python 3.10+ required |
| Ollama Installation | Critical | Ollama binary accessible |
| Ollama Service | Critical | Ollama responding to commands |
| Required Models | Warning | Specified models available |
| Git | Optional | Git available for operations |
| PDF Libraries | Optional | pypdf library importable |

**Exit Codes**:
- `0`: All critical checks passed
- `1`: One or more critical checks failed

## Best Practices

### Development

1. Enable verbose verification:
```bash
docker-compose up  # No -d flag to see logs
```

2. Use smaller models for faster iteration:
```yaml
environment:
  - REQUIRED_MODELS=qwen2.5-coder:7b  # Smaller model
```

### Production

1. Pre-pull all models:
```bash
./deploy.sh pull-models
```

2. Disable auto-pull:
```yaml
environment:
  - AUTO_PULL_MODELS=false
```

3. Enable verification:
```yaml
environment:
  - SKIP_VERIFICATION=false  # Catch config issues
```

4. Set resource limits:
```yaml
services:
  web:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

### CI/CD

1. Check before deploy:
```bash
./deploy.sh check
```

2. Verify after deploy:
```bash
./deploy.sh verify
```

3. Pull models in separate step:
```bash
./deploy.sh pull-models
```

## Performance Considerations

### Startup Time

| Configuration | Expected Startup Time |
|---------------|----------------------|
| Skip verification | 5-10 seconds |
| Verification only | 10-15 seconds |
| Verification + small model pull | 1-3 minutes |
| Verification + large model pull | 10-30 minutes |

### Model Sizes

Common model sizes (approximate):

| Model | Size | Pull Time (10 Mbps) |
|-------|------|---------------------|
| qwen2.5-coder:7b | 4.7 GB | 6-8 minutes |
| llama3.2:latest | 2.0 GB | 3-4 minutes |
| codellama:34b | 19 GB | 25-30 minutes |
| qwen2.5:72b | 41 GB | 55-60 minutes |

**Recommendation**: Use smaller models for development, larger models for production.

## Files Changed

### New Files
- `docker-entrypoint.sh` - Verification entrypoint script
- `DOCKER_VERIFICATION.md` - This documentation

### Modified Files
- `Dockerfile` - Added PDF libraries and entrypoint
- `Dockerfile.web` - Added PDF libraries and entrypoint
- `docker-compose.yml` - Added environment variables and verify service
- `deploy.sh` - Added check and verify commands

## Integration with Hrisa Code

The Docker verification integrates with Hrisa Code's built-in verification:

### Python API

```python
from hrisa_code.core.validation import PreflightChecker, SetupManager

# Run checks programmatically
checker = PreflightChecker()
passed, results = checker.run_all_checks(
    required_models=["qwen2.5-coder:7b"]
)

# Run full setup
manager = SetupManager(auto_install=True)
success, steps = manager.run_full_setup()
```

### CLI Commands

```bash
# Run checks from host
hrisa check

# Run checks in container
docker exec hrisa-web hrisa check

# Run setup wizard (interactive)
docker exec -it hrisa-web hrisa setup

# Run setup with auto-install
docker exec hrisa-web hrisa setup --auto-install
```

## Summary

The Docker verification system ensures:

✅ All dependencies are installed and working
✅ Ollama service is accessible before starting
✅ Required models are available or pulled automatically
✅ PDF libraries are installed for document support
✅ Cross-platform compatibility (macOS, Linux, Windows)
✅ Fast verification with sensible timeouts
✅ Flexible configuration via environment variables
✅ Comprehensive error messages and fixes

**Result**: Reliable, reproducible deployments with minimal manual configuration.
