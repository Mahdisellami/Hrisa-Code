# Local Development with Docker

## Quick Start

### 1. Start Services
```bash
docker-compose up -d
```

This starts:
- **Ollama** (port 11434) - Local LLM service
- **Web UI** (port 8000) - Agent management dashboard

### 2. Access the Application
Open your browser: **http://localhost:8000**

You should see the Agents Dashboard (no login required).

### 3. Stop Services
```bash
docker-compose down
```

---

## What's Running

### Ollama Service
- **URL**: http://localhost:11434
- **Purpose**: Runs local LLMs
- **Models**: You need to pull models first (see below)

### Web UI
- **URL**: http://localhost:8000
- **Purpose**: Interactive agent management dashboard
- **Features**:
  - Create and manage agents
  - Monitor agent execution
  - View logs and artifacts
  - Team collaboration

---

## Initial Setup

### Pull Required Models
```bash
# Start Ollama
docker-compose up -d ollama

# Pull models (one-time setup)
docker exec -it hrisa-ollama ollama pull qwen2.5-coder:7b
docker exec -it hrisa-ollama ollama pull llama3.2:latest

# Verify models
docker exec -it hrisa-ollama ollama list
```

Or use the helper service:
```bash
docker-compose --profile setup up ollama-pull
```

---

## Development Workflow

### Watch Logs
```bash
# All services
docker-compose logs -f

# Just web service
docker-compose logs -f web

# Just ollama
docker-compose logs -f ollama
```

### Restart Service
```bash
# Restart web after code changes
docker-compose restart web

# Restart everything
docker-compose restart
```

### Run CLI Commands
```bash
# Interactive chat
docker-compose run --rm hrisa hrisa chat

# List models
docker-compose run --rm hrisa hrisa models

# Check system
docker-compose run --rm hrisa hrisa check
```

---

## Troubleshooting

### Port Already in Use
```bash
# Check what's using port 8000
lsof -i :8000

# Or use different port
docker-compose down
# Edit docker-compose.yml: change "8000:8000" to "8001:8000"
docker-compose up -d
```

### Ollama Not Responding
```bash
# Restart Ollama
docker-compose restart ollama

# Check status
docker-compose ps ollama

# View logs
docker-compose logs ollama
```

### Web UI Not Loading
```bash
# Check if service is running
docker-compose ps web

# Check logs for errors
docker-compose logs web

# Restart service
docker-compose restart web
```

### Models Not Found
```bash
# Pull models manually
docker exec -it hrisa-ollama ollama pull qwen2.5-coder:7b

# Verify they're installed
docker exec -it hrisa-ollama ollama list
```

---

## File Structure

```
.
├── docker-compose.yml       # Service definitions
├── Dockerfile              # CLI container image
├── Dockerfile.web          # Web UI container image
├── src/                    # Source code
│   └── hrisa_code/
│       ├── cli.py          # CLI entry point
│       └── web/
│           ├── server.py   # FastAPI backend
│           └── static/     # Frontend files
│               ├── index.html
│               ├── app.js
│               └── styles.css
├── workspace/              # Your work files (mounted in containers)
└── volumes/                # Docker volumes (created automatically)
    ├── ollama_data/        # Ollama models
    ├── hrisa_config/       # Configuration
    └── hrisa_history/      # Conversation history
```

---

## Configuration

### Environment Variables
Edit `docker-compose.yml` to change:

```yaml
environment:
  - OLLAMA_HOST=http://ollama:11434
  - REQUIRED_MODELS=qwen2.5-coder:7b,llama3.2:latest
  - AUTO_PULL_MODELS=false
  - SKIP_VERIFICATION=false
```

### Custom Models
```yaml
environment:
  - REQUIRED_MODELS=codellama:latest,mistral:latest
```

---

## Clean Up

### Remove Everything
```bash
# Stop and remove containers
docker-compose down

# Remove volumes (deletes models and history)
docker-compose down -v

# Remove images
docker rmi $(docker images | grep hrisa | awk '{print $3}')
```

### Just Reset Data
```bash
# Stop services
docker-compose down

# Remove specific volumes
docker volume rm hrisa-code_hrisa_history
docker volume rm hrisa-code_hrisa_config

# Keep ollama_data to preserve downloaded models
```

---

## Production Deployment

Production deployment (Render/Vercel) will be handled in a future phase.

For now, focus on local development with Docker.

---

## Next Steps

1. Start services: `docker-compose up -d`
2. Pull models (see above)
3. Open http://localhost:8000
4. Create your first agent!

Happy coding! 🚀
