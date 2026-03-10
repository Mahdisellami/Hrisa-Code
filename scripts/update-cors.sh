#!/bin/bash
# Quick CORS Fix Script - Update ALLOWED_ORIGINS in Render
# Usage: RENDER_API_KEY=rnd_xxx NEW_FRONTEND_URL=https://your-app.vercel.app ./scripts/update-cors.sh

set -e

SERVICE_ID="${RENDER_SERVICE_ID:-srv-d6l94ia4d50c73b542lg}"
NEW_FRONTEND="${NEW_FRONTEND_URL:-https://hrisa-code-new.vercel.app}"
BACKEND="https://hrisa-backend.onrender.com"

echo "=========================================="
echo "CORS Configuration Update"
echo "=========================================="
echo ""
echo "Service ID: $SERVICE_ID"
echo "New frontend URL: $NEW_FRONTEND"
echo ""

if [ -z "$RENDER_API_KEY" ]; then
    echo "❌ ERROR: RENDER_API_KEY not set"
    echo ""
    echo "Get API key from: https://dashboard.render.com/u/settings#api-keys"
    echo ""
    echo "Then run:"
    echo "  export RENDER_API_KEY=rnd_your_key_here"
    echo "  ./scripts/update-cors.sh"
    echo ""
    echo "Or update manually in Render Dashboard:"
    echo "  → https://dashboard.render.com/web/$SERVICE_ID"
    echo "  → Environment tab"
    echo "  → Set ALLOWED_ORIGINS to: $BACKEND,$NEW_FRONTEND"
    exit 1
fi

echo "Updating ALLOWED_ORIGINS via Render API..."
echo ""

response=$(curl -s -w "\n%{http_code}" -X PUT \
  "https://api.render.com/v1/services/$SERVICE_ID/env-vars" \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d "[{\"key\": \"ALLOWED_ORIGINS\", \"value\": \"$BACKEND,$NEW_FRONTEND\"}]")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" == "200" ] || [ "$http_code" == "201" ]; then
    echo "✅ ALLOWED_ORIGINS updated successfully!"
    echo ""
    echo "New value: $BACKEND,$NEW_FRONTEND"
    echo ""
    echo "Render will automatically redeploy (takes ~30 seconds)"
    echo ""
    echo "After 30 seconds, test at: $NEW_FRONTEND"
else
    echo "❌ Failed to update (HTTP $http_code)"
    echo ""
    echo "Response: $body"
    echo ""
    echo "Try updating manually:"
    echo "  → https://dashboard.render.com/web/$SERVICE_ID"
    echo "  → Environment tab"
    exit 1
fi

echo "=========================================="
echo "Waiting for deployment... (30 seconds)"
echo "=========================================="
echo ""

sleep 30

echo "Testing CORS..."
echo ""

cors_test=$(curl -s -I -X OPTIONS "$BACKEND/api/auth/send-magic-link" \
  -H "Origin: $NEW_FRONTEND" \
  -H "Access-Control-Request-Method: POST" | grep -i "access-control-allow-origin" || echo "")

if [ ! -z "$cors_test" ]; then
    echo "✅ CORS is working!"
    echo "   $cors_test"
    echo ""
    echo "You can now test login at: $NEW_FRONTEND"
else
    echo "⚠️  CORS headers not detected yet"
    echo ""
    echo "Wait another minute and check manually:"
    echo "  → Visit: $NEW_FRONTEND"
    echo "  → Open browser console"
    echo "  → Try login - CORS error should be gone"
fi

echo ""
echo "=========================================="
echo "Next Steps"
echo "=========================================="
echo ""
echo "1. Visit: $NEW_FRONTEND"
echo "2. Test login (CORS should work now)"
echo "3. If backend returns 500 error:"
echo "   → Configure DATABASE_URL and other env vars"
echo "   → See: RENDER_AUTOMATION.md"
echo ""
