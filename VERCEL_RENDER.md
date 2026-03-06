# Vercel + Render Deployment Guide

Complete guide for deploying Hrisa Code with Vercel (frontend) and Render (backend).

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Architecture](#architecture)
- [Step-by-Step Deployment](#step-by-step-deployment)
- [Configuration](#configuration)
- [Environment Variables](#environment-variables)
- [Monitoring & Maintenance](#monitoring--maintenance)
- [Troubleshooting](#troubleshooting)
- [Cost Estimation](#cost-estimation)

## Overview

This deployment architecture separates concerns:
- **Vercel**: Hosts static frontend files (HTML, CSS, JavaScript)
- **Render**: Hosts FastAPI backend + Ollama LLM service

**Benefits:**
- ✅ Vercel's global CDN for fast frontend delivery
- ✅ Render's persistent disks for Ollama models
- ✅ Automatic HTTPS on both platforms
- ✅ Easy scaling and monitoring
- ✅ Free tier available for testing

## Prerequisites

### Accounts Required
1. **Vercel Account** - https://vercel.com/signup
2. **Render Account** - https://render.com/register
3. **GitHub Account** - For repository hosting

### Local Requirements
- Git installed and configured
- GitHub repository with Hrisa Code pushed
- Basic understanding of environment variables

### Repository Setup
```bash
# Ensure your code is committed
git add .
git commit -m "Prepare for deployment"

# Push to GitHub (create repo first at github.com)
git remote add origin https://github.com/yourusername/hrisa-code.git
git push -u origin main
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         INTERNET                             │
└───────────────┬─────────────────────────────────────────────┘
                │
        ┌───────┴────────┐
        │                │
   ┌────▼─────┐    ┌────▼──────┐
   │  Vercel  │    │  Render   │
   │ Frontend │◄───┤  Backend  │
   │  (CDN)   │    │  (API)    │
   └──────────┘    └─────┬─────┘
                         │
                   ┌─────▼──────┐
                   │   Render   │
                   │   Ollama   │
                   │  (LLM GPU) │
                   └────────────┘
```

**Request Flow:**
1. User accesses `https://your-app.vercel.app`
2. Vercel serves static files (HTML, CSS, JS)
3. JavaScript makes API calls to `https://hrisa-backend.onrender.com`
4. Backend communicates with Ollama service internally
5. Responses returned to frontend

## Step-by-Step Deployment

### Part 1: Deploy Backend to Render

#### 1.1 Create Render Account
- Go to https://render.com/register
- Sign up with GitHub (recommended for easy deploys)

#### 1.2 Deploy Ollama Service

**Option A: Using Blueprint (Recommended)**

1. Push `render.yaml` to your GitHub repo
2. In Render dashboard, click **New** → **Blueprint**
3. Connect your GitHub repository
4. Render will detect `render.yaml` and create all services
5. Click **Apply** to start deployment

**Option B: Manual Setup**

1. In Render dashboard, click **New** → **Private Service**
2. Select your GitHub repository
3. Configure:
   - **Name**: `hrisa-ollama`
   - **Runtime**: Docker
   - **Dockerfile Path**: `./docker/Dockerfile.ollama`
   - **Plan**: Standard (requires paid plan for persistent disk)
4. Add disk:
   - **Name**: `ollama-models`
   - **Mount Path**: `/root/.ollama`
   - **Size**: 20 GB
5. Add environment variables:
   ```
   OLLAMA_HOST=0.0.0.0
   OLLAMA_MODELS=qwen2.5-coder:7b
   ```
6. Click **Create Private Service**

**Wait for Ollama to deploy (10-15 minutes for model download)**

#### 1.3 Deploy Backend API

1. In Render dashboard, click **New** → **Web Service**
2. Select your GitHub repository
3. Configure:
   - **Name**: `hrisa-backend`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -e ".[web]"`
   - **Start Command**: `uvicorn hrisa_code.web.server:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Starter ($7/month) or Free
4. Add environment variables (see [Environment Variables](#environment-variables) below)
5. Click **Create Web Service**

**Copy the backend URL** (e.g., `https://hrisa-backend.onrender.com`)

### Part 2: Deploy Frontend to Vercel

#### 2.1 Create Vercel Account
- Go to https://vercel.com/signup
- Sign up with GitHub

#### 2.2 Deploy Frontend

1. In Vercel dashboard, click **Add New** → **Project**
2. Import your GitHub repository
3. Configure:
   - **Framework Preset**: Other
   - **Root Directory**: `./`
   - **Build Command**: Leave empty (static files)
   - **Output Directory**: `src/hrisa_code/web/static`
4. Add environment variables:
   ```
   BACKEND_URL=https://hrisa-backend.onrender.com
   ```
5. Click **Deploy**

**Deployment takes 30-60 seconds**

#### 2.3 Update Frontend Configuration

After deployment, update `app.js` to use production backend:

1. In Vercel dashboard, go to your project → **Settings** → **Environment Variables**
2. Add:
   ```
   NEXT_PUBLIC_API_BASE=https://hrisa-backend.onrender.com
   ```
3. Redeploy for changes to take effect

### Part 3: Configure CORS

Update backend to allow Vercel origin:

1. In Render dashboard, go to `hrisa-backend` → **Environment**
2. Update `ALLOWED_ORIGINS`:
   ```
   ALLOWED_ORIGINS=https://your-app.vercel.app,https://your-app-git-main-yourusername.vercel.app
   ```
3. Save changes (auto-redeploys)

## Configuration

### Backend Configuration (Render)

**Key Settings:**
- **Auto-Deploy**: Enabled (deploys on git push)
- **Health Check Path**: `/health`
- **Health Check Interval**: 30 seconds

**Scaling:**
- Free tier: 0.1 CPU, 512 MB RAM
- Starter tier: 0.5 CPU, 512 MB RAM
- Standard tier: 1 CPU, 2 GB RAM (recommended)

### Frontend Configuration (Vercel)

**Key Settings:**
- **Build Command**: None (static files)
- **Output Directory**: `src/hrisa_code/web/static`
- **Node.js Version**: Not required

**Custom Domain (Optional):**
1. Go to **Settings** → **Domains**
2. Add your custom domain
3. Update DNS records as instructed
4. HTTPS certificate auto-provisioned

## Environment Variables

### Backend (Render)

**Required:**
```bash
# Ollama Configuration
OLLAMA_HOST=http://hrisa-ollama:11434  # Internal Render service URL

# Server Configuration
HOST=0.0.0.0
PORT=8000  # Render sets this automatically
RELOAD=false

# Security (CRITICAL)
SECRET_KEY=<generate-with-openssl-rand-hex-32>
ALLOWED_ORIGINS=https://your-app.vercel.app

# Agent Configuration
MAX_CONCURRENT_AGENTS=5
STUCK_THRESHOLD_SECONDS=120
```

**Optional:**
```bash
# Webhooks
WEBHOOK_TIMEOUT_SECONDS=10
MAX_WEBHOOK_RETRIES=0
ENABLE_WEBHOOK_SIGNATURES=true

# Logging
LOG_LEVEL=INFO
DEBUG=false

# Database (if using PostgreSQL)
DATABASE_URL=postgresql://user:pass@host/dbname

# Monitoring
SENTRY_DSN=https://...@sentry.io/...
```

### Frontend (Vercel)

**Required:**
```bash
BACKEND_URL=https://hrisa-backend.onrender.com
# Or use environment-specific URLs:
NEXT_PUBLIC_API_BASE=https://hrisa-backend.onrender.com
```

### Generating Secrets

```bash
# SECRET_KEY for backend
openssl rand -hex 32

# WEBHOOK_SECRET for integrations
openssl rand -hex 32
```

## Monitoring & Maintenance

### Health Checks

**Backend Health:**
```bash
curl https://hrisa-backend.onrender.com/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-03-06T10:30:00Z",
  "agents": {
    "total": 0,
    "running": 0
  }
}
```

### Render Dashboard

Monitor in Render:
- **Logs**: Real-time logs for debugging
- **Metrics**: CPU, memory, request count
- **Events**: Deployment history
- **Shell**: Access running container

### Vercel Dashboard

Monitor in Vercel:
- **Deployments**: Build logs and preview URLs
- **Analytics**: Page views, performance metrics
- **Logs**: Function execution logs (if using serverless functions)

### Logging

**View Backend Logs:**
1. Render dashboard → `hrisa-backend` → **Logs**
2. Or via CLI:
   ```bash
   render logs hrisa-backend
   ```

**View Ollama Logs:**
1. Render dashboard → `hrisa-ollama` → **Logs**
2. Check model loading progress

## Troubleshooting

### Issue 1: Backend Connection Failed

**Symptoms**: Frontend shows "Failed to fetch agents"

**Solutions:**
1. Verify backend is running:
   ```bash
   curl https://hrisa-backend.onrender.com/health
   ```
2. Check CORS settings in backend `ALLOWED_ORIGINS`
3. Verify Vercel environment variable `BACKEND_URL` is correct
4. Check browser console for CORS errors

### Issue 2: Ollama Not Responding

**Symptoms**: Backend logs show "Connection refused" to Ollama

**Solutions:**
1. Check Ollama service is running in Render dashboard
2. Verify `OLLAMA_HOST` is set to internal service URL:
   ```
   http://hrisa-ollama:11434
   ```
3. Check Ollama logs for model loading errors
4. Ensure disk space is sufficient (20+ GB)

### Issue 3: Slow Model Loading

**Symptoms**: First request takes 30+ seconds

**Solutions:**
1. Models load on first request - this is expected
2. Keep backend warm with periodic health checks:
   ```bash
   # Cron job (every 5 minutes)
   */5 * * * * curl https://hrisa-backend.onrender.com/health
   ```
3. Use smaller models for faster loading (e.g., `qwen2.5-coder:7b` instead of `32b`)

### Issue 4: Deployment Failed

**Symptoms**: Render build fails

**Solutions:**
1. Check build logs in Render dashboard
2. Verify `requirements.txt` or `pyproject.toml` is correct
3. Ensure Python version matches (3.10+)
4. Check for missing dependencies:
   ```bash
   pip install -e ".[web]"
   ```

### Issue 5: WebSocket Connection Failed

**Symptoms**: Real-time updates not working

**Solutions:**
1. Vercel doesn't support WebSockets on free tier
2. Use HTTP polling as fallback (already implemented in frontend)
3. Or deploy frontend elsewhere (Netlify, custom server)

### Issue 6: High Memory Usage

**Symptoms**: Backend crashes with OOM errors

**Solutions:**
1. Reduce `MAX_CONCURRENT_AGENTS` to 2-3
2. Upgrade Render plan to Standard (2 GB RAM)
3. Use smaller Ollama models
4. Monitor memory in Render metrics

## Cost Estimation

### Render

**Ollama Service:**
- Standard Plan: **$25/month**
- Includes: 1 CPU, 2 GB RAM, 20 GB disk
- Required for persistent models

**Backend API:**
- Free Tier: **$0/month** (with limitations: spins down after inactivity)
- Starter Plan: **$7/month** (always on, 0.5 CPU, 512 MB RAM)
- Standard Plan: **$25/month** (1 CPU, 2 GB RAM) - Recommended

**Database (Optional):**
- PostgreSQL Free: **$0/month** (up to 1 GB)
- PostgreSQL Starter: **$7/month** (10 GB)

**Total Minimum: $25-32/month** (Ollama + API)
**Total Recommended: $50-57/month** (with Standard plans)

### Vercel

**Hobby (Free):**
- 100 GB bandwidth/month
- Unlimited deployments
- HTTPS included
- **$0/month**

**Pro (Paid):**
- 1 TB bandwidth/month
- Advanced analytics
- **$20/month**

### Total Cost

**Development/Testing**: **$25-32/month** (Render only + Vercel free)
**Production**: **$50-77/month** (Render Standard + Vercel Pro)

**Cost Savings Tips:**
1. Use Free Render tier for API during development
2. Share Ollama service across multiple projects
3. Use Vercel free tier unless you need analytics
4. Scale down when not in use (Render allows pausing services)

## Next Steps

1. ✅ Deploy and verify health checks
2. ✅ Set up custom domain (optional)
3. ✅ Configure monitoring (Sentry, DataDog)
4. ✅ Set up backups (database if using)
5. ✅ Create staging environment (optional)
6. ✅ Set up CI/CD pipeline (GitHub Actions)

## Additional Resources

- [Render Documentation](https://render.com/docs)
- [Vercel Documentation](https://vercel.com/docs)
- [Ollama Documentation](https://ollama.ai/docs)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)
- [PRODUCTION.md](./PRODUCTION.md) - General production guide

## Support

For issues:
- **Render Support**: https://render.com/docs/support
- **Vercel Support**: https://vercel.com/support
- **Hrisa Code Issues**: https://github.com/yourusername/hrisa-code/issues

---

**Last Updated**: 2026-03-06
