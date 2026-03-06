#!/bin/bash
# Deployment Monitoring Script for Render
# Checks backend health, database connectivity, and auth endpoints

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKEND_URL="${BACKEND_URL:-https://hrisa-backend.onrender.com}"
FRONTEND_URL="${FRONTEND_URL:-https://hrisa-mywebsite.vercel.app}"

echo "=========================================="
echo "Hrisa Code Deployment Monitor"
echo "=========================================="
echo ""
echo "Backend:  $BACKEND_URL"
echo "Frontend: $FRONTEND_URL"
echo ""

# Function to check HTTP endpoint
check_endpoint() {
    local url=$1
    local name=$2
    local expected_status=${3:-200}

    echo -n "Checking $name... "

    http_code=$(curl -s -o /dev/null -w "%{http_code}" "$url" --max-time 10 || echo "000")

    if [ "$http_code" == "$expected_status" ]; then
        echo -e "${GREEN}✓ OK${NC} (HTTP $http_code)"
        return 0
    elif [ "$http_code" == "000" ]; then
        echo -e "${RED}✗ TIMEOUT${NC} (connection failed)"
        return 1
    else
        echo -e "${YELLOW}⚠ Unexpected${NC} (HTTP $http_code, expected $expected_status)"
        return 1
    fi
}

# Function to check JSON endpoint
check_json_endpoint() {
    local url=$1
    local name=$2
    local expected_key=$3

    echo -n "Checking $name... "

    response=$(curl -s "$url" --max-time 10 || echo "")

    if [ -z "$response" ]; then
        echo -e "${RED}✗ No response${NC}"
        return 1
    fi

    if echo "$response" | grep -q "\"$expected_key\""; then
        echo -e "${GREEN}✓ OK${NC}"
        echo "  Response: $(echo "$response" | head -c 100)..."
        return 0
    else
        echo -e "${RED}✗ Missing key '$expected_key'${NC}"
        echo "  Response: $response"
        return 1
    fi
}

# Function to get deployment status from Render API
check_render_status() {
    if [ -z "$RENDER_API_KEY" ]; then
        echo -e "${YELLOW}⚠ RENDER_API_KEY not set - skipping Render API checks${NC}"
        return 0
    fi

    local service_id="${RENDER_SERVICE_ID:-srv-d6l94ia4d50c73b542lg}"

    echo "Fetching Render deployment status..."

    response=$(curl -s -H "Authorization: Bearer $RENDER_API_KEY" \
        "https://api.render.com/v1/services/$service_id" || echo "")

    if [ -z "$response" ]; then
        echo -e "${RED}✗ Failed to fetch Render status${NC}"
        return 1
    fi

    # Parse deploy status (basic grep since we don't have jq)
    if echo "$response" | grep -q '"suspended":true'; then
        echo -e "${YELLOW}⚠ Service is SUSPENDED${NC}"
    elif echo "$response" | grep -q '"state":"live"'; then
        echo -e "${GREEN}✓ Service is LIVE${NC}"
    else
        echo -e "${YELLOW}⚠ Service state unknown${NC}"
    fi
}

echo "=========================================="
echo "1. Backend Health Checks"
echo "=========================================="
echo ""

# Check basic endpoints
check_endpoint "$BACKEND_URL/api/stats" "Stats endpoint"
check_endpoint "$BACKEND_URL/favicon.ico" "Favicon" "200"

echo ""
echo "=========================================="
echo "2. Authentication Endpoints"
echo "=========================================="
echo ""

# Check auth endpoints (expect 405 for GET on POST endpoint, or 422 for missing body)
check_endpoint "$BACKEND_URL/api/auth/send-magic-link" "Magic link endpoint" "422"
check_endpoint "$BACKEND_URL/api/auth/me" "Auth me endpoint" "401"

# Try to get users list (should fail with 401)
echo -n "Checking admin users endpoint (should require auth)... "
http_code=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/api/auth/users" --max-time 10)
if [ "$http_code" == "401" ]; then
    echo -e "${GREEN}✓ OK${NC} (401 Unauthorized - auth is working)"
