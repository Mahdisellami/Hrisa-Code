# Deployment Checklist

Quick reference for deploying Hrisa Code to production.

## Pre-Deployment

### 1. Code Preparation
- [ ] All tests passing (`make test`)
- [ ] No linting errors (`make lint`)
- [ ] Type checking clean (`make type-check`)
- [ ] Code formatted (`make format`)
- [ ] All changes committed to git
- [ ] Pushed to GitHub main branch

### 2. Configuration Files
- [ ] `vercel.json` configured
- [ ] `render.yaml` configured
- [ ] `docker/Dockerfile.ollama` present
- [ ] `docker/entrypoint.sh` executable
- [ ] `.env.example` updated with all variables

### 3. Secrets Generated
```bash
# Generate these secrets and save securely
openssl rand -hex 32  # SECRET_KEY
openssl rand -hex 32  # WEBHOOK_SECRET
```

- [ ] `SECRET_KEY` generated
- [ ] `WEBHOOK_SECRET` generated (if using webhooks)
- [ ] SMTP credentials obtained (if using email notifications)
- [ ] Slack/Discord webhook URLs obtained (if using)

## Render Deployment

### 4. Create Render Account
- [ ] Sign up at https://render.com/register
- [ ] Connect GitHub account
- [ ] Add payment method (required for persistent disks)

### 5. Deploy Ollama Service
- [ ] Create Private Service
- [ ] Set Runtime: Docker
- [ ] Dockerfile Path: `./docker/Dockerfile.ollama`
- [ ] Add persistent disk (20 GB)
- [ ] Set environment variables:
  ```
  OLLAMA_HOST=0.0.0.0
  OLLAMA_MODELS=qwen2.5-coder:7b
  ```
- [ ] Deploy and wait for model download (10-15 min)
- [ ] Verify health check passes

### 6. Deploy Backend API
- [ ] Create Web Service
- [ ] Set Runtime: Python 3
- [ ] Build Command: `pip install -e ".[web]"`
- [ ] Start Command: `uvicorn hrisa_code.web.server:app --host 0.0.0.0 --port $PORT`
- [ ] Set environment variables:
  ```
  OLLAMA_HOST=http://hrisa-ollama:11434
  HOST=0.0.0.0
  PORT=8000
  SECRET_KEY=<your-generated-secret>
  ALLOWED_ORIGINS=<will-update-after-vercel>
  MAX_CONCURRENT_AGENTS=5
  LOG_LEVEL=INFO
  DEBUG=false
  ```
- [ ] Deploy and verify health check
- [ ] Copy backend URL (e.g., `https://hrisa-backend.onrender.com`)

## Vercel Deployment

### 7. Create Vercel Account
- [ ] Sign up at https://vercel.com/signup
- [ ] Connect GitHub account

### 8. Deploy Frontend
- [ ] Import GitHub repository
- [ ] Framework Preset: Other
- [ ] Build Command: (leave empty)
- [ ] Output Directory: `src/hrisa_code/web/static`
- [ ] Set environment variables:
  ```
  BACKEND_URL=https://hrisa-backend.onrender.com
  ```
- [ ] Deploy and verify
- [ ] Copy Vercel URL (e.g., `https://your-app.vercel.app`)

## Post-Deployment Configuration

### 9. Update CORS
- [ ] Go to Render backend → Environment
- [ ] Update `ALLOWED_ORIGINS`:
  ```
  ALLOWED_ORIGINS=https://your-app.vercel.app,https://your-app-git-main-username.vercel.app
  ```
- [ ] Save and redeploy

### 10. Verify Deployment
- [ ] Visit frontend URL
- [ ] Create test agent
- [ ] Verify agent creation works
- [ ] Check WebSocket/polling works
- [ ] Test all major features:
  - [ ] Agent list view
  - [ ] Agent details view
  - [ ] Teams view
  - [ ] Model metrics view
  - [ ] Priority queue view
  - [ ] Network graph view
  - [ ] Activity timeline view
  - [ ] Performance charts view
  - [ ] Resource usage view
  - [ ] System metrics view
  - [ ] Integrations view
  - [ ] Exports working

