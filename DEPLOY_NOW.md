# Deploy Now - Quick Start Guide

This is the fastest way to deploy Hrisa Code to production. Follow these steps in order.

## Prerequisites ✅

Before you begin, ensure you have:
- [ ] GitHub account with this repository pushed
- [ ] SSH keys configured for git push
- [ ] Credit card (for Render - required even for free tier trial)

## Step 1: Push to GitHub (5 minutes)

```bash
# Configure SSH keys if needed
ssh-keygen -t ed25519 -C "your.email@example.com"
cat ~/.ssh/id_ed25519.pub
# Copy output and add to GitHub: Settings → SSH and GPG keys → New SSH key

# Push the code
git push origin main
```

**Verify**: Visit your GitHub repository and confirm all files are there.

## Step 2: Deploy Backend to Render (15 minutes)

### 2.1 Create Render Account
1. Go to https://render.com/register
2. Click **"Sign up with GitHub"**
3. Authorize Render to access your repositories
4. Add payment method (required for persistent disks)

### 2.2 Deploy Using Blueprint (Easiest)
1. In Render dashboard, click **"New +"** → **"Blueprint"**
2. Connect your `hrisa-code` repository
3. Render detects `render.yaml` automatically
4. Click **"Apply"**
5. Wait 10-15 minutes for Ollama to download models

