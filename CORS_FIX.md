# CORS Fix - Frontend URL Changed

## Problem

Frontend moved to new URL: `https://hrisa-code-new.vercel.app`
Backend CORS is blocking requests because it's configured for old URL.

**Error:**
```
Access to fetch at 'https://hrisa-backend.onrender.com/api/auth/send-magic-link'
from origin 'https://hrisa-code-new.vercel.app' has been blocked by CORS policy
```

## Quick Fix (2 minutes)

### Option 1: Allow All Origins (Temporary - For Testing)

1. Go to Render Dashboard:
   https://dashboard.render.com/web/srv-d6l94ia4d50c73b542lg

2. Click **Environment** tab

3. Find or add `ALLOWED_ORIGINS` variable:
   - **Key**: `ALLOWED_ORIGINS`
   - **Value**: `*`

4. Click **Save Changes**

5. Wait 30 seconds for automatic redeploy

6. Test: Visit https://hrisa-code-new.vercel.app and try logging in

---

### Option 2: Specific Origins (Recommended - For Production)

1. Go to Render Dashboard → Environment tab

2. Set `ALLOWED_ORIGINS` to:
   ```
   https://hrisa-backend.onrender.com,https://hrisa-code-new.vercel.app
   ```

3. Click **Save Changes**

4. Wait 30 seconds for automatic redeploy

---

## Using Automation Script

If you have Render API key:

```bash
export RENDER_API_KEY=rnd_your_key

# Update just ALLOWED_ORIGINS
curl -X PUT "https://api.render.com/v1/services/srv-d6l94ia4d50c73b542lg/env-vars" \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '[{"key": "ALLOWED_ORIGINS", "value": "https://hrisa-backend.onrender.com,https://hrisa-code-new.vercel.app"}]'
```

---

## Verification

After updating:

```bash
# Should see Access-Control-Allow-Origin header
curl -I -X OPTIONS "https://hrisa-backend.onrender.com/api/auth/send-magic-link" \
  -H "Origin: https://hrisa-code-new.vercel.app" \
  -H "Access-Control-Request-Method: POST"
```

Or visit frontend and check browser console - CORS error should be gone.

---

## Other Frontend Favicon Issue

The favicon error on frontend is separate:
```
GET https://hrisa-code-new.vercel.app/favicon.ico 404 (Not Found)
```

This is a Vercel deployment issue, not Render. You need to add a favicon to your frontend repo.

---

## Why This Happened

The backend CORS configuration reads from `ALLOWED_ORIGINS` environment variable in Render.

When we initially deployed, we set it to the old frontend URL:
- Old: `https://hrisa-mywebsite.vercel.app`
- New: `https://hrisa-code-new.vercel.app`

Render is still using the old value.

---

## Files Updated

- `.env.production` - Updated to new frontend URL
- This will be committed shortly

---

**Action Required:** Update ALLOWED_ORIGINS in Render Dashboard (see Option 1 or 2 above)