### 11. Health Checks
```bash
# Backend health
curl https://hrisa-backend.onrender.com/health

# Ollama health
curl https://hrisa-ollama.onrender.com/api/tags

# Frontend loads
curl -I https://your-app.vercel.app
```

- [ ] Backend health check returns 200
- [ ] Ollama API responds
- [ ] Frontend loads without errors

## Optional: Custom Domain

### 12. Vercel Custom Domain
- [ ] Go to Vercel project → Settings → Domains
- [ ] Add custom domain
- [ ] Update DNS records (A/CNAME)
- [ ] Wait for HTTPS certificate (automatic)
- [ ] Verify domain works

### 13. Render Custom Domain
- [ ] Go to Render service → Settings → Custom Domain
- [ ] Add custom domain
- [ ] Update DNS records (CNAME)
- [ ] Wait for HTTPS certificate (automatic)
- [ ] Update Vercel `BACKEND_URL` to custom domain
- [ ] Update backend `ALLOWED_ORIGINS` to include new domain

## Optional: CI/CD Setup

### 14. GitHub Actions Secrets
- [ ] Go to GitHub repo → Settings → Secrets
- [ ] Add secrets:
  - `VERCEL_TOKEN` (from Vercel account settings)
  - `VERCEL_ORG_ID` (from Vercel project settings)
  - `VERCEL_PROJECT_ID` (from Vercel project settings)
  - `RENDER_DEPLOY_HOOK_URL` (from Render service settings)
  - `SLACK_WEBHOOK_URL` (optional, for notifications)
- [ ] Push to main to trigger workflow
- [ ] Verify automated deployment works

## Optional: Monitoring

### 15. Set Up Monitoring
- [ ] Create Sentry account (optional)
- [ ] Add `SENTRY_DSN` to backend environment
- [ ] Set up uptime monitoring (UptimeRobot, Pingdom, etc.)
- [ ] Configure alerting for downtime
- [ ] Set up log aggregation (Papertrail, Loggly, etc.)

## Optional: Database

### 16. Add PostgreSQL Database
- [ ] Create database in Render
- [ ] Copy `DATABASE_URL`
- [ ] Add to backend environment variables
- [ ] Redeploy backend
- [ ] Run migrations if needed

## Maintenance

### 17. Regular Tasks
- [ ] Monitor error logs weekly
- [ ] Check resource usage monthly
- [ ] Update dependencies quarterly
- [ ] Rotate secrets every 90 days
- [ ] Review and optimize costs monthly
- [ ] Backup database weekly (if using)

## Troubleshooting Quick Reference

**Backend not responding:**
```bash
# Check Render logs
render logs hrisa-backend --tail 100

# Check health endpoint
curl -v https://hrisa-backend.onrender.com/health
```

**Ollama not responding:**
```bash
# Check Ollama logs
render logs hrisa-ollama --tail 100

# Check if models loaded
curl https://hrisa-ollama.onrender.com/api/tags
```

**CORS errors:**
1. Check `ALLOWED_ORIGINS` includes Vercel URL
2. Verify Vercel `BACKEND_URL` is correct
3. Check browser console for exact error

**Deployment failed:**
1. Check build logs in Render/Vercel dashboard
2. Verify all environment variables set
3. Check for syntax errors in config files

## Cost Tracking

**Monthly Costs:**
- Render Ollama (Standard): $25/month
- Render Backend (Starter): $7/month
- Render Database (optional): $7/month
- Vercel (Free/Pro): $0-20/month

**Total: $32-59/month**

## Support

- Render Support: https://render.com/docs/support
- Vercel Support: https://vercel.com/support
- Hrisa Code Issues: https://github.com/yourusername/hrisa-code/issues

---

**See detailed guide:** [VERCEL_RENDER.md](./VERCEL_RENDER.md)
