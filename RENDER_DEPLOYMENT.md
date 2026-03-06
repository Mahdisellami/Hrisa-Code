# Render.com Deployment Guide - Authentication Update

## Current Situation

Your Hrisa Code backend is deployed on Render at:
- **Backend**: https://hrisa-backend.onrender.com
- **Status**: Running but missing authentication system (returns 404 on `/api/auth/*` endpoints)

The authentication code was just pushed to GitHub (commit `639fd48`), but Render needs:
1. **Redeploy** to pull the latest code
2. **PostgreSQL database** to be added
3. **Environment variables** for authentication
4. **Database migrations** to run

## Step-by-Step Deployment

### Step 1: Add PostgreSQL Database

1. **Go to Render Dashboard**: https://dashboard.render.com
2. **Create PostgreSQL Database**:
   - Click **"New +"** → **"PostgreSQL"**
   - Name: `hrisa-db`
   - Database: `hrisa`
   - User: `hrisa`
   - Region: Same as your web service (for low latency)
   - Plan: **Starter ($7/month)** or Free (if available)
   - Click **"Create Database"**

3. **Copy Connection String**:
   - Once created, click on the database
   - Find **"Internal Database URL"** (starts with `postgresql://`)
   - Copy this URL - you'll need it in Step 2

### Step 2: Configure Environment Variables

1. **Go to Your Web Service**:
   - Dashboard → Select `hrisa-backend` (or your service name)
   - Go to **"Environment"** tab

2. **Add Required Variables**:

Click **"Add Environment Variable"** for each:

```env
# Database (REQUIRED)
DATABASE_URL=<paste-internal-database-url-from-step-1>

# SMTP Email (REQUIRED) - Get Gmail App Password
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=<your-gmail-app-password>
SMTP_FROM_EMAIL=noreply@hrisa.local

# Application (REQUIRED)
APP_BASE_URL=https://hrisa-backend.onrender.com
SECRET_KEY=<generate-this-see-below>
ALLOWED_ORIGINS=https://hrisa-backend.onrender.com,https://hrisa-mywebsite.vercel.app

# Optional
SESSION_EXPIRY_DAYS=30
MAGIC_LINK_EXPIRY_MINUTES=15
DB_ECHO=false
LOG_LEVEL=INFO
```

3. **Generate SECRET_KEY**:
   - On your local machine, run:
     ```bash
     openssl rand -hex 32
     ```
   - Copy the output (64-character hex string)
   - Paste as `SECRET_KEY` value

4. **Get Gmail App Password** (if using Gmail):
   - Enable 2FA on your Gmail account
   - Go to: https://myaccount.google.com/apppasswords
   - Create app password for "Mail"
   - Copy the 16-character password (no spaces)
   - Use this as `SMTP_PASSWORD`

5. **Save Environment Variables**:
   - Click **"Save Changes"**
   - Render will automatically start redeploying

### Step 3: Trigger Manual Deploy (if needed)

If Render didn't auto-deploy after adding environment variables:

1. Go to your web service
2. Click **"Manual Deploy"** button at top right
3. Select **"Deploy latest commit"**
4. Wait for deployment to complete (~5-10 minutes)

### Step 4: Run Database Migrations

After deployment completes:

1. **Go to Shell**:
   - Your web service → **"Shell"** tab
   - Click **"Launch Shell"**

2. **Run Migrations**:
   ```bash
   # Check if Alembic is installed
   alembic --version

   # Run migrations
   alembic upgrade head

   # Verify tables were created
   python -c "
   import os
   import psycopg2
   conn = psycopg2.connect(os.getenv('DATABASE_URL'))
   cur = conn.cursor()
   cur.execute(\"SELECT tablename FROM pg_tables WHERE schemaname='public'\")
   print('Tables:', [row[0] for row in cur.fetchall()])
   cur.close()
   conn.close()
   "
   ```

   **Expected output**: Tables should include: users, magic_link_tokens, sessions, agents, teams, audit_logs

3. **Create Admin User** (Optional):
   ```bash
   python scripts/create_admin.py admin@yourdomain.com
   ```

### Step 5: Verify Deployment

1. **Test Authentication Endpoint**:
   ```bash
   curl -I https://hrisa-backend.onrender.com/api/auth/send-magic-link
   ```
   **Expected**: HTTP 200 or 405 (not 404)

2. **Test Stats Endpoint** (should still work):
   ```bash
   curl https://hrisa-backend.onrender.com/api/stats
   ```

3. **Check Logs**:
   - Go to **"Logs"** tab
   - Look for:
     - ✅ "Database initialized successfully"
     - ✅ "Application startup complete"
     - ❌ Any errors related to DATABASE_URL or migrations

4. **Test Frontend**:
   - Go to: https://hrisa-mywebsite.vercel.app
   - You should see the login page (purple gradient)
   - Try entering an email
   - Check if you receive magic link email

### Step 6: Update Frontend API URL (if needed)

Your frontend at Vercel needs to know about the auth endpoints:

1. **Check app.js**:
   ```javascript
   const API_BASE = 'https://hrisa-backend.onrender.com/api';
   ```
   ✅ This looks correct - it should already be set

2. **If you need to update it**:
   - Update the `API_BASE` constant in your deployed frontend
   - Redeploy Vercel frontend

## Troubleshooting

### Issue: "Database not initialized" in logs

**Solution**: DATABASE_URL environment variable not set correctly

1. Check environment variables in Render
2. Ensure DATABASE_URL is the **Internal Database URL** (not External)
3. Restart service

