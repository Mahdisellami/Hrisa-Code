# Authentication System Testing Guide

This guide provides comprehensive instructions for testing the RBAC + Magic Link authentication system end-to-end.

## Prerequisites

- Python 3.10+
- Docker and Docker Compose (for PostgreSQL)
- SMTP credentials (Gmail app password recommended)
- PostgreSQL (via Docker or local installation)

## Setup

### 1. Install Dependencies

```bash
# Install with web dependencies
pip install -e ".[web]"
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
nano .env
```

**Required environment variables:**

```env
# Database
DATABASE_URL=postgresql://hrisa:hrisa_password@localhost:5432/hrisa

# SMTP (Gmail example)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password
SMTP_FROM_EMAIL=noreply@hrisa.local

# Application
APP_BASE_URL=http://localhost:8000
SECRET_KEY=generate-with-openssl-rand-hex-32
ALLOWED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
```

**Generate SECRET_KEY:**
```bash
openssl rand -hex 32
```

**Setup Gmail App Password:**
1. Enable 2FA on your Gmail account
2. Go to https://myaccount.google.com/apppasswords
3. Generate an app password for "Mail"
4. Use this password in SMTP_PASSWORD

### 3. Start PostgreSQL

**Option A: Docker Compose (Recommended)**
```bash
docker-compose up -d postgres
```

**Option B: Local PostgreSQL**
```bash
# MacOS
brew install postgresql
brew services start postgresql

# Linux
sudo apt-get install postgresql
sudo service postgresql start

# Create database
createdb hrisa
```

### 4. Run Database Migrations

```bash
# Using Alembic directly
alembic upgrade head

# OR using migration script
./scripts/migrate.sh

# OR using Python script
python scripts/run_migrations.py
```

**Verify migration:**
```bash
# Check if tables were created
docker exec -it hrisa-postgres psql -U hrisa -d hrisa -c "\dt"
```

You should see 6 tables:
- users
- magic_link_tokens
- sessions
- agents
- teams
- audit_logs

### 5. Start the Web Server

```bash
# Development mode
uvicorn hrisa_code.web.server:app --reload --host 0.0.0.0 --port 8000

# OR with Docker Compose
docker-compose up web
```

## Test Scenarios

### Test 1: First User Registration (Auto-Admin)

**Objective:** Verify that the first user automatically becomes an admin.

1. Open browser to `http://localhost:8000`
2. You should see the login page (purple gradient background)
3. Enter an email address (e.g., `admin@test.com`)
4. Click "Send Magic Link"
5. You should see "Check Your Email" success screen
6. Check your email inbox for magic link
7. Click the link in the email
8. You should be redirected to the dashboard
9. Verify user profile dropdown shows:
   - Email: admin@test.com
   - Role badge: ADMIN (white background)
   - "Admin Panel" menu item visible

**Expected Results:**
- ✅ Login page displayed on first visit
- ✅ Magic link email received within 30 seconds
- ✅ Magic link redirects to dashboard with session token
- ✅ User profile shows correct email and "admin" role
- ✅ Admin Panel button visible in dropdown

**Verify in Database:**
```sql
docker exec -it hrisa-postgres psql -U hrisa -d hrisa -c "SELECT email, role, is_active, created_at FROM users;"
```

### Test 2: Magic Link Security

**Objective:** Verify magic link security features.

#### Test 2.1: Single-Use Token
1. Log out from the dashboard
2. Request a new magic link
3. Copy the magic link URL from email
4. Click the link (should work - redirects to dashboard)
5. Log out again
6. Try clicking the same magic link URL again
7. **Expected:** Redirect to login with error (token already used)

#### Test 2.2: Token Expiration
1. Request a new magic link
2. Wait 16+ minutes (tokens expire after 15 minutes)
3. Try clicking the expired link
4. **Expected:** Redirect to login with error (token expired)

#### Test 2.3: Token Format Validation
1. Manually craft an invalid token URL: `http://localhost:8000/auth/verify?token=invalid`
2. Visit the URL
3. **Expected:** Redirect to login with error (invalid token)

