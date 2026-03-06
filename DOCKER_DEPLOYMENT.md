# Docker Deployment Guide

Complete guide for deploying Hrisa Code Web UI with Docker and Docker Compose.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Services Overview](#services-overview)
- [Deployment Options](#deployment-options)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Production Deployment](#production-deployment)

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 4GB+ RAM available
- 10GB+ disk space (for models)

## Quick Start

### 1. Clone and Navigate

```bash
git clone https://github.com/yourusername/hrisa-code.git
cd hrisa-code
```

### 2. Start All Services

```bash
# Start Ollama and Web UI
docker-compose up -d

# Wait for services to be healthy (30-60 seconds)
docker-compose ps
```

### 3. Pull Required Models

```bash
# Pull models (first time setup)
docker-compose --profile setup up ollama-pull

# Or manually pull specific models
docker exec hrisa-ollama ollama pull qwen2.5-coder:7b
docker exec hrisa-ollama ollama pull llama3.2:latest
```

### 4. Access Web UI

Open your browser to: **http://localhost:8000**

## Services Overview

### Ollama Service
- **Container**: `hrisa-ollama`
- **Port**: 11434
- **Purpose**: Local LLM backend
- **Volume**: `ollama_data` (persists downloaded models)

### Web UI Service
- **Container**: `hrisa-web`
- **Port**: 8000
- **Purpose**: Multi-agent management interface
- **Volumes**:
  - `./workspace:/workspace` - Agent working directory
  - `hrisa_config` - Configuration persistence
  - `hrisa_history` - Conversation history

### CLI Service (Optional)
- **Container**: `hrisa-code`
- **Purpose**: Interactive CLI sessions
- **Profile**: `cli` (not started by default)

## Deployment Options

### Option 1: Web UI Only (Default)

Start just the web interface and Ollama:

```bash
docker-compose up -d
```

Access at: http://localhost:8000

### Option 2: CLI Only

Start Ollama and interactive CLI:

```bash
docker-compose --profile cli up
```

Attaches to interactive terminal.

### Option 3: Everything

Start all services including CLI:

```bash
docker-compose --profile cli up -d
docker attach hrisa-code
```

### Option 4: Development Mode

With live reload for development:

```bash
# Edit docker-compose.yml to mount src/ as volume
docker-compose up web

# In web service, add:
# volumes:
#   - ./src:/app/src
# command: hrisa web --host 0.0.0.0 --reload
```

## Configuration

### Environment Variables

Edit `docker-compose.yml` to customize:

```yaml
services:
  web:
    environment:
      - OLLAMA_HOST=http://ollama:11434
      - WEB_HOST=0.0.0.0
      - WEB_PORT=8000
      - MAX_CONCURRENT_AGENTS=5
      - STUCK_THRESHOLD_SECONDS=120
```

### Custom Models

To use different models, update the `ollama-pull` service:

```yaml
services:
  ollama-pull:
    command: -c "ollama pull your-model-here"
```

Or pull manually:

```bash
docker exec hrisa-ollama ollama pull mistral:latest
docker exec hrisa-ollama ollama pull codellama:34b
```

### Port Configuration

Change exposed ports in `docker-compose.yml`:

```yaml
services:
  web:
    ports:
      - "3000:8000"  # Access on port 3000 instead
```

### GPU Support (NVIDIA)

Uncomment GPU configuration in `docker-compose.yml`:

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

Requires:
- NVIDIA GPU
- NVIDIA Container Toolkit installed
- Docker with GPU support

## Common Commands

### Service Management

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart services
docker-compose restart

# View logs
docker-compose logs -f web
docker-compose logs -f ollama

# Check service status
docker-compose ps
```

### Model Management

```bash
# List available models
docker exec hrisa-ollama ollama list

# Pull a new model
docker exec hrisa-ollama ollama pull model-name

# Remove a model
docker exec hrisa-ollama ollama rm model-name

# Check Ollama service
docker exec hrisa-ollama ollama ps
```

### Agent Management

```bash
# View web UI logs (agent activity)
docker-compose logs -f web

# Access web container shell
docker exec -it hrisa-web bash

# Check agent working directory
docker exec hrisa-web ls -la /workspace
```

### Data Management

```bash
# Backup volumes
docker run --rm -v hrisa_code_ollama_data:/data -v $(pwd):/backup \
    ubuntu tar czf /backup/ollama_backup.tar.gz /data

# Restore volumes
docker run --rm -v hrisa_code_ollama_data:/data -v $(pwd):/backup \
    ubuntu tar xzf /backup/ollama_backup.tar.gz -C /

# Clean up volumes (WARNING: deletes all data)
docker-compose down -v
```

## Troubleshooting

### Service Won't Start

**Check logs:**
```bash
docker-compose logs web
docker-compose logs ollama
```

**Common issues:**
- Port 8000 already in use: Change port in docker-compose.yml
- Port 11434 already in use: Stop local Ollama or change port
- Out of memory: Increase Docker memory limit (4GB minimum)

### Ollama Not Responding

```bash
# Check Ollama health
docker exec hrisa-ollama curl -f http://localhost:11434/api/tags

# Restart Ollama
docker-compose restart ollama

# Check Ollama logs
docker-compose logs ollama
```

### Web UI Not Accessible

```bash
# Check if web service is running
docker-compose ps web

# Check web service health
curl http://localhost:8000/api/stats

# Check web service logs
docker-compose logs web

# Restart web service
docker-compose restart web
```

### Models Not Found

```bash
# List available models
docker exec hrisa-ollama ollama list

# Pull required models
docker exec hrisa-ollama ollama pull qwen2.5-coder:7b

# Or run setup profile
docker-compose --profile setup up ollama-pull
```

### Agent Failing to Execute

**Check workspace permissions:**
```bash
docker exec hrisa-web ls -la /workspace
```

**Check Ollama connectivity from web service:**
```bash
docker exec hrisa-web curl http://ollama:11434/api/tags
```

**Check agent logs in web UI:**
- Open http://localhost:8000
- Click on agent
- View message history and errors

### Container Build Fails

```bash
# Clean build
docker-compose build --no-cache web

# Check Dockerfile syntax
docker build -f Dockerfile.web -t test .

# Remove old images
docker image prune -a
```

## Production Deployment

### Security Considerations

1. **Change default ports** in production
2. **Add authentication** (not included by default)
3. **Use HTTPS** with reverse proxy (nginx, Caddy)
4. **Limit resource usage** with Docker resource constraints
5. **Use secrets** for sensitive configuration

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
        reservations:
          cpus: '1'
          memory: 1G

  ollama:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          cpus: '2'
          memory: 4G
```

### Reverse Proxy (Nginx)

Example nginx configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### SSL with Let's Encrypt

```bash
# Using Certbot
sudo certbot --nginx -d your-domain.com
```

### Monitoring

Add monitoring with Prometheus/Grafana:

```yaml
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    depends_on:
      - prometheus
```

### Logging

Configure log rotation:

```yaml
services:
  web:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### Health Checks

Services include health checks:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/api/stats"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

Check health status:

```bash
docker-compose ps
# Look for "healthy" status
```

## Performance Tuning

### Model Selection

Smaller models = faster responses, less memory:
- **Development**: `qwen2.5-coder:7b` (4GB RAM)
- **Production**: `qwen2.5-coder:32b` (20GB RAM)
- **Lightweight**: `llama3.2:1b` (1GB RAM)

### Concurrent Agents

Adjust in environment variables:

```yaml
services:
  web:
    environment:
      - MAX_CONCURRENT_AGENTS=3  # Lower for less memory usage
```

### Volume Performance

Use named volumes for better performance:

```yaml
volumes:
  workspace:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /path/to/fast/storage
```

## Backup and Restore

### Backup Everything

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup volumes
docker run --rm -v hrisa_code_ollama_data:/data -v $(pwd)/$BACKUP_DIR:/backup \
    ubuntu tar czf /backup/ollama.tar.gz /data

docker run --rm -v hrisa_code_hrisa_config:/data -v $(pwd)/$BACKUP_DIR:/backup \
    ubuntu tar czf /backup/config.tar.gz /data

docker run --rm -v hrisa_code_hrisa_history:/data -v $(pwd)/$BACKUP_DIR:/backup \
    ubuntu tar czf /backup/history.tar.gz /data

# Backup workspace
tar czf "$BACKUP_DIR/workspace.tar.gz" workspace/

echo "Backup completed: $BACKUP_DIR"
```

### Restore from Backup

```bash
#!/bin/bash
# restore.sh

BACKUP_DIR="$1"

if [ -z "$BACKUP_DIR" ]; then
    echo "Usage: ./restore.sh <backup_directory>"
    exit 1
fi

# Stop services
docker-compose down

# Restore volumes
docker run --rm -v hrisa_code_ollama_data:/data -v $(pwd)/$BACKUP_DIR:/backup \
    ubuntu tar xzf /backup/ollama.tar.gz -C /

docker run --rm -v hrisa_code_hrisa_config:/data -v $(pwd)/$BACKUP_DIR:/backup \
    ubuntu tar xzf /backup/config.tar.gz -C /

docker run --rm -v hrisa_code_hrisa_history:/data -v $(pwd)/$BACKUP_DIR:/backup \
    ubuntu tar xzf /backup/history.tar.gz -C /

# Restore workspace
tar xzf "$BACKUP_DIR/workspace.tar.gz"

# Start services
docker-compose up -d

echo "Restore completed"
```

## Network Configuration

Services communicate via `hrisa-network`:

```yaml
networks:
  hrisa-network:
    driver: bridge
```

To use custom network:

```yaml
networks:
  hrisa-network:
    external: true
    name: your-custom-network
```

## Multi-Host Deployment

For deploying across multiple hosts, use Docker Swarm:

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml hrisa

# Scale web service
docker service scale hrisa_web=3

# Check services
docker stack services hrisa
```

## Updating

### Update Images

```bash
# Pull latest images
docker-compose pull

# Rebuild custom images
docker-compose build --no-cache

# Restart services
docker-compose up -d
```

### Update Models

```bash
# Update to latest model version
docker exec hrisa-ollama ollama pull qwen2.5-coder:latest
```

### Rolling Update

```bash
# Update web service without downtime
docker-compose up -d --no-deps --build web
```

## FAQ

**Q: How much disk space do I need?**
A: Minimum 10GB for models, 20GB+ recommended.

**Q: Can I use remote Ollama?**
A: Yes, set `OLLAMA_HOST` to remote URL.

**Q: How do I add authentication?**
A: Use reverse proxy with basic auth or implement custom auth.

**Q: Can I run on ARM (M1/M2 Mac)?**
A: Yes, Docker will use ARM-compatible images automatically.

**Q: How do I migrate from local to Docker?**
A: Copy `~/.config/hrisa-code/` to `hrisa_config` volume.

**Q: Can I use external database?**
A: Currently uses in-memory state; persistence planned for future.

## Support

- **Issues**: https://github.com/yourusername/hrisa-code/issues
- **Documentation**: See `docs/` directory
- **Docker Docs**: https://docs.docker.com/

---

**Last Updated**: 2026-03-03