else
    echo -e "${YELLOW}⚠ Unexpected${NC} (HTTP $http_code)"
fi

echo ""
echo "=========================================="
echo "3. Frontend Checks"
echo "=========================================="
echo ""

check_endpoint "$FRONTEND_URL" "Frontend homepage"

echo ""
echo "=========================================="
echo "4. Database Check (via API)"
echo "=========================================="
echo ""

# Check if stats endpoint returns data (implies app is running)
echo -n "Testing database connectivity... "
stats_response=$(curl -s "$BACKEND_URL/api/stats" --max-time 10 || echo "")
if echo "$stats_response" | grep -q "total_agents"; then
    echo -e "${GREEN}✓ App is running${NC}"

    # Check if DATABASE_URL is configured (look for auth endpoints working)
    echo -n "Checking if authentication is enabled... "
    auth_check=$(curl -s "$BACKEND_URL/api/auth/me" --max-time 10 || echo "")
    if echo "$auth_check" | grep -q "detail"; then
        echo -e "${GREEN}✓ Authentication is active${NC}"
        echo "  (401 error confirms auth middleware is running)"
    else
        echo -e "${YELLOW}⚠ Authentication may not be configured${NC}"
        echo "  DATABASE_URL might not be set in Render environment"
    fi
else
    echo -e "${RED}✗ Stats endpoint not responding correctly${NC}"
fi

echo ""
echo "=========================================="
echo "5. Render Service Status"
echo "=========================================="
echo ""

check_render_status

echo ""
echo "=========================================="
echo "6. Recent Logs (Last 10 lines)"
echo "=========================================="
echo ""

if [ ! -z "$RENDER_API_KEY" ] && [ ! -z "$RENDER_SERVICE_ID" ]; then
    echo "Fetching recent logs from Render..."
    curl -s -H "Authorization: Bearer $RENDER_API_KEY" \
        "https://api.render.com/v1/services/${RENDER_SERVICE_ID}/logs?limit=10" | \
        grep -o '"text":"[^"]*"' | sed 's/"text":"//; s/"$//' || echo "Failed to fetch logs"
else
    echo -e "${YELLOW}Set RENDER_API_KEY and RENDER_SERVICE_ID to fetch logs${NC}"
    echo ""
    echo "To check logs manually:"
    echo "  → https://dashboard.render.com/web/srv-d6l94ia4d50c73b542lg/logs"
fi

echo ""
echo "=========================================="
echo "Summary"
echo "=========================================="
echo ""

# Test all critical endpoints
backend_ok=0
frontend_ok=0
auth_ok=0

curl -s "$BACKEND_URL/api/stats" --max-time 5 > /dev/null 2>&1 && backend_ok=1
curl -s "$FRONTEND_URL" --max-time 5 > /dev/null 2>&1 && frontend_ok=1
curl -s "$BACKEND_URL/api/auth/me" --max-time 5 | grep -q "detail" && auth_ok=1

if [ $backend_ok -eq 1 ] && [ $frontend_ok -eq 1 ] && [ $auth_ok -eq 1 ]; then
    echo -e "${GREEN}✓ All systems operational!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Configure environment variables (DATABASE_URL, SMTP_*)"
    echo "  2. Run migrations: alembic upgrade head"
    echo "  3. Create admin user: python scripts/create_admin.py admin@yourdomain.com"
    echo "  4. Test login at: $FRONTEND_URL"
elif [ $backend_ok -eq 1 ]; then
    echo -e "${YELLOW}⚠ Backend is running but auth needs configuration${NC}"
    echo ""
    echo "See: RENDER_AUTOMATION.md for setup instructions"
else
    echo -e "${RED}✗ Backend is not responding correctly${NC}"
    echo ""
    echo "Check Render logs:"
    echo "  → https://dashboard.render.com/web/srv-d6l94ia4d50c73b542lg/logs"
fi

echo ""