**Verify in Database:**
```sql
-- Check magic link tokens
docker exec -it hrisa-postgres psql -U hrisa -d hrisa -c "SELECT token, used, used_at, expires_at FROM magic_link_tokens ORDER BY created_at DESC LIMIT 5;"
```

### Test 3: Session Management

**Objective:** Verify 30-day session persistence and token refresh.

#### Test 3.1: Session Persistence
1. Log in successfully
2. Refresh the browser page
3. **Expected:** Still logged in (no redirect to login)
4. Close browser completely
5. Reopen browser and visit `http://localhost:8000`
6. **Expected:** Still logged in

#### Test 3.2: Session Token in LocalStorage
1. Open browser DevTools (F12)
2. Go to Application → Local Storage → http://localhost:8000
3. Verify `hrisa_auth_token` key exists
4. Copy the token value
5. Make API request with token:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN_HERE" http://localhost:8000/api/auth/me
```
6. **Expected:** Returns user info JSON

#### Test 3.3: Logout
1. Click user profile dropdown
2. Click "Logout"
3. **Expected:** Redirected to login page
4. Check LocalStorage - `hrisa_auth_token` should be removed
5. Try accessing `http://localhost:8000` again
6. **Expected:** Login page shown

**Verify in Database:**
```sql
-- Check active sessions
docker exec -it hrisa-postgres psql -U hrisa -d hrisa -c "SELECT user_id, expires_at, last_accessed, created_at FROM sessions;"
```

### Test 4: Multiple Users and Roles

**Objective:** Verify different role permissions.

#### Test 4.1: Create Regular User
1. Log in as admin
2. Open Admin Panel from user dropdown
3. Note total user count (should be 1)
4. Open a different browser (or incognito window)
5. Go to `http://localhost:8000`
6. Register with different email: `user@test.com`
7. Log in via magic link
8. **Expected:** User profile shows "USER" role (not "ADMIN")
9. Verify "Admin Panel" button NOT visible in dropdown

#### Test 4.2: Create Viewer
1. In admin browser, open Admin Panel
2. Note: New user `user@test.com` appears in table with role "user"
3. Change role dropdown to "viewer"
4. Refresh the user browser
5. **Expected:** User profile now shows "VIEWER" role

### Test 5: Admin Panel Functionality

**Objective:** Test user management features (admin only).

#### Test 5.1: View All Users
1. Log in as admin
2. Click Admin Panel
3. Verify you see all users in table with:
   - Email
   - Role (badge)
   - Status (Active/Inactive)
   - Created date
   - Last login
   - Actions (role dropdown + deactivate button)
4. Stats at top show correct counts

#### Test 5.2: Change User Role
1. Select a user (not yourself)
2. Change role dropdown (e.g., user → admin)
3. **Expected:** Toast notification "User role updated to admin"
4. Verify role badge updates immediately
5. Refresh page - role persists

#### Test 5.3: Deactivate User
1. Click "Deactivate" button for a user
2. **Expected:** Toast notification "User deactivated successfully"
3. Status badge changes to "Inactive" (red)
4. Role dropdown becomes disabled
5. Have that user try to log in
6. **Expected:** Magic link works, but after clicking it shows error (inactive account)

#### Test 5.4: Reactivate User
1. In admin panel, click "Activate" button for inactive user
2. **Expected:** Toast notification "User activated successfully"
3. Status badge changes to "Active" (green)
4. User can now log in successfully

### Test 6: RBAC Permissions

**Objective:** Verify role-based access control on API endpoints.

#### Test 6.1: Admin Access
1. Log in as admin
2. Open browser DevTools → Network tab
3. Navigate through the application
4. All API calls should succeed (200 status)

#### Test 6.2: Regular User Access
1. Log in as regular user (not admin)
2. Try to access admin panel
3. **Expected:** "Admin access required" error
4. Try direct API call:
```bash
curl -H "Authorization: Bearer USER_TOKEN" http://localhost:8000/api/auth/users
```
5. **Expected:** 403 Forbidden

#### Test 6.3: Unauthenticated Access
1. Log out (or use curl without token)
2. Try API call:
```bash
curl http://localhost:8000/api/agents
```
3. **Expected:** 401 Unauthorized

### Test 7: Audit Logging

**Objective:** Verify all actions are logged.

