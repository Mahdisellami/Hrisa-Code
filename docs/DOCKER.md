# Docker Guide for Hrisa Code

This guide covers running Hrisa Code with Docker and Docker Compose, providing a fully containerized environment with Ollama.

## Why Docker?

- **Isolated Environment**: No conflicts with system packages
- **Easy Setup**: Everything runs in containers
- **Consistent**: Same environment everywhere
- **Portable**: Works on any platform with Docker
- **Includes Ollama**: Both services orchestrated together

## Prerequisites

- Docker Desktop or Docker Engine installed
- Docker Compose (included with Docker Desktop)
- At least 8GB RAM (for running models)
- Sufficient disk space for models (5-20GB depending on model size)

## Quick Start

### 1. Start Services

```bash
# Using Makefile (recommended)
make docker-up

# Or using docker compose directly
docker compose up -d ollama

# Or using the script
./scripts/docker-start.sh
```

This starts the Ollama service in the background.

### 2. Pull Models

```bash
# Pull default models (codellama and deepseek-coder)
make docker-pull

# Pull specific model
make docker-pull MODEL=mistral

# Or manually
docker compose exec ollama ollama pull codellama
```

### 3. Start Chatting

```bash
# Using Makefile
make docker-chat

# With specific model
make docker-chat MODEL=deepseek-coder

# Or using script
./scripts/docker-chat.sh codellama
```

## Architecture

The Docker setup includes:

```
┌─────────────────────────────────────┐
│   Docker Compose Environment        │
│                                     │
│  ┌──────────────┐  ┌─────────────┐ │
│  │  Hrisa Code  │→→│   Ollama    │ │
│  │  Container   │  │  Container  │ │
│  └──────────────┘  └─────────────┘ │
│         ↓                  ↓        │
│  ┌──────────────┐  ┌─────────────┐ │
│  │  Workspace   │  │   Models    │ │
│  │   Volume     │  │   Volume    │ │
│  └──────────────┘  └─────────────┘ │
└─────────────────────────────────────┘
```

## Services

### Ollama Service

Runs the Ollama server for local LLM inference.

**Ports**: `11434` (API endpoint)
**Volume**: `ollama_data` (persists downloaded models)
**Health Check**: Automatically waits for service to be ready

### Hrisa Code Service

The CLI application that connects to Ollama.

**Volumes**:
- `./workspace:/workspace` - Your code workspace
- `hrisa_config:/home/hrisa/.config/hrisa-code` - Configuration
- `hrisa_history:/home/hrisa/.hrisa` - Conversation history

## Common Commands

### Service Management

```bash
# Start services
make docker-up

# Stop services (keeps volumes)
make docker-down

# Restart services
make docker-down && make docker-up

# View logs
docker compose logs -f ollama
docker compose logs -f hrisa
```

### Model Management

```bash
# List available models
make docker-models
# or
docker compose exec ollama ollama list

# Pull a model
make docker-pull MODEL=codellama
# or
docker compose exec ollama ollama pull codellama

# Remove a model
docker compose exec ollama ollama rm codellama
```

### Using Hrisa Code

```bash
# Interactive chat
make docker-chat

# With specific model
make docker-chat MODEL=deepseek-coder

# Run other commands
docker compose run --rm hrisa hrisa models
docker compose run --rm hrisa hrisa init
docker compose run --rm hrisa hrisa --help
```

### Workspace Management

Your code lives in the `./workspace` directory, which is mounted into the container:

```bash
# Files in workspace/ are accessible to the assistant
echo "print('Hello')" > workspace/test.py

# In the chat, you can ask:
# "Read the file test.py and explain what it does"
```

## Configuration

### Custom Configuration

Create a config file in your workspace:

```bash
# Initialize config
docker compose run --rm hrisa hrisa init

# Edit the config
nano .hrisa/config.yaml
```

### Environment Variables

Edit `docker-compose.yml` to customize:

```yaml
environment:
  - OLLAMA_HOST=http://ollama:11434
  - HRISA_MODEL=codellama  # Default model
```

## GPU Support (NVIDIA)

