#!/bin/bash
# Docker entrypoint script with verification for Hrisa Code

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Hrisa Code - Docker Startup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if running verification check
if [ "$1" = "check" ]; then
    echo -e "${BLUE}Running verification checks...${NC}"
    hrisa check
    exit 0
fi

# Wait for Ollama to be available if OLLAMA_HOST is set
if [ -n "$OLLAMA_HOST" ]; then
    echo -e "${BLUE}[1/3] Waiting for Ollama service...${NC}"

    MAX_WAIT=60
    WAITED=0
    OLLAMA_URL="${OLLAMA_HOST}/api/tags"

    while [ $WAITED -lt $MAX_WAIT ]; do
        if curl -s "$OLLAMA_URL" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Ollama service is ready${NC}"
            break
        fi
        echo -e "${YELLOW}Waiting for Ollama... (${WAITED}s/${MAX_WAIT}s)${NC}"
        sleep 5
        WAITED=$((WAITED + 5))
    done

    if [ $WAITED -ge $MAX_WAIT ]; then
        echo -e "${RED}✗ Timeout waiting for Ollama service${NC}"
        exit 1
    fi
fi

# Check for required models
echo ""
echo -e "${BLUE}[2/3] Checking for required models...${NC}"

if [ -n "$REQUIRED_MODELS" ]; then
    IFS=',' read -ra MODELS <<< "$REQUIRED_MODELS"

    MISSING_MODELS=()
    for model in "${MODELS[@]}"; do
        model=$(echo "$model" | xargs)  # trim whitespace
        if ! curl -s "${OLLAMA_HOST}/api/show" -d "{\"name\":\"$model\"}" 2>/dev/null | grep -q "model"; then
            MISSING_MODELS+=("$model")
        fi
    done

    if [ ${#MISSING_MODELS[@]} -gt 0 ]; then
        echo -e "${YELLOW}⚠ Missing models: ${MISSING_MODELS[*]}${NC}"
        echo -e "${YELLOW}Models can be pulled using: docker exec <container> ollama pull <model>${NC}"

        if [ "$AUTO_PULL_MODELS" = "true" ]; then
            echo -e "${BLUE}AUTO_PULL_MODELS=true, pulling models...${NC}"
            for model in "${MISSING_MODELS[@]}"; do
                echo -e "${BLUE}Pulling $model...${NC}"
                if curl -s -X POST "${OLLAMA_HOST}/api/pull" -d "{\"name\":\"$model\"}" | grep -q "success"; then
                    echo -e "${GREEN}✓ Pulled $model${NC}"
                else
                    echo -e "${RED}✗ Failed to pull $model${NC}"
                fi
            done
        fi
    else
        echo -e "${GREEN}✓ All required models are available${NC}"
    fi
else
    echo -e "${YELLOW}⚠ No REQUIRED_MODELS specified, skipping model check${NC}"
fi

# Run verification if requested
echo ""
echo -e "${BLUE}[3/3] Running pre-flight checks...${NC}"

if [ "$SKIP_VERIFICATION" != "true" ]; then
    if hrisa check 2>/dev/null; then
        echo -e "${GREEN}✓ Verification passed${NC}"
    else
        echo -e "${YELLOW}⚠ Some verification checks failed (non-critical)${NC}"
    fi
else
    echo -e "${YELLOW}○ Verification skipped (SKIP_VERIFICATION=true)${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Hrisa Code Ready!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Execute the main command
exec "$@"
