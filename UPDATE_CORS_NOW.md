# Update CORS NOW - Quick 2-Minute Fix

## ✅ Deployment Complete!

**New Frontend URL:** https://hrisa-frontend.vercel.app

The frontend is deployed with fixed asset paths. Now you just need to update CORS in Render.

---

## 🎯 Update CORS (Do This Now)

### Step 1: Open Render Dashboard
Click: **https://dashboard.render.com/web/srv-d6l94ia4d50c73b542lg**

### Step 2: Go to Environment Tab
- Look for tabs: Events | Settings | Monitor | **Manage**
- Under Manage, click **"Environment"**

### Step 3: Update ALLOWED_ORIGINS

**If it exists:**
1. Find `ALLOWED_ORIGINS` in the list
2. Click the **pencil/edit icon**
3. Change value to:
   ```
   https://hrisa-backend.onrender.com,https://hrisa-frontend.vercel.app
   ```
4. Click **"Save Changes"**

**If it doesn't exist:**
1. Click **"Add Environment Variable"**
2. **Key**: `ALLOWED_ORIGINS`
3. **Value**: `https://hrisa-backend.onrender.com,https://hrisa-frontend.vercel.app`
4. Click **"Save"**

### Step 4: Wait 30 Seconds
Render will automatically redeploy with the new CORS setting.

---

## ✅ Test (After 30 Seconds)

1. Visit: **https://hrisa-frontend.vercel.app**
2. Should see login page (purple gradient)
3. Try entering an email
4. CORS error should be **GONE**

You might see:
```
500 Internal Server Error
```

**That's good!** It means:
- ✅ Frontend working
- ✅ CORS working
- ⚠️ Backend needs DATABASE_URL (next step)

---

## 🚀 What Was Fixed

**Problem:**
- Old paths: `/static/app.js` → MIME type errors
- Wrong Vercel projects deployed

**Fixed:**
- ✅ Paths: `/app.js` and `/styles.css` (correct)
- ✅ Fresh Vercel deployment
- ✅ New clean URL: hrisa-frontend.vercel.app

**Just need:**
- 🔲 Update CORS (2 minutes - do now!)

---

## Alternative: Use Wildcard (Temporary)

If you want to test quickly, set ALLOWED_ORIGINS to:
```
*
```

This allows ALL origins (less secure, but good for testing).

Change it to specific origins later for production.

---

**Action Required:** Update ALLOWED_ORIGINS in Render (see Step 3 above)

After that, your frontend will work! 🎉
