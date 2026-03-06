# Production Deployment Guide

This guide covers deploying Hrisa Code to production environments.

## Table of Contents

- [Pre-deployment Checklist](#pre-deployment-checklist)
- [Security Considerations](#security-considerations)
- [Environment Variables](#environment-variables)
- [Deployment Options](#deployment-options)
- [Monitoring & Logging](#monitoring--logging)
- [Backup & Recovery](#backup--recovery)

## Pre-deployment Checklist

### Required

- [ ] Set `DEBUG=false` in environment
- [ ] Configure strong `SECRET_KEY`
- [ ] Set up HTTPS/TLS certificates
- [ ] Configure `ALLOWED_ORIGINS` for CORS
- [ ] Review and set `MAX_CONCURRENT_AGENTS`
- [ ] Configure Ollama host URL
- [ ] Set up logging to file or service
- [ ] Test webhook endpoints with production URLs
- [ ] Configure SMTP settings for email notifications

### Recommended

- [ ] Set up monitoring (Sentry, DataDog, etc.)
- [ ] Configure rate limiting on API endpoints
- [ ] Set up database for persistent storage
- [ ] Configure Redis for caching
- [ ] Set up automated backups
- [ ] Configure reverse proxy (nginx, Caddy)
- [ ] Set up log rotation
- [ ] Configure health check endpoints

## Security Considerations

### 1. HTTPS Only

**Never** run Hrisa Code over plain HTTP in production.

**nginx configuration example:**

```nginx
server {
    listen 443 ssl http2;
    server_name hrisa.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 2. Webhook Security

- **Always use HTTPS** for webhook URLs
- **Enable HMAC signatures** with strong secrets
- **Validate webhook payloads** on receiving end
- **Implement rate limiting** to prevent abuse
- **Rotate secrets** periodically

### 3. API Security

- **CORS**: Configure allowed origins strictly
- **Rate Limiting**: Implement per-IP limits
- **Authentication**: Add API keys or OAuth (future)
- **Input Validation**: Enforce strict schemas
- **SQL Injection**: Use parameterized queries

### 4. Secret Management

**Never** commit secrets to git:

```bash
# Use environment variables
export SECRET_KEY="$(openssl rand -hex 32)"
export WEBHOOK_SECRET="$(openssl rand -hex 32)"

# Or use secret management services
# AWS Secrets Manager, HashiCorp Vault, etc.
```

## Environment Variables

### Required Variables

```bash
# Server
HOST=0.0.0.0
PORT=8000

# Ollama
OLLAMA_HOST=http://ollama-server:11434

# Security
SECRET_KEY=your-secret-key-here
ALLOWED_ORIGINS=https://hrisa-ui.yourdomain.com

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/hrisa/app.log
```

### Optional Variables

```bash
# Agent Configuration
MAX_CONCURRENT_AGENTS=10
STUCK_THRESHOLD_SECONDS=180

# Webhooks
WEBHOOK_TIMEOUT_SECONDS=10
MAX_WEBHOOK_RETRIES=3

# Email
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your-sendgrid-api-key

# Monitoring
SENTRY_DSN=https://...@sentry.io/...
ENABLE_METRICS=true

# Database (optional)
DATABASE_URL=postgresql://user:pass@localhost/hrisa
```

## Deployment Options

### Option 1: Vercel (Frontend) + Render (Backend)

**Architecture:**
- Frontend (static files) → Vercel
- Backend (FastAPI) → Render

**See**: [VERCEL_RENDER.md](./VERCEL_RENDER.md) for detailed guide

### Option 2: Docker Compose

**Recommended for self-hosted deployments**

```yaml
version: '3.8'

services:
  ollama:
    image: ollama/ollama:latest
    volumes:
      - ollama_data:/root/.ollama
    ports:
      - "11434:11434"

  hrisa:
    build: .
    environment:
      - OLLAMA_HOST=http://ollama:11434
      - HOST=0.0.0.0
      - PORT=8000
      - SECRET_KEY=${SECRET_KEY}
    ports:
      - "8000:8000"
    depends_on:
      - ollama
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    ports:
      - "443:443"
      - "80:80"
    depends_on:
      - hrisa
    restart: unless-stopped

volumes:
  ollama_data:
```

### Option 3: Kubernetes

**For large-scale deployments**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hrisa-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: hrisa
  template:
    metadata:
      labels:
        app: hrisa
    spec:
      containers:
      - name: hrisa
        image: your-registry/hrisa:latest
        env:
        - name: OLLAMA_HOST
          value: "http://ollama-service:11434"
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: hrisa-secrets
              key: secret-key
        ports:
        - containerPort: 8000
        resources:
          limits:
            memory: "2Gi"
            cpu: "1000m"
          requests:
            memory: "1Gi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: hrisa-service
spec:
  selector:
    app: hrisa
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

### Option 4: AWS ECS

**For AWS-native deployments**

- Use ECS Fargate for serverless containers
- RDS for database (PostgreSQL)
- ElastiCache for Redis
- S3 for artifact storage
- CloudWatch for logging
- Application Load Balancer for HTTPS

## Monitoring & Logging

### Sentry Integration

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

if os.getenv("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        integrations=[FastApiIntegration()],
        traces_sample_rate=0.1,
        environment=os.getenv("ENV", "production"),
    )
```

### Logging Configuration

```python
import logging

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.getenv("LOG_FILE", "hrisa.log")),
        logging.StreamHandler()
    ]
)
```

### Health Check Endpoint

```python
@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agents": {
            "total": len(agent_manager.agents),
            "running": sum(1 for a in agent_manager.agents.values() if a.status == "running"),
        }
    }
```

### Metrics Export

Consider exporting metrics to:
- Prometheus
- DataDog
- New Relic
- CloudWatch

## Backup & Recovery

### What to Backup

1. **Configuration Files**
   - `.env` or environment variables
   - `config.yaml`
   - Integration configurations

2. **Database** (if using)
   - Agent history
   - Webhook configurations
   - Notification channels

3. **Ollama Models**
   - Model files (can be large)
   - Model configurations

### Backup Strategy

```bash
# Daily backup script
#!/bin/bash

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/hrisa/$DATE"

mkdir -p "$BACKUP_DIR"

# Backup database
pg_dump $DATABASE_URL > "$BACKUP_DIR/database.sql"

# Backup configurations
cp .env "$BACKUP_DIR/"
cp config.yaml "$BACKUP_DIR/"

# Backup to S3
aws s3 sync "$BACKUP_DIR" "s3://your-bucket/hrisa-backups/$DATE/"

# Cleanup old backups (keep 30 days)
find /backups/hrisa -type d -mtime +30 -exec rm -rf {} +
```

### Recovery Procedure

1. **Restore Database**
   ```bash
   psql $DATABASE_URL < backup/database.sql
   ```

2. **Restore Configurations**
   ```bash
   cp backup/.env ./
   cp backup/config.yaml ./
   ```

3. **Restart Services**
   ```bash
   docker-compose down
   docker-compose up -d
   ```

4. **Verify Health**
   ```bash
   curl https://your-domain.com/health
   ```

## Performance Tuning

### Database

- Add indexes on frequently queried fields
- Use connection pooling
- Configure appropriate pool size

### Caching

- Use Redis for session data
- Cache agent statuses
- Cache model performance metrics

### Concurrent Agents

Balance between performance and resources:

```python
# Conservative (2GB RAM)
MAX_CONCURRENT_AGENTS=3

# Moderate (4GB RAM)
MAX_CONCURRENT_AGENTS=5

# Aggressive (8GB+ RAM)
MAX_CONCURRENT_AGENTS=10
```

### Ollama

- Use GPU acceleration if available
- Configure appropriate context size
- Use quantized models for faster inference

## Troubleshooting

### High Memory Usage

**Symptoms**: OOM errors, slow performance

**Solutions**:
- Reduce `MAX_CONCURRENT_AGENTS`
- Use smaller Ollama models
- Enable swap (not recommended for production)
- Increase container memory limits

### Webhook Failures

**Symptoms**: High failure count, timeout errors

**Solutions**:
- Verify webhook URLs are accessible
- Check firewall rules
- Increase `WEBHOOK_TIMEOUT_SECONDS`
- Enable webhook retry logic
- Review webhook event logs

### Agent Stuck States

**Symptoms**: Agents not completing

**Solutions**:
- Review agent logs for errors
- Adjust `STUCK_THRESHOLD_SECONDS`
- Check Ollama connectivity
- Review model performance metrics

### Database Connection Issues

**Symptoms**: Connection refused, pool exhausted

**Solutions**:
- Verify database is running
- Check connection string
- Increase connection pool size
- Implement connection retry logic

## Support

For production support:
- GitHub Issues: https://github.com/your-repo/hrisa-code/issues
- Documentation: https://docs.yourdomain.com
- Email: support@yourdomain.com

---

**Last Updated**: 2026-03-06