**Or Manual Setup** (if Blueprint doesn't work):

**Ollama Service:**
1. Click **"New +"** → **"Private Service"**
2. Connect repository
3. Settings:
   - Name: `hrisa-ollama`
   - Runtime: **Docker**
   - Dockerfile Path: `./docker/Dockerfile.ollama`
   - Plan: **Standard** ($25/month - required for disk)
4. Add Disk:
   - Name: `ollama-models`
   - Mount Path: `/root/.ollama`
   - Size: **20 GB**
5. Environment Variables:
   ```
   OLLAMA_HOST=0.0.0.0
   OLLAMA_MODELS=qwen2.5-coder:7b
   ```
6. Click **"Create Private Service"**
7. Wait for "Live" status (10-15 min)

**Backend API:**
1. Click **"New +"** → **"Web Service"**
2. Connect repository
3. Settings:
   - Name: `hrisa-backend`
   - Runtime: **Python 3**
   - Build Command: `pip install -e ".[web]"`
   - Start Command: `uvicorn hrisa_code.web.server:app --host 0.0.0.0 --port $PORT`
   - Plan: **Starter** ($7/month) or Free
4. Environment Variables:
   ```
   OLLAMA_HOST=http://hrisa-ollama:11434
   HOST=0.0.0.0
   SECRET_KEY=<generate below>
   ALLOWED_ORIGINS=<will update after Vercel>
   MAX_CONCURRENT_AGENTS=5
   LOG_LEVEL=INFO
   DEBUG=false
   ```
5. Click **"Create Web Service"**
6. Copy the URL (e.g., `https://hrisa-backend.onrender.com`)

**Generate SECRET_KEY:**
```bash
openssl rand -hex 32
```

## Step 3: Deploy Frontend to Vercel (5 minutes)

### 3.1 Create Vercel Account
1. Go to https://vercel.com/signup
2. Click **"Continue with GitHub"**
3. Authorize Vercel

### 3.2 Deploy Project
1. Click **"Add New..."** → **"Project"**
2. Import `hrisa-code` repository
3. Configure:
   - Framework Preset: **Other**
   - Root Directory: `./`
   - Build Command: (leave empty)
   - Output Directory: `src/hrisa_code/web/static`
4. Environment Variables:
   ```
   BACKEND_URL=https://hrisa-backend.onrender.com
   ```
   (Use your actual Render backend URL from Step 2)
5. Click **"Deploy"**
6. Wait 30-60 seconds
7. Copy the Vercel URL (e.g., `https://your-app.vercel.app`)

## Step 4: Update CORS (2 minutes)

1. Go to Render dashboard → `hrisa-backend` → **"Environment"**
2. Find `ALLOWED_ORIGINS` and update:
   ```
   ALLOWED_ORIGINS=https://your-app.vercel.app,https://your-app-git-main-yourusername.vercel.app
   ```
3. Click **"Save Changes"** (auto-redeploys)

## Step 5: Verify Deployment (5 minutes)

### Test Backend
```bash
curl https://hrisa-backend.onrender.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2026-03-06T...",
  "agents": {"total": 0, "running": 0}
}
```

### Test Frontend
1. Visit `https://your-app.vercel.app`
2. Click **"+ New Agent"**
3. Enter task: "Say hello"
4. Click **"Create Agent"**
5. Verify agent appears in list

**If you see "Failed to fetch":**
- Check CORS settings in Render
- Verify backend URL in Vercel environment variables
- Check browser console for errors

## Step 6: Optional - Custom Domain

### Vercel Custom Domain
1. Vercel dashboard → Project → **"Settings"** → **"Domains"**
2. Add domain: `hrisa.yourdomain.com`
3. Update DNS:
   ```
   Type: CNAME
   Name: hrisa
   Value: cname.vercel-dns.com
   ```
4. Wait for HTTPS (automatic, 5-10 minutes)

### Render Custom Domain
1. Render dashboard → Service → **"Settings"** → **"Custom Domain"**
2. Add domain: `api.yourdomain.com`
3. Update DNS:
   ```
   Type: CNAME
   Name: api
   Value: <provided by Render>
   ```
4. Update Vercel `BACKEND_URL` to use custom domain
5. Update Render `ALLOWED_ORIGINS` to include custom domain

## Step 7: Optional - CI/CD with GitHub Actions

### Add Secrets to GitHub
1. Go to GitHub repository → **"Settings"** → **"Secrets and variables"** → **"Actions"**
2. Click **"New repository secret"** for each:

   **VERCEL_TOKEN** (from Vercel):
   - Vercel dashboard → **"Settings"** → **"Tokens"**
   - Create token → Copy

   **VERCEL_ORG_ID** (from Vercel):
   - Vercel dashboard → **"Settings"**
   - Copy "Organization ID" under General

   **VERCEL_PROJECT_ID** (from Vercel):
   - Vercel project → **"Settings"** → **"General"**
   - Copy "Project ID"

   **RENDER_DEPLOY_HOOK_URL** (from Render):
   - Render dashboard → Service → **"Settings"** → **"Deploy Hook"**
   - Create deploy hook → Copy URL

   **SLACK_WEBHOOK_URL** (optional):
   - Create Slack Incoming Webhook
   - Copy webhook URL

3. Push any commit to `main` branch
4. GitHub Actions will automatically test and deploy!

## Troubleshooting

### Backend Returns 503
**Issue**: Ollama not ready yet
**Solution**: Wait 10-15 minutes for model download. Check Render logs.

### Frontend Shows CORS Error
**Issue**: CORS misconfigured
**Solution**: Verify `ALLOWED_ORIGINS` includes exact Vercel URL (with https://)

### Agent Creation Fails
**Issue**: Backend can't reach Ollama
**Solution**: Check `OLLAMA_HOST=http://hrisa-ollama:11434` (internal URL)

### WebSocket Not Working
**Issue**: Vercel free tier doesn't support WebSockets
**Solution**: App uses HTTP polling as fallback - should work automatically

## Cost Summary

**Minimum Setup:**
- Render Ollama (Standard): $25/month
- Render Backend (Free): $0/month (spins down after inactivity)
- Vercel (Free): $0/month
- **Total: $25/month**

**Recommended Production:**
- Render Ollama (Standard): $25/month
- Render Backend (Starter): $7/month (always on)
- Vercel (Free): $0/month
- **Total: $32/month**

**Professional:**
- Render Ollama (Standard): $25/month
- Render Backend (Standard): $25/month (better performance)
- Vercel Pro: $20/month (analytics, more bandwidth)
- **Total: $70/month**

## Next Steps

After deployment:
1. ✅ Test all features (agents, teams, exports, integrations)
2. ✅ Set up monitoring (optional - Sentry, UptimeRobot)
3. ✅ Configure webhooks for Slack/Discord notifications
4. ✅ Set up backups if using database
5. ✅ Invite team members

## Support

- **Detailed Guide**: See `VERCEL_RENDER.md`
- **Checklist**: See `DEPLOYMENT_CHECKLIST.md`
- **Production**: See `PRODUCTION.md`

---

**Estimated Time**: 30-45 minutes total
**Skill Level**: Beginner-friendly (just follow steps)
**Cost**: $25-32/month for production-ready deployment