For GPU acceleration with NVIDIA GPUs:

1. Install [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)

2. Uncomment the GPU section in `docker-compose.yml`:

```yaml
services:
  ollama:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
```

3. Restart services:

```bash
make docker-down
make docker-up
```

## Volumes and Data Persistence

### Persistent Data

Three volumes store persistent data:

- **ollama_data**: Downloaded models (largest, 5-20GB)
- **hrisa_config**: User configuration
- **hrisa_history**: Conversation history

### Backup Volumes

```bash
# Backup models
docker run --rm -v hrisa-code_ollama_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/ollama-models-backup.tar.gz -C /data .

# Backup config
docker run --rm -v hrisa-code_hrisa_config:/data -v $(pwd):/backup \
  alpine tar czf /backup/hrisa-config-backup.tar.gz -C /data .
```

### Clean Up

```bash
# Remove containers but keep volumes
make docker-down

# Remove everything including volumes
make docker-clean
# or
docker compose down -v
```

## Troubleshooting

### Service Won't Start

```bash
# Check Docker status
docker info

# Check logs
docker compose logs ollama
docker compose logs hrisa

# Restart services
make docker-down
make docker-up
```

### Ollama Connection Issues

```bash
# Test Ollama directly
curl http://localhost:11434/api/tags

# From within container
docker compose exec ollama curl http://localhost:11434/api/tags

# Check if service is running
docker compose ps
```

### Out of Memory

Models require significant RAM:

- 7B models: ~8GB RAM
- 13B models: ~16GB RAM
- 33B models: ~32GB RAM

**Solutions**:
- Use smaller models (e.g., `codellama:7b`)
- Increase Docker memory limit in Docker Desktop
- Use quantized models (e.g., `codellama:7b-q4`)

### Permission Issues

```bash
# Fix workspace permissions
chmod -R 755 workspace/

# Rebuild with correct user
docker compose build --no-cache
```

### Models Taking Too Long to Download

Large models can take time:

```bash
# Monitor download progress
docker compose exec ollama ollama pull codellama

# Download in advance
docker compose exec ollama ollama pull deepseek-coder:6.7b
```

## Advanced Usage

### Custom Dockerfile

Modify `Dockerfile` to:
- Add additional tools
- Include project dependencies
- Customize the environment

### Multiple Projects

Use different workspace directories:

```bash
# Project 1
docker compose run --rm -v $(pwd)/project1:/workspace hrisa hrisa chat

# Project 2
docker compose run --rm -v $(pwd)/project2:/workspace hrisa hrisa chat
```

### CI/CD Integration

```yaml
# .github/workflows/test.yml
- name: Start services
  run: docker compose up -d ollama

- name: Pull model
  run: docker compose exec ollama ollama pull codellama

- name: Run tests
  run: docker compose run --rm hrisa pytest
```

## Performance Tips

1. **Use GPU**: Dramatically faster with NVIDIA GPUs
2. **Choose Right Model Size**: Smaller = faster, larger = smarter
3. **Keep Models Cached**: Models persist in volume
4. **Limit Context**: Shorter conversations = faster responses
5. **Use Quantized Models**: `model:7b-q4` is faster than `model:7b`

## Comparison with Local Development

| Aspect | Docker | Local (venv/uv) |
|--------|---------|-----------------|
| Setup Time | Faster | Slower |
| Isolation | Complete | Partial |
| Ollama Install | Included | Manual |
| Disk Space | More | Less |
| Performance | Good | Slightly better |
| Portability | Excellent | Platform-dependent |

## Resources

- [Docker Documentation](https://docs.docker.com/)
- [Ollama Docker Image](https://hub.docker.com/r/ollama/ollama)
- [Docker Compose Spec](https://docs.docker.com/compose/compose-file/)

## Next Steps

1. ✅ Start services: `make docker-up`
2. ✅ Pull models: `make docker-pull`
3. ✅ Start chatting: `make docker-chat`
4. Try different models
5. Mount your actual projects to workspace
6. Customize configuration

Happy coding with Hrisa Code! 🚀
