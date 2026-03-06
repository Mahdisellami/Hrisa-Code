# Render Deployment Automation

This guide shows you how to use the automation scripts to minimize manual work when deploying to Render.com.

## What Can Be Automated?

✅ **Fully Automated (with Render API key):**
- Setting all environment variables
- Triggering deployment
- Generating SECRET_KEY

⚠️ **Semi-Automated (still need manual step):**
- Running migrations (paste script in Render Shell)
- Creating admin user (one command in Render Shell)

❌ **Cannot Automate (must do manually):**
- Creating PostgreSQL database (Render Dashboard)
- Getting database ID and service ID (from Render URLs)
- Getting Gmail app password (Google account settings)

---

## Quick Start

### Option A: Fully Automated (Recommended)

**Prerequisites:**
1. PostgreSQL database already created in Render
2. Render API key from: https://dashboard.render.com/u/settings#api-keys
3. Gmail app password from: https://myaccount.google.com/apppasswords

**Steps:**

1. **Find your IDs** (from Render Dashboard URLs):
   - Service ID: `https://dashboard.render.com/web/srv-XXXXX` → copy `srv-XXXXX`
   - Database ID: `https://dashboard.render.com/d/dpg-YYYYY` → copy `dpg-YYYYY`

2. **Run the automation script:**
   ```bash
   export RENDER_API_KEY=rnd_xxxxxxxxxxxxx
   python scripts/deploy-to-render.py \
     --service-id srv-XXXXX \
     --database-id dpg-YYYYY \
     --gmail your-email@gmail.com \
     --admin-email admin@yourdomain.com
   ```

3. **Wait for deployment** (~5-10 minutes)
   - Monitor at: https://dashboard.render.com/services/srv-XXXXX

4. **Run migrations** (in Render Shell):
   - Go to: Render Dashboard → Your Service → Shell → Launch Shell
   - Paste:
   ```bash
   alembic upgrade head && python scripts/create_admin.py admin@yourdomain.com
   ```

5. **Test login:**
   - Visit: https://hrisa-mywebsite.vercel.app
   - Enter your admin email
   - Check email for magic link

---

### Option B: Manual with Helper Files

If you prefer manual configuration or don't have API access:

1. **Create PostgreSQL in Render Dashboard:**
   - Click "New +" → "PostgreSQL"
   - Name: `hrisa-db`
   - Plan: Starter ($7/month) or Free
   - **Copy Internal Database URL**

2. **Use pre-filled environment variables:**
   - Open `.env.production` (already generated with SECRET_KEY)
   - Replace these placeholders:
     - `<YOUR_RENDER_POSTGRES_INTERNAL_URL>` → paste from step 1
     - `<YOUR_GMAIL_ADDRESS>` → your email
     - `<YOUR_GMAIL_APP_PASSWORD>` → from https://myaccount.google.com/apppasswords
   - Copy all variables to Render Dashboard → Environment tab

3. **Trigger deployment:**
   - Render should auto-deploy after env vars are added
   - Or click "Manual Deploy" → "Deploy latest commit"

4. **Run migrations** (in Render Shell):
   ```bash
   bash < <(curl -s https://raw.githubusercontent.com/YOUR_REPO/main/scripts/render-shell-setup.sh)
   ```
   Or paste the script manually from `scripts/render-shell-setup.sh`

5. **Create admin user:**
   ```bash
   python scripts/create_admin.py admin@yourdomain.com
   ```

---

## Files Created for You

1. **`.env.production`** - Pre-filled environment variables
   - SECRET_KEY already generated: `30a909bcb8b888c5a2078b49a7d3f951f0c768dc5d3eb89f93054eb564ed836d`
   - Just fill in: PostgreSQL URL, Gmail credentials

2. **`scripts/deploy-to-render.py`** - Automated deployment script
   - Uses Render API to configure everything
   - Requires: API key, service ID, database ID

3. **`scripts/render-shell-setup.sh`** - Shell setup script
   - Runs migrations
   - Verifies database tables
   - Instructions for creating admin user

---

## Detailed Instructions

### Getting Render API Key

1. Go to: https://dashboard.render.com/u/settings#api-keys
2. Click "Create API Key"
3. Name: "Hrisa Code Deployment"
4. Copy the key (starts with `rnd_`)
5. Export it:
   ```bash
   export RENDER_API_KEY=rnd_xxxxxxxxxxxxx
   ```

### Getting Gmail App Password

1. Enable 2FA on your Gmail account (required)
2. Go to: https://myaccount.google.com/apppasswords
3. Select "Mail" as app type
4. Click "Generate"
5. Copy the 16-character password (no spaces)
6. Use this password, NOT your regular Gmail password

