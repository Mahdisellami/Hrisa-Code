#!/bin/bash
# Render Shell Setup Script
# Run this in Render Shell after deployment
#
# INSTRUCTIONS:
# 1. Go to Render Dashboard → Your Service → Shell → Launch Shell
# 2. Copy and paste this entire script
# 3. Replace YOUR_ADMIN_EMAIL with your email address
#

set -e

echo "=========================================="
echo "Hrisa Code - Render Shell Setup"
echo "=========================================="
echo ""

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL not set in environment variables"
    echo "   → Go to Render Dashboard → Environment tab and add DATABASE_URL"
    exit 1
fi

echo "✓ DATABASE_URL is configured"
echo ""

# Check if alembic is installed
if ! command -v alembic &> /dev/null; then
    echo "❌ ERROR: Alembic not installed"
    echo "   → Run: pip install -e \".[web]\""
    exit 1
fi

echo "✓ Alembic is installed"
echo ""

# Run migrations
echo "Step 1: Running database migrations..."
alembic upgrade head

if [ $? -eq 0 ]; then
    echo "✓ Migrations completed successfully"
else
    echo "❌ Migration failed"
    exit 1
fi

echo ""

# Verify tables were created
echo "Step 2: Verifying database tables..."
python3 << 'EOF'
import os
import sys

try:
    import psycopg2

    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    cur = conn.cursor()
    cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")
    tables = [row[0] for row in cur.fetchall()]

    expected_tables = ['users', 'magic_link_tokens', 'sessions', 'agents', 'teams', 'audit_logs', 'alembic_version']
    missing_tables = [t for t in expected_tables if t not in tables]

    if missing_tables:
        print(f"❌ Missing tables: {', '.join(missing_tables)}")
        sys.exit(1)
    else:
        print(f"✓ All tables created: {', '.join(tables)}")

    cur.close()
    conn.close()
except Exception as e:
    print(f"❌ Error checking tables: {e}")
    sys.exit(1)
EOF

if [ $? -ne 0 ]; then
    exit 1
fi

echo ""

# Create admin user
echo "Step 3: Creating admin user..."
echo ""
echo "⚠️  IMPORTANT: Replace 'YOUR_ADMIN_EMAIL' below with your actual email"
echo ""
echo "Run this command manually:"
echo "----------------------------------------"
echo "python scripts/create_admin.py YOUR_ADMIN_EMAIL"
echo "----------------------------------------"
echo ""
echo "Example:"
echo "python scripts/create_admin.py admin@yourdomain.com"
echo ""
echo "=========================================="
echo "Setup Complete! ✓"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Create admin user with command above"
echo "2. Test login at: https://hrisa-mywebsite.vercel.app"
echo "3. Check your email for magic link"
echo ""
