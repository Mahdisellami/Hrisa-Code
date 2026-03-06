# Docker Quick Start

One-page guide to get Hrisa Code Web UI running with Docker in 5 minutes.

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM, 10GB disk space

## Installation

### 1. Start Services (One Command)

```bash
./deploy.sh start
```

This will:
- Build the web UI image
- Start Ollama service
- Start web UI service
- Wait for health checks

### 2. Pull Models

```bash
./deploy.sh pull-models
```

Or manually:

```bash
docker exec hrisa-ollama ollama pull qwen2.5-coder:7b
docker exec hrisa-ollama ollama pull llama3.2:latest
```

### 3. Access Web UI

Open browser: **http://localhost:8000**

## Essential Commands

```bash
# Deployment
./deploy.sh start         # Start all services
./deploy.sh stop          # Stop all services
./deploy.sh restart       # Restart services
./deploy.sh status        # Check status

# Monitoring
./deploy.sh logs          # View logs (Ctrl+C to exit)
docker-compose ps         # Service status

# Models
docker exec hrisa-ollama ollama list   # List models
docker exec hrisa-ollama ollama pull MODEL  # Pull model

# Maintenance
./deploy.sh update        # Update to latest version
./deploy.sh backup        # Backup data
./deploy.sh clean         # Remove all data (careful!)
```

## Service URLs

- **Web UI**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Ollama API**: http://localhost:11434

## Troubleshooting

### Port Already in Use

```bash
# Change port in docker-compose.yml
services:
  web:
    ports:
      - "3000:8000"  # Use port 3000 instead
```

### Services Won't Start

```bash
# Check logs
./deploy.sh logs

# Check Docker
docker info

# Restart from scratch
./deploy.sh stop
./deploy.sh start
```

### Models Not Found

```bash
# Pull models explicitly
./deploy.sh pull-models

# Or pull specific model
docker exec hrisa-ollama ollama pull your-model
```

### Web UI Not Loading

```bash
# Check web service health
docker-compose ps web

# Restart web service
docker-compose restart web

# Check logs for errors
docker-compose logs web
```

## Configuration

### Environment Variables

Edit `docker-compose.yml`:

```yaml
services:
  web:
    environment:
      - MAX_CONCURRENT_AGENTS=5
      - STUCK_THRESHOLD_SECONDS=120
```

### Custom Models

Edit `docker-compose.yml`:

```yaml
services:
  ollama-pull:
    command: -c "ollama pull your-model-name"
```

### Resource Limits

Add to `docker-compose.yml`:

```yaml
services:
  web:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

## Data Locations

```bash
# Volumes (persistent data)
ollama_data       # Downloaded models
hrisa_config      # Configuration
hrisa_history     # Conversation history
./workspace       # Agent working directory

# View volume data
docker volume ls
docker volume inspect hrisa-code_ollama_data
```

## Manual Docker Commands

If you prefer not to use `deploy.sh`:

```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# Logs
docker-compose logs -f web

# Status
docker-compose ps

# Rebuild
docker-compose build web
docker-compose up -d
```

## Development Mode

```bash
# Edit docker-compose.yml to add:
services:
  web:
    volumes:
      - ./src:/app/src
    command: hrisa web --host 0.0.0.0 --reload

# Start
docker-compose up web
```

## First-Time Setup Checklist

- [ ] Install Docker and Docker Compose
- [ ] Clone repository
- [ ] Run `./deploy.sh start`
- [ ] Run `./deploy.sh pull-models`
- [ ] Access http://localhost:8000
- [ ] Create test agent
- [ ] Verify agent executes successfully

## Common Use Cases

### Quick Test

```bash
./deploy.sh start
# Wait 30 seconds for health checks
open http://localhost:8000
# Create agent with task: "List Python files"
```

### Daily Usage

```bash
# Morning
./deploy.sh start

# Work with agents via web UI

# Evening
./deploy.sh stop
```

### Model Updates

```bash
docker exec hrisa-ollama ollama pull qwen2.5-coder:latest
./deploy.sh restart
```

### Backup Before Update

```bash
./deploy.sh backup
./deploy.sh update
```

## Getting Help

- Full documentation: [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)
- Web UI guide: [docs/WEB_UI.md](docs/WEB_UI.md)
- Issues: https://github.com/yourusername/hrisa-code/issues

## Architecture

```
┌─────────────────────┐
│   Browser :8000     │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│   hrisa-web         │
│  (FastAPI + WS)     │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│   hrisa-ollama      │
│  (LLM Backend)      │
└─────────────────────┘
```

## Performance Tips

1. **Use smaller models** for development (7B vs 32B)
2. **Limit concurrent agents** (3-5 recommended)
3. **Enable GPU** if available (NVIDIA only)
4. **Monitor memory** usage with `docker stats`
5. **Close unused agents** in web UI

## Security Notes

**Default setup is for local development only!**

For production:
- Add authentication
- Use HTTPS with reverse proxy
- Change default ports
- Limit resource usage
- Regular backups

See [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) for production setup.

---

**That's it!** You're ready to use Hrisa Code Web UI with Docker.
