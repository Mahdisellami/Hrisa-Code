# Vercel Fresh Deployment Guide

## Step 1: Delete Old Vercel Projects

### Via Vercel Dashboard (Easiest)

1. **Go to Vercel Dashboard**: https://vercel.com/dashboard

2. **Find all projects related to Hrisa**:
   - Look for projects like:
     - `hrisa-mywebsite`
     - `hrisa-code-new`
     - Any other Hrisa-related projects

3. **Delete each project**:
   - Click on the project
   - Go to **Settings** (top navigation)
   - Scroll to bottom → **"Delete Project"** section
   - Click **"Delete"**
   - Type the project name to confirm
   - Click **"Delete"**

4. **Repeat for all Hrisa projects**

---

## Step 2: Prepare Frontend Code

The frontend code is in: `src/hrisa_code/web/static/`

Key files:
- `index.html` - Main HTML
- `app.js` - JavaScript (with auth logic)
- `styles.css` - Styles

### Check Current API URL

Before deploying, verify the backend URL in `app.js`:

```bash
grep -n "API_BASE\|const API" src/hrisa_code/web/static/app.js | head -5
```

Should be:
```javascript
const API_BASE = 'https://hrisa-backend.onrender.com/api';
```

If it's not, we'll update it.

---

## Step 3: Create New Vercel Project

### Option A: Via Vercel CLI (Recommended)

1. **Install Vercel CLI** (if not installed):
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel**:
   ```bash
   vercel login
   ```

3. **Deploy from static directory**:
   ```bash
   cd src/hrisa_code/web/static
   vercel --prod
   ```

4. **Follow prompts**:
   - Set up and deploy? **Y**
   - Which scope? (Select your account)
   - Link to existing project? **N**
   - What's your project's name? **hrisa-frontend**
   - In which directory is your code located? **.**
   - Want to modify settings? **N**

5. **Copy the deployment URL** (e.g., `https://hrisa-frontend-xxx.vercel.app`)

---

### Option B: Via Vercel Dashboard (Manual Upload)

1. **Go to**: https://vercel.com/new

2. **Click "Add New..." → "Project"**

3. **Import Git Repository**:
   - Connect GitHub if not connected
   - Select: `Mahdisellami/Hrisa-Code`
   - Click **"Import"**

4. **Configure Project**:
   - **Project Name**: `hrisa-frontend`
   - **Framework Preset**: Other
   - **Root Directory**: Click "Edit" → Enter: `src/hrisa_code/web/static`
   - **Build Command**: Leave empty (static files)
   - **Output Directory**: `.` (current directory)
   - **Install Command**: Leave empty

5. **Click "Deploy"**

6. **Wait 1-2 minutes** for deployment

7. **Copy the deployment URL**

---

### Option C: Create vercel.json Configuration

This approach creates a config file in the repo.

1. **Create vercel.json** in repo root:
   ```json
   {
     "version": 2,
     "name": "hrisa-frontend",
     "builds": [
       {
         "src": "src/hrisa_code/web/static/**",
         "use": "@vercel/static"
       }
     ],
     "routes": [
       {
         "src": "/(.*)",
         "dest": "/src/hrisa_code/web/static/$1"
       }
     ]
   }
   ```

2. **Deploy**:
   ```bash
   vercel --prod
   ```

---

## Step 4: Update CORS for New Frontend URL

After deployment, you'll have a new URL like:
`https://hrisa-frontend-xxx.vercel.app`

### Update Render Backend CORS:

1. **Go to Render Dashboard**:
   https://dashboard.render.com/web/srv-d6l94ia4d50c73b542lg

2. **Environment tab**

3. **Update ALLOWED_ORIGINS**:
   ```
   https://hrisa-backend.onrender.com,https://YOUR_NEW_VERCEL_URL.vercel.app
   ```

4. **Save** (auto-redeploys in 30 seconds)

---

## Step 5: Verify Deployment

### Test Frontend:

1. Visit your new Vercel URL
2. Check browser console (F12)
3. Should see login page

### Test Backend Connection:

1. Try to login with any email
2. Check console for errors
3. CORS error should be **gone**
4. You might see 500 error (that's OK - means backend needs DATABASE_URL)

---

## Troubleshooting

### Frontend shows blank page:

**Check Vercel build logs**:
- Dashboard → Your Project → Deployments → Click latest
- Check for errors

**Common fix**: Ensure Root Directory is set to `src/hrisa_code/web/static`

### API_BASE URL is wrong:

Update `src/hrisa_code/web/static/app.js`:
```javascript
const API_BASE = 'https://hrisa-backend.onrender.com/api';
```

Then redeploy.

### CORS error persists:

1. Verify ALLOWED_ORIGINS in Render includes your new Vercel URL
2. Wait 30 seconds after saving
3. Hard refresh frontend (Ctrl+Shift+R)

---

## Automation Script

I'll create a script to automate the Vercel deployment.

---

## Next Steps After Fresh Deploy

1. ✅ Delete old Vercel projects
2. ✅ Create new Vercel project
3. ✅ Update CORS in Render
4. 🔲 Configure DATABASE_URL in Render
5. 🔲 Run migrations
6. 🔲 Create admin user
7. 🔲 Test login flow

---

**Action Required**:
1. Delete old Vercel projects
2. Create new one using Option A, B, or C above
3. Share the new Vercel URL so I can update CORS

---

**Files in this repo:**
- Frontend: `src/hrisa_code/web/static/`
- Backend: Already on Render (srv-d6l94ia4d50c73b542lg)
