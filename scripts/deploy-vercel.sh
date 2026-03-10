#!/bin/bash
# Vercel Fresh Deployment Script
# Automates deployment of frontend to Vercel

set -e

echo "=========================================="
echo "Vercel Fresh Deployment"
echo "=========================================="
echo ""

# Check if vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "⚠️  Vercel CLI not installed"
    echo ""
    echo "Install with:"
    echo "  npm install -g vercel"
    echo ""
    echo "Or deploy manually:"
    echo "  1. Go to: https://vercel.com/new"
    echo "  2. Import: Mahdisellami/Hrisa-Code"
    echo "  3. Root Directory: src/hrisa_code/web/static"
    echo "  4. Deploy"
    echo ""
    exit 1
fi

echo "✓ Vercel CLI found"
echo ""

# Check if logged in
echo "Checking Vercel authentication..."
if ! vercel whoami &> /dev/null; then
    echo "⚠️  Not logged in to Vercel"
    echo ""
    echo "Logging in..."
    vercel login
    echo ""
fi

echo "✓ Authenticated with Vercel"
echo ""

# Deploy from static directory
echo "Deploying frontend from src/hrisa_code/web/static..."
echo ""

cd src/hrisa_code/web/static

# Deploy to production
vercel --prod --yes

# Get the deployment URL
deployment_url=$(vercel ls --prod | grep "hrisa" | head -1 | awk '{print $2}')

if [ -z "$deployment_url" ]; then
    echo ""
    echo "⚠️  Could not detect deployment URL"
    echo ""
    echo "Check your Vercel dashboard:"
    echo "  → https://vercel.com/dashboard"
    echo ""
    exit 1
fi

echo ""
echo "=========================================="
echo "Deployment Successful!"
echo "=========================================="
echo ""
echo "Frontend URL: https://$deployment_url"
echo ""

# Go back to repo root
cd ../../../..

echo "=========================================="
echo "Next Steps"
echo "=========================================="
echo ""
echo "1. Update CORS in Render:"
echo "   → https://dashboard.render.com/web/srv-d6l94ia4d50c73b542lg"
echo "   → Environment tab"
echo "   → Set ALLOWED_ORIGINS to:"
echo "     https://hrisa-backend.onrender.com,https://$deployment_url"
echo ""
echo "2. Test your frontend:"
echo "   → https://$deployment_url"
echo ""
echo "3. Or update CORS automatically:"
echo "   export RENDER_API_KEY=rnd_your_key"
echo "   export NEW_FRONTEND_URL=https://$deployment_url"
echo "   ./scripts/update-cors.sh"
echo ""
