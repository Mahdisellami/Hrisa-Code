#!/bin/bash
# Deployment Verification Script
# Checks that all deployment files are configured correctly

set -e

echo "🔍 Hrisa Code Deployment Verification"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

errors=0
warnings=0

# Check if files exist
echo "📁 Checking deployment files..."

files=(
    "vercel.json"
    "render.yaml"
    "docker/Dockerfile.ollama"
    "docker/entrypoint.sh"
    ".github/workflows/deploy.yml"
    "VERCEL_RENDER.md"
    "DEPLOYMENT_CHECKLIST.md"
    "DEPLOY_NOW.md"
    ".env.example"
    "PRODUCTION.md"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file exists"
    else
        echo -e "${RED}✗${NC} $file missing"
        ((errors++))
    fi
done

echo ""

# Check if entrypoint.sh is executable
echo "🔐 Checking file permissions..."
if [ -x "docker/entrypoint.sh" ]; then
    echo -e "${GREEN}✓${NC} docker/entrypoint.sh is executable"
else
    echo -e "${RED}✗${NC} docker/entrypoint.sh is not executable"
    echo "   Fix: chmod +x docker/entrypoint.sh"
    ((errors++))
fi

echo ""

# Check vercel.json syntax
echo "📋 Checking vercel.json..."
if command -v python3 &> /dev/null; then
    if python3 -c "import json; json.load(open('vercel.json'))" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} vercel.json is valid JSON"
    else
        echo -e "${RED}✗${NC} vercel.json has JSON syntax errors"
        ((errors++))
    fi
else
    echo -e "${YELLOW}⚠${NC} Python3 not found, skipping JSON validation"
    ((warnings++))
fi

echo ""

# Check render.yaml syntax
echo "📋 Checking render.yaml..."
if command -v python3 &> /dev/null; then
    if python3 -c "import yaml; yaml.safe_load(open('render.yaml'))" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} render.yaml is valid YAML"
    else
        echo -e "${RED}✗${NC} render.yaml has YAML syntax errors"
        ((errors++))
    fi
else
    echo -e "${YELLOW}⚠${NC} PyYAML not found, skipping YAML validation"
    ((warnings++))
fi

echo ""

# Check GitHub secrets reminder
echo "🔑 GitHub Secrets Checklist (add these to GitHub):"
secrets=(
    "VERCEL_TOKEN"
    "VERCEL_ORG_ID"
    "VERCEL_PROJECT_ID"
    "RENDER_DEPLOY_HOOK_URL"
    "SLACK_WEBHOOK_URL (optional)"
)

for secret in "${secrets[@]}"; do
    echo "   - $secret"
done

echo ""

# Check if git is configured
echo "🌳 Checking git status..."
if git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Git repository initialized"

    # Check if there are uncommitted changes
    if git diff-index --quiet HEAD -- 2>/dev/null; then
        echo -e "${GREEN}✓${NC} No uncommitted changes"
    else
        echo -e "${YELLOW}⚠${NC} You have uncommitted changes"
        echo "   Run: git add -A && git commit -m 'Your message'"
        ((warnings++))
    fi

    # Check if origin is set
    if git remote get-url origin > /dev/null 2>&1; then
        origin=$(git remote get-url origin)
        echo -e "${GREEN}✓${NC} Git origin configured: $origin"
    else
        echo -e "${RED}✗${NC} Git origin not configured"
        echo "   Add remote: git remote add origin https://github.com/yourusername/hrisa-code.git"
        ((errors++))
    fi

    # Check if pushed to remote
    LOCAL=$(git rev-parse @ 2>/dev/null || echo "")
    REMOTE=$(git rev-parse @{u} 2>/dev/null || echo "")

    if [ "$LOCAL" != "$REMOTE" ]; then
        echo -e "${YELLOW}⚠${NC} Local commits not pushed to remote"
        echo "   Run: git push origin main"
        ((warnings++))
    else
        echo -e "${GREEN}✓${NC} All commits pushed to remote"
    fi
else
    echo -e "${RED}✗${NC} Not a git repository"
    ((errors++))