### Issue: "Failed to send email" errors

**Solutions**:

1. **Gmail App Password not working**:
   - Verify 2FA is enabled on Gmail
   - Generate new app password
   - Copy without spaces
   - Update SMTP_PASSWORD in Render

2. **Use SendGrid instead** (recommended for production):
   ```env
   SMTP_HOST=smtp.sendgrid.net
   SMTP_PORT=587
   SMTP_USER=apikey
   SMTP_PASSWORD=<sendgrid-api-key>
   SMTP_FROM_EMAIL=noreply@yourdomain.com
   ```
   - Sign up at: https://sendgrid.com
   - Free tier: 100 emails/day
   - Create API key with "Mail Send" permission

### Issue: "Migration failed" or "Alembic not found"

**Solution**: Dependencies not installed

1. Check if `pyproject.toml` includes:
   ```toml
   web = [
       "sqlalchemy[asyncio]>=2.0.0",
       "asyncpg>=0.29.0",
       "alembic>=1.13.0",
       "aiosmtplib>=3.0.0",
   ]
   ```

2. In Render Shell:
   ```bash
   pip install -e ".[web]"
   alembic upgrade head
   ```

### Issue: Frontend shows 401 errors

**Solution**: CORS configuration

1. Check ALLOWED_ORIGINS includes your frontend URL
2. Update environment variable:
   ```env
   ALLOWED_ORIGINS=https://hrisa-backend.onrender.com,https://hrisa-mywebsite.vercel.app
   ```
3. Restart service

### Issue: Tables not created

**Solution**: Run migrations manually

```bash
# In Render Shell
alembic upgrade head

# Or using Python directly
python -c "
import asyncio
from hrisa_code.web.db.database import init_database
import os

async def create_tables():
    db = await init_database(os.getenv('DATABASE_URL'))
    print('Tables created successfully')

asyncio.run(create_tables())
"
```

## Verification Checklist

After deployment, verify:

- [ ] Backend accessible at https://hrisa-backend.onrender.com
- [ ] `/api/stats` endpoint returns JSON
- [ ] `/api/auth/send-magic-link` returns 200 (not 404)
- [ ] PostgreSQL database shows 6 tables
- [ ] Environment variables all set (DATABASE_URL, SMTP_*, SECRET_KEY)
- [ ] Logs show "Database initialized successfully"
- [ ] Frontend shows login page (not error)
- [ ] Can request magic link (email received)
- [ ] Can log in via magic link
- [ ] User profile dropdown visible after login

## Cost Breakdown (Render)

**Current Setup:**
- Web Service: $7/month (Starter)
- PostgreSQL: $7/month (Starter) **NEW**
- **Total**: ~$14/month

**Free Alternative** (limitations apply):
- Web Service: Free (spins down after 15 min inactivity)
- PostgreSQL: Free (90 days, then $7/month)
- **Total**: Free initially, then $7/month

## Alternative: Use External PostgreSQL

If Render's PostgreSQL is too expensive, use:

1. **Railway.app**: Free PostgreSQL (5GB)
   - Sign up: https://railway.app
   - Create PostgreSQL service
   - Copy connection URL
   - Use as DATABASE_URL in Render

2. **ElephantSQL**: Free tier (20MB limit)
   - Sign up: https://elephantsql.com
   - Create tiny turtle instance (free)
   - Copy URL
   - Use as DATABASE_URL in Render

3. **Supabase**: Free PostgreSQL (500MB)
   - Sign up: https://supabase.com
   - Create project
   - Get connection string (direct connection)
   - Use as DATABASE_URL in Render

## Next Steps After Deployment

1. **Test Authentication**:
   - Follow `docs/AUTHENTICATION_TESTING.md`
   - Verify all 9 test scenarios pass

2. **Create Admin User**:
   - Either: Be the first to register (auto-admin)
   - Or: Use `scripts/create_admin.py` in Render Shell

3. **Monitor**:
   - Check Render logs regularly
   - Review audit logs in database
   - Monitor email delivery rates

4. **Secure**:
   - Change SECRET_KEY to production value
   - Use production SMTP (SendGrid, not Gmail)
   - Enable HTTPS (Render does this automatically)
   - Verify CORS allows only your frontend

## Support

If issues persist:

1. Check Render logs: Service → Logs tab
2. Check database logs: Database → Logs tab
3. Review: `docs/AUTHENTICATION_DEPLOYMENT.md`
4. Test locally first with: `docs/AUTHENTICATION_TESTING.md`

## Quick Commands Reference

```bash
# In Render Shell

# Check environment
env | grep DATABASE_URL
env | grep SMTP

# Run migrations
alembic upgrade head

# Create admin
python scripts/create_admin.py admin@example.com

# Check tables
python -c "import os; import psycopg2; conn = psycopg2.connect(os.getenv('DATABASE_URL')); cur = conn.cursor(); cur.execute('SELECT tablename FROM pg_tables WHERE schemaname=\\'public\\''); print([row[0] for row in cur.fetchall()])"

# Test SMTP
python -c "
import asyncio
import os
from hrisa_code.web.auth.email import create_email_service_from_env

async def test():
    svc = create_email_service_from_env()
    if svc:
        print('Email service configured')
        result = await svc.send_email('test@example.com', 'Test', '<p>Test</p>')
        print('Sent:', result)
    else:
        print('Email service NOT configured')

asyncio.run(test())
"
```

---

**Last Updated**: After commit `639fd48`
**Status**: Ready for Render deployment