**Check audit logs in database:**
```sql
docker exec -it hrisa-postgres psql -U hrisa -d hrisa -c "
SELECT
    u.email,
    al.action,
    al.resource_type,
    al.resource_id,
    al.details,
    al.created_at
FROM audit_logs al
LEFT JOIN users u ON al.user_id = u.id
ORDER BY al.created_at DESC
LIMIT 20;
"
```

**Expected log entries:**
- `auth.magic_link_sent` - When magic link requested
- `auth.login` - When user logs in
- `auth.logout` - When user logs out
- `user.role_update` - When admin changes user role
- `user.deactivated` - When admin deactivates user

### Test 8: Error Handling

**Objective:** Verify graceful error handling.

#### Test 8.1: Invalid Email Format
1. On login page, enter invalid email (e.g., "notanemail")
2. Try to submit
3. **Expected:** Browser validation prevents submission

#### Test 8.2: SMTP Failure
1. Stop SMTP or use wrong credentials
2. Try to send magic link
3. **Expected:** Toast error "Failed to send email"

#### Test 8.3: Database Failure
1. Stop PostgreSQL:
```bash
docker-compose stop postgres
```
2. Try to send magic link
3. **Expected:** Error shown (not crash)
4. Restart PostgreSQL:
```bash
docker-compose start postgres
```

#### Test 8.4: Network Failure
1. Disconnect network
2. Try any action
3. **Expected:** Graceful error message

### Test 9: Cross-Browser Compatibility

**Objective:** Verify authentication works across browsers.

Test in:
- Chrome/Chromium
- Firefox
- Safari (macOS)
- Edge (Windows)

**For each browser:**
1. Log in successfully
2. Verify UI renders correctly
3. Verify dropdown works
4. Verify logout works

## Test Checklist

- [ ] First user becomes admin automatically
- [ ] Magic link email received successfully
- [ ] Magic link works and creates session
- [ ] Magic link is single-use only
- [ ] Magic link expires after 15 minutes
- [ ] Session persists for 30 days
- [ ] Session stored in localStorage
- [ ] Logout clears session
- [ ] Multiple users can register
- [ ] Admin panel visible only to admins
- [ ] Admin can view all users
- [ ] Admin can change user roles
- [ ] Admin can deactivate/activate users
- [ ] Regular users cannot access admin features
- [ ] Unauthenticated users redirected to login
- [ ] All actions logged in audit_logs table
- [ ] Error messages displayed for failures
- [ ] UI works in all major browsers

## Troubleshooting

### Database Migration Fails
```bash
# Reset database (WARNING: Deletes all data)
docker exec -it hrisa-postgres psql -U hrisa -d hrisa -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# Run migrations again
alembic upgrade head
```

### Magic Link Not Received
1. Check SMTP credentials in .env
2. Check spam/junk folder
3. Test SMTP connection:
```python
import aiosmtplib
import os
from email.message import EmailMessage

async def test_smtp():
    msg = EmailMessage()
    msg['From'] = os.getenv('SMTP_FROM_EMAIL')
    msg['To'] = 'your-email@example.com'
    msg['Subject'] = 'Test'
    msg.set_content('Test email')

    await aiosmtplib.send(
        msg,
        hostname=os.getenv('SMTP_HOST'),
        port=int(os.getenv('SMTP_PORT')),
        username=os.getenv('SMTP_USER'),
        password=os.getenv('SMTP_PASSWORD'),
        start_tls=True
    )

import asyncio
asyncio.run(test_smtp())
```

### Token Invalid Error
1. Check DATABASE_URL is correct
2. Verify PostgreSQL is running
3. Check server logs for errors
4. Clear browser cache and localStorage

### 401 Unauthorized on API Calls
1. Check if token exists in localStorage
2. Verify token hasn't expired
3. Try logging out and back in

## Success Criteria

All tests pass when:
- ✅ Users can register and log in via magic link
- ✅ First user is automatically an admin
- ✅ Sessions persist for 30 days
- ✅ Admin panel works for role management
- ✅ Non-admins cannot access admin features
- ✅ All actions are audit logged
- ✅ System gracefully handles errors
- ✅ Works across all major browsers