fi

echo ""

# Check SSH keys
echo "🔐 Checking SSH keys for GitHub..."
if [ -f ~/.ssh/id_ed25519.pub ] || [ -f ~/.ssh/id_rsa.pub ]; then
    echo -e "${GREEN}✓${NC} SSH key found"

    # Test GitHub connection
    if ssh -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
        echo -e "${GREEN}✓${NC} GitHub SSH authentication working"
    else
        echo -e "${YELLOW}⚠${NC} GitHub SSH authentication not confirmed"
        echo "   Test: ssh -T git@github.com"
        ((warnings++))
    fi
else
    echo -e "${RED}✗${NC} No SSH key found"
    echo "   Generate: ssh-keygen -t ed25519 -C 'your.email@example.com'"
    echo "   Add to GitHub: cat ~/.ssh/id_ed25519.pub"
    ((errors++))
fi

echo ""

# Check if Ollama is running locally (for testing)
echo "🦙 Checking local Ollama (for testing)..."
if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✓${NC} Ollama installed"

    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Ollama service running"

        # Check if required model is pulled
        if ollama list | grep -q "qwen2.5-coder"; then
            echo -e "${GREEN}✓${NC} qwen2.5-coder model available"
        else
            echo -e "${YELLOW}⚠${NC} qwen2.5-coder model not pulled"
            echo "   Pull: ollama pull qwen2.5-coder:7b"
            ((warnings++))
        fi
    else
        echo -e "${YELLOW}⚠${NC} Ollama service not running"
        echo "   Start: ollama serve"
        ((warnings++))
    fi
else
    echo -e "${YELLOW}⚠${NC} Ollama not installed (not required for deployment)"
    echo "   Install: https://ollama.ai"
fi

echo ""

# Check Python dependencies
echo "🐍 Checking Python environment..."
if command -v python3 &> /dev/null; then
    python_version=$(python3 --version | awk '{print $2}')
    echo -e "${GREEN}✓${NC} Python $python_version installed"

    # Check if in virtual environment
    if [[ "$VIRTUAL_ENV" != "" ]]; then
        echo -e "${GREEN}✓${NC} Virtual environment active: $VIRTUAL_ENV"
    else
        echo -e "${YELLOW}⚠${NC} No virtual environment active"
        echo "   Create: python3 -m venv venv"
        echo "   Activate: source venv/bin/activate"
        ((warnings++))
    fi

    # Check if hrisa is installed
    if python3 -c "import hrisa_code" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} hrisa-code package installed"
    else
        echo -e "${YELLOW}⚠${NC} hrisa-code package not installed"
        echo "   Install: pip install -e '.[web]'"
        ((warnings++))
    fi
else
    echo -e "${RED}✗${NC} Python3 not found"
    ((errors++))
fi

echo ""

# Check tests pass
echo "🧪 Checking tests..."
if command -v pytest &> /dev/null; then
    echo "Running tests..."
    if pytest tests/ -q --tb=no > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} All tests passing"
    else
        echo -e "${RED}✗${NC} Some tests failing"
        echo "   Run: pytest tests/ -v"
        ((errors++))
    fi
else
    echo -e "${YELLOW}⚠${NC} pytest not installed"
    echo "   Install: pip install -e '.[dev]'"
    ((warnings++))
fi

echo ""
echo "======================================"
echo "📊 Summary"
echo "======================================"

if [ $errors -eq 0 ] && [ $warnings -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! Ready to deploy.${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Push to GitHub: git push origin main"
    echo "2. Follow DEPLOY_NOW.md for deployment"
    exit 0
elif [ $errors -eq 0 ]; then
    echo -e "${YELLOW}⚠ $warnings warning(s) found${NC}"
    echo "Deployment possible but some optional items need attention."
    echo ""
    echo "Review warnings above and proceed with deployment if acceptable."
    exit 0
else
    echo -e "${RED}✗ $errors error(s) found, $warnings warning(s)${NC}"
    echo "Fix errors before deploying."
    exit 1
fi