### Finding Service and Database IDs

**Service ID:**
- Go to your web service in Render Dashboard
- URL looks like: `https://dashboard.render.com/web/srv-abc123xyz`
- Service ID is: `srv-abc123xyz`

**Database ID:**
- Go to your PostgreSQL database in Render Dashboard
- URL looks like: `https://dashboard.render.com/d/dpg-def456uvw`
- Database ID is: `dpg-def456uvw`

---

## Automation Script Usage

### Basic Usage (Interactive):
```bash
python scripts/deploy-to-render.py \
  --service-id srv-XXXXX \
  --database-id dpg-YYYYY
```
*Script will prompt for API key, Gmail address, and Gmail app password*

### Non-Interactive Usage:
```bash
export RENDER_API_KEY=rnd_xxxxxxxxxxxxx
python scripts/deploy-to-render.py \
  --service-id srv-XXXXX \
  --database-id dpg-YYYYY \
  --gmail your-email@gmail.com \
  --admin-email admin@yourdomain.com
```

### Update Env Vars Only (Don't Deploy):
```bash
python scripts/deploy-to-render.py \
  --service-id srv-XXXXX \
  --database-id dpg-YYYYY \
  --skip-deploy
```

---

## Troubleshooting

### "Failed to fetch database info"
- **Cause**: Database doesn't exist or ID is wrong
- **Fix**: Create PostgreSQL in Render Dashboard first, double-check ID

### "Failed to update environment variables"
- **Cause**: Service ID is wrong or API key lacks permissions
- **Fix**: Verify service ID, regenerate API key with full permissions

### "Alembic not found" in Render Shell
- **Cause**: Dependencies not installed
- **Fix**: Run `pip install -e ".[web]"` in Render Shell

### Migration fails with "relation already exists"
- **Cause**: Database already has tables from previous attempt
- **Fix**: Either:
  1. Use existing tables: `python scripts/create_admin.py your-email@example.com`
  2. Reset database: `DROP SCHEMA public CASCADE; CREATE SCHEMA public;` (⚠️ deletes all data)

### Magic link email not received
- **Cause**: SMTP credentials incorrect or Gmail blocking
- **Fix**:
  1. Verify Gmail app password (not regular password)
  2. Check spam/junk folder
  3. Test SMTP in Render Shell:
     ```bash
     python -c "
     import asyncio, os, aiosmtplib
     from email.message import EmailMessage
     async def test():
         msg = EmailMessage()
         msg['From'] = os.getenv('SMTP_FROM_EMAIL')
         msg['To'] = 'your-email@example.com'
         msg['Subject'] = 'Test'
         msg.set_content('Test email')
         await aiosmtplib.send(msg, hostname=os.getenv('SMTP_HOST'),
                               port=int(os.getenv('SMTP_PORT')),
                               username=os.getenv('SMTP_USER'),
                               password=os.getenv('SMTP_PASSWORD'),
                               start_tls=True)
         print('✓ Email sent')
     asyncio.run(test())
     "
     ```

---

## Verification Checklist

After deployment, verify:

- [ ] Backend accessible: https://hrisa-backend.onrender.com/api/stats
- [ ] Database has 6 tables: users, magic_link_tokens, sessions, agents, teams, audit_logs
- [ ] Environment variables set (14 variables)
- [ ] Logs show "Database initialized successfully"
- [ ] Frontend shows login page: https://hrisa-mywebsite.vercel.app
- [ ] Can request magic link (no errors in console)
- [ ] Magic link email received
- [ ] Can log in successfully
- [ ] User profile shows admin role
- [ ] Admin panel accessible

---

## Cost Summary

**Render Starter Plan (~$14/month):**
- Web Service: $7/month
- PostgreSQL: $7/month

**Free Alternative (with limitations):**
- Web Service: Free (spins down after 15 min inactivity)
- PostgreSQL: Free for 90 days, then $7/month

**Or use external free PostgreSQL:**
- Railway.app (5GB free)
- Supabase (500MB free)
- ElephantSQL (20MB free)

---

## Support

For detailed troubleshooting, see:
- `RENDER_DEPLOYMENT.md` - Comprehensive deployment guide
- `docs/AUTHENTICATION_TESTING.md` - Testing scenarios
- `docs/AUTHENTICATION_DEPLOYMENT.md` - Multi-platform deployment

---

**Last Updated**: 2026-03-06
**Generated Files**:
- `.env.production` (environment variables with SECRET_KEY)
- `scripts/deploy-to-render.py` (automation script)
- `scripts/render-shell-setup.sh` (shell setup script)
