#!/bin/bash
# Simple startup script for Hrisa Code Web UI

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Hrisa Code Web UI - Startup Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if Ollama is running
echo -e "${BLUE}[1/3] Checking Ollama...${NC}"
if ollama list &> /dev/null; then
    echo -e "${GREEN}✓ Ollama is running${NC}"
else
    echo -e "${RED}✗ Ollama is not running${NC}"
    echo ""
    echo "Please start Ollama first:"
    echo "  ollama serve"
    echo ""
    exit 1
fi

# Activate virtual environment
echo ""
echo -e "${BLUE}[2/3] Activating virtual environment...${NC}"
if [ -d "venv" ]; then
    source venv/bin/activate
    echo -e "${GREEN}✓ Virtual environment activated${NC}"
else
    echo -e "${RED}✗ Virtual environment not found${NC}"
    echo ""
    echo "Please create the virtual environment first:"
    echo "  python -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -e \".[web]\""
    echo ""
    exit 1
fi

# Start the web server
echo ""
echo -e "${BLUE}[3/3] Starting web server...${NC}"
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Web UI will be available at:${NC}"
echo -e "${GREEN}  http://localhost:8000${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start hrisa web
hrisa web
