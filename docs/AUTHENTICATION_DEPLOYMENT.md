# Authentication System Deployment Guide

This guide provides step-by-step instructions for deploying the Hrisa Code web application with RBAC + Magic Link authentication to production.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start (Docker)](#quick-start-docker)
- [Production Deployment](#production-deployment)
  - [Database Setup](#database-setup)
  - [SMTP Configuration](#smtp-configuration)
  - [Application Configuration](#application-configuration)
  - [Running Migrations](#running-migrations)
  - [Creating Admin User](#creating-admin-user)
- [Deployment Platforms](#deployment-platforms)
  - [Render.com](#rendercom)
  - [Railway.app](#railwayapp)
  - [AWS EC2](#aws-ec2)
  - [DigitalOcean](#digitalocean)
  - [Heroku](#heroku)
- [Security Checklist](#security-checklist)
- [Monitoring](#monitoring)
- [Backup & Recovery](#backup--recovery)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- Python 3.10+
- PostgreSQL 14+ database (managed service recommended)
- SMTP email service (SendGrid, Mailgun, AWS SES, etc.)
- Domain name with SSL certificate (optional but recommended)
- Docker (for containerized deployment)

## Quick Start (Docker)

For local or Docker-based deployments:

### 1. Clone and Configure

```bash
git clone <repository-url>
cd Hrisa-Code

# Copy and edit environment file
cp .env.example .env
nano .env
```

### 2. Update Environment Variables

```env
# Database (use external PostgreSQL URL)
DATABASE_URL=postgresql://user:password@host:5432/database

# SMTP (production service)
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your-sendgrid-api-key
SMTP_FROM_EMAIL=noreply@yourdomain.com

# Application
APP_BASE_URL=https://yourdomain.com
SECRET_KEY=$(openssl rand -hex 32)
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### 3. Start Services

```bash
# Start all services (PostgreSQL + Web + Ollama)
docker-compose up -d

# Run migrations
docker exec -it hrisa-web alembic upgrade head

# Create admin user
docker exec -it hrisa-web python scripts/create_admin.py admin@yourdomain.com
```

### 4. Verify Deployment

```bash
# Check service health
docker-compose ps

# View logs
docker-compose logs -f web

# Test API
curl https://yourdomain.com/api/stats
```

## Production Deployment

### Database Setup

#### Option 1: Managed PostgreSQL (Recommended)

**AWS RDS:**
```bash
# Create RDS instance
aws rds create-db-instance \
    --db-instance-identifier hrisa-db \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --engine-version 16.1 \
    --master-username hrisa \
    --master-user-password YOUR_PASSWORD \
    --allocated-storage 20 \
    --vpc-security-group-ids sg-xxxxx

# Get connection URL
aws rds describe-db-instances --db-instance-identifier hrisa-db --query 'DBInstances[0].Endpoint'

# Connection URL format:
# postgresql://hrisa:PASSWORD@hrisa-db.xxxxx.us-east-1.rds.amazonaws.com:5432/postgres
```

**Google Cloud SQL:**
```bash
# Create Cloud SQL instance
gcloud sql instances create hrisa-db \
    --database-version=POSTGRES_16 \
    --tier=db-f1-micro \
    --region=us-central1

# Create database
gcloud sql databases create hrisa --instance=hrisa-db

# Get connection info
gcloud sql instances describe hrisa-db
```

**DigitalOcean Managed Database:**
```bash
# Create via web UI or API
doctl databases create hrisa-db \
    --engine pg \
    --region nyc1 \
    --size db-s-1vcpu-1gb
```

#### Option 2: Self-Hosted PostgreSQL

```bash
# Install PostgreSQL
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib

# Configure PostgreSQL for remote access
sudo nano /etc/postgresql/16/main/postgresql.conf
# Set: listen_addresses = '*'

sudo nano /etc/postgresql/16/main/pg_hba.conf
# Add: host all all 0.0.0.0/0 md5

# Restart PostgreSQL
sudo systemctl restart postgresql

# Create database and user
sudo -u postgres psql
CREATE DATABASE hrisa;
CREATE USER hrisa WITH ENCRYPTED PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE hrisa TO hrisa;
\q
```

**Security Hardening:**
- Enable SSL connections
- Restrict access by IP (use security groups/firewall)
- Use strong passwords (32+ characters)
- Enable automated backups
- Set up monitoring

### SMTP Configuration

#### SendGrid (Recommended for Production)

```bash
# Sign up at https://sendgrid.com
# Create API key with "Mail Send" permission

# .env configuration
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
SMTP_FROM_EMAIL=noreply@yourdomain.com
```

**Verify sender email:**
1. Go to SendGrid → Settings → Sender Authentication
2. Verify your domain or single sender
3. Add SPF and DKIM DNS records

#### AWS SES

```bash
# Verify domain in SES console
aws ses verify-domain-identity --domain yourdomain.com

# Get SMTP credentials
aws ses get-send-quota

# .env configuration
SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USER=your-smtp-username
SMTP_PASSWORD=your-smtp-password
SMTP_FROM_EMAIL=noreply@yourdomain.com
```

#### Mailgun

```bash
# .env configuration
SMTP_HOST=smtp.mailgun.org
SMTP_PORT=587
SMTP_USER=postmaster@yourdomain.com
SMTP_PASSWORD=your-mailgun-password
SMTP_FROM_EMAIL=noreply@yourdomain.com
```

### Application Configuration

#### Generate Production SECRET_KEY

```bash
# Generate secure random key
openssl rand -hex 32
# Copy output to SECRET_KEY in .env
```

#### Configure CORS Origins

```env
# Restrict to your actual domains only
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com,https://app.yourdomain.com
```

#### Environment Variables Checklist

```env
# Required
DATABASE_URL=postgresql://user:pass@host:5432/db
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your-user
SMTP_PASSWORD=your-password
SMTP_FROM_EMAIL=noreply@yourdomain.com
APP_BASE_URL=https://yourdomain.com
SECRET_KEY=generate-with-openssl-rand-hex-32
ALLOWED_ORIGINS=https://yourdomain.com

# Optional
DB_ECHO=false
SESSION_EXPIRY_DAYS=30
MAGIC_LINK_EXPIRY_MINUTES=15
LOG_LEVEL=INFO
```

### Running Migrations

```bash
# Method 1: Using Alembic directly
alembic upgrade head

# Method 2: Using migration script
./scripts/migrate.sh

# Method 3: Using Python script
python scripts/run_migrations.py

# Verify migrations
psql $DATABASE_URL -c "\dt"
# Should show 6 tables: users, magic_link_tokens, sessions, agents, teams, audit_logs
```

### Creating Admin User

```bash
# Create first admin user
python scripts/create_admin.py admin@yourdomain.com

# Or use SQL directly
psql $DATABASE_URL <<EOF
INSERT INTO users (id, email, role, is_active, created_at)
VALUES (gen_random_uuid(), 'admin@yourdomain.com', 'admin', true, now());
EOF
```

## Deployment Platforms

### Render.com

**1. Create PostgreSQL Database:**
- Go to Render Dashboard → New → PostgreSQL
- Name: hrisa-db
- Plan: Starter ($7/month)
- Copy "Internal Database URL"

**2. Deploy Web Service:**
- Go to New → Web Service
- Connect your GitHub repo
- Configure:
  - Name: hrisa-web
  - Environment: Docker
  - Instance Type: Starter ($7/month)
  - Environment Variables:
    ```
    DATABASE_URL=<paste-internal-database-url>
    SMTP_HOST=smtp.sendgrid.net
    SMTP_PORT=587
    SMTP_USER=apikey
    SMTP_PASSWORD=<sendgrid-api-key>
    SMTP_FROM_EMAIL=noreply@yourdomain.com
    APP_BASE_URL=https://hrisa-web.onrender.com
    SECRET_KEY=<generate-with-openssl-rand>
    ALLOWED_ORIGINS=https://hrisa-web.onrender.com
    ```

**3. Run Migrations:**
```bash
# Via Render Shell
# Go to Service → Shell
alembic upgrade head
python scripts/create_admin.py admin@example.com
```

**4. Custom Domain (Optional):**
- Go to Settings → Custom Domain
- Add your domain
- Update DNS CNAME record

### Railway.app

**1. Deploy via CLI:**
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Create project
railway init

# Add PostgreSQL
railway add postgresql

# Deploy
railway up

# Set environment variables
railway variables set SMTP_HOST=smtp.sendgrid.net
railway variables set SMTP_PORT=587
# ... set all other variables
```

**2. Run Migrations:**
```bash
railway run alembic upgrade head
railway run python scripts/create_admin.py admin@example.com
```

### AWS EC2

**1. Launch EC2 Instance:**
```bash
# Launch Ubuntu 22.04 instance
aws ec2 run-instances \
    --image-id ami-0c7217cdde317cfec \
    --instance-type t3.small \
    --key-name your-key-pair \
    --security-group-ids sg-xxxxx \
    --subnet-id subnet-xxxxx

# SSH into instance
ssh -i your-key.pem ubuntu@ec2-xxx-xxx-xxx-xxx.compute.amazonaws.com
```

**2. Install Dependencies:**
```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install Python 3.10+
sudo apt-get install python3.10 python3.10-venv python3-pip -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt-get install docker-compose-plugin -y
```

**3. Deploy Application:**
```bash
# Clone repository
git clone <repository-url>
cd Hrisa-Code

# Create .env file
cp .env.example .env
nano .env
# Paste production configuration

# Start services
docker-compose up -d

# Run migrations
docker exec -it hrisa-web alembic upgrade head

# Create admin
docker exec -it hrisa-web python scripts/create_admin.py admin@yourdomain.com
```

**4. Setup Nginx Reverse Proxy:**
```bash
# Install Nginx
sudo apt-get install nginx -y

# Configure
sudo nano /etc/nginx/sites-available/hrisa

# Paste configuration:
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Enable site
sudo ln -s /etc/nginx/sites-available/hrisa /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

**5. Setup SSL with Let's Encrypt:**
```bash
sudo apt-get install certbot python3-certbot-nginx -y
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
sudo systemctl reload nginx
```

### DigitalOcean

**Using App Platform:**
1. Go to DigitalOcean → App Platform → Create App
2. Connect GitHub repo
3. Add PostgreSQL database ($15/month)
4. Configure environment variables
5. Deploy

**Using Droplet (Same as AWS EC2 above)**

### Heroku

**Note:** Heroku ended free tier. Paid plans start at $7/month.

```bash
# Install Heroku CLI
curl https://cli-assets.heroku.com/install.sh | sh

# Login
heroku login

# Create app
heroku create hrisa-web

# Add PostgreSQL
heroku addons:create heroku-postgresql:mini

# Set environment variables
heroku config:set SMTP_HOST=smtp.sendgrid.net
heroku config:set SMTP_PORT=587
# ... set all variables

# Deploy
git push heroku main

# Run migrations
heroku run alembic upgrade head

# Create admin
heroku run python scripts/create_admin.py admin@example.com
```

## Security Checklist

### Before Going Live

- [ ] **HTTPS Enabled**: Force HTTPS in production
- [ ] **Strong SECRET_KEY**: Generated with `openssl rand -hex 32`
- [ ] **Database Security**:
  - [ ] Strong password (32+ characters)
  - [ ] SSL connections enabled
  - [ ] Access restricted by IP/security group
  - [ ] Automated backups enabled
- [ ] **SMTP Security**:
  - [ ] Using production email service (not Gmail)
  - [ ] SPF and DKIM records configured
  - [ ] DMARC policy set
- [ ] **CORS Configuration**:
  - [ ] `ALLOWED_ORIGINS` restricted to actual domains
  - [ ] No wildcard (`*`) in production
- [ ] **Environment Variables**:
  - [ ] No secrets in code or git
  - [ ] `.env` in `.gitignore`
  - [ ] All production values set
- [ ] **Rate Limiting**: Consider adding rate limiting middleware
- [ ] **Monitoring**: Set up error tracking (Sentry, etc.)
- [ ] **Backups**: Database automated backups enabled
- [ ] **Audit Logs**: Review regularly for suspicious activity

### Post-Deployment Security

```bash
# Check for exposed secrets
grep -r "SECRET_KEY\|PASSWORD\|API_KEY" .env

# Verify .env not in git
git ls-files | grep .env

# Test HTTPS redirect
curl -I http://yourdomain.com

# Test CORS
curl -H "Origin: https://malicious.com" https://yourdomain.com/api/agents

# Review audit logs
psql $DATABASE_URL -c "SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 20;"
```

## Monitoring

### Application Logs

```bash
# Docker logs
docker-compose logs -f web

# Tail logs
tail -f /var/log/hrisa/app.log

# Filter errors
docker-compose logs web | grep ERROR
```

### Database Monitoring

```sql
-- Check active sessions
SELECT count(*) FROM sessions WHERE expires_at > now();

-- Check user activity
SELECT email, last_login FROM users ORDER BY last_login DESC;

-- Audit log summary
SELECT action, count(*) FROM audit_logs GROUP BY action;

-- Failed login attempts
SELECT details->>'email', count(*)
FROM audit_logs
WHERE action = 'auth.magic_link_sent'
GROUP BY details->>'email'
HAVING count(*) > 10;
```

### Health Check Endpoint

```bash
# Check API health
curl https://yourdomain.com/api/stats

# Expected response:
{
  "agents": {...},
  "system": {...}
}
```

### Sentry Integration (Optional)

```bash
# Install Sentry SDK
pip install sentry-sdk[fastapi]

# Add to server.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    integrations=[FastApiIntegration()],
)
```

## Backup & Recovery

### Database Backups

**Automated Backups (Managed PostgreSQL):**
- Most managed services have built-in backups
- Ensure daily backups enabled
- Test restore process monthly

**Manual Backup:**
```bash
# Backup database
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Backup to S3
pg_dump $DATABASE_URL | gzip | aws s3 cp - s3://your-bucket/backups/hrisa_$(date +%Y%m%d).sql.gz

# Restore from backup
psql $DATABASE_URL < backup_20240115.sql
```

**Backup Schedule:**
```bash
# Add to crontab
0 2 * * * pg_dump $DATABASE_URL | gzip > /backups/hrisa_$(date +\%Y\%m\%d).sql.gz
```

### Disaster Recovery Plan

1. **Database Failure:**
   ```bash
   # Restore from latest backup
   psql $NEW_DATABASE_URL < latest_backup.sql

   # Update DATABASE_URL in .env
   # Restart application
   docker-compose restart web
   ```

2. **Application Failure:**
   ```bash
   # Redeploy from git
   git pull
   docker-compose up -d --build
   ```

3. **Complete Infrastructure Loss:**
   - Restore PostgreSQL from backup
   - Redeploy application to new infrastructure
   - Update DNS records
   - Verify all services operational

## Troubleshooting

### Common Issues

#### Database Connection Fails

```bash
# Test connection
psql $DATABASE_URL -c "SELECT 1;"

# Check connection string format
# postgresql://user:password@host:port/database

# Verify PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres
```

#### Magic Links Not Sending

```bash
# Test SMTP connection
telnet $SMTP_HOST $SMTP_PORT

# Check SMTP credentials
python -c "
import os
print('Host:', os.getenv('SMTP_HOST'))
print('Port:', os.getenv('SMTP_PORT'))
print('User:', os.getenv('SMTP_USER'))
print('From:', os.getenv('SMTP_FROM_EMAIL'))
"

# Verify email service status
# - SendGrid: Check dashboard for errors
# - AWS SES: Check bounce/complaint rates
# - Mailgun: Check logs
```

#### 401 Unauthorized Errors

```bash
# Check if DATABASE_URL is set
env | grep DATABASE_URL

# Verify tables exist
psql $DATABASE_URL -c "\dt"

# Check sessions table
psql $DATABASE_URL -c "SELECT count(*) FROM sessions WHERE expires_at > now();"
```

#### Performance Issues

```bash
# Check database connections
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity;"

# Check slow queries
psql $DATABASE_URL -c "SELECT query, total_time FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"

# Add indexes if needed
psql $DATABASE_URL -c "CREATE INDEX idx_custom ON table_name (column);"
```

### Getting Help

- **Documentation**: [GitHub Repository](https://github.com/your-org/hrisa-code)
- **Issues**: [GitHub Issues](https://github.com/your-org/hrisa-code/issues)
- **Email**: support@yourdomain.com

## Maintenance

### Regular Tasks

**Daily:**
- [ ] Check error logs
- [ ] Monitor email delivery rates
- [ ] Review failed login attempts

**Weekly:**
- [ ] Review audit logs for suspicious activity
- [ ] Check database backup status
- [ ] Monitor disk space usage

**Monthly:**
- [ ] Test backup restore process
- [ ] Update dependencies
- [ ] Review user access levels
- [ ] Clean up expired sessions/tokens
- [ ] Security audit

### Cleanup Tasks

```sql
-- Delete expired magic link tokens (older than 1 day)
DELETE FROM magic_link_tokens WHERE expires_at < now() - interval '1 day';

-- Delete expired sessions
DELETE FROM sessions WHERE expires_at < now();

-- Archive old audit logs (older than 1 year)
CREATE TABLE audit_logs_archive AS
SELECT * FROM audit_logs WHERE created_at < now() - interval '1 year';

DELETE FROM audit_logs WHERE created_at < now() - interval '1 year';
```

### Upgrade Process

```bash
# 1. Backup database
pg_dump $DATABASE_URL > backup_pre_upgrade.sql

# 2. Pull latest code
git pull

# 3. Install dependencies
pip install -e ".[web]"

# 4. Run migrations
alembic upgrade head

# 5. Restart application
docker-compose restart web

# 6. Verify
curl https://yourdomain.com/api/stats

# 7. Monitor logs
docker-compose logs -f web
```

## Success Metrics

Your deployment is successful when:

- ✅ Application accessible via HTTPS
- ✅ Users can register and receive magic links
- ✅ Database migrations completed without errors
- ✅ Admin panel functional
- ✅ Audit logs recording all actions
- ✅ Email delivery rate > 95%
- ✅ API response time < 500ms
- ✅ Zero 500 errors in logs
- ✅ Automated backups running daily
- ✅ Monitoring alerts configured
