#!/bin/bash

# Deployment Status Dashboard
clear
echo "=========================================="
echo "  Hrisa Code - Deployment Status"
echo "=========================================="
echo ""
echo "Date: $(date)"
echo ""

# Check services
echo "📦 Docker Services:"
docker-compose ps --format "table {{.Name}}\t{{.Status}}" 2>/dev/null | grep -v "version" || echo "  Error checking services"
echo ""

# Check Web UI
echo "🌐 Web UI:"
if curl -s -f http://localhost:8000/api/stats > /dev/null 2>&1; then
    echo "  ✅ http://localhost:8000 - ACCESSIBLE"
    curl -s http://localhost:8000/api/stats | python3 -c "import sys, json; data=json.load(sys.stdin); print(f'  📊 Agents: {data[\"total_agents\"]} total, {data[\"running_agents\"]} running')"
else
    echo "  ❌ Web UI not accessible"
fi
echo ""

# Check Ollama
echo "🤖 Ollama Service:"
if curl -s -f http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "  ✅ http://localhost:11434 - ACCESSIBLE"
    MODEL_COUNT=$(curl -s http://localhost:11434/api/tags | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('models', [])))" 2>/dev/null)
    echo "  📚 Models available: $MODEL_COUNT"

    if [ "$MODEL_COUNT" -gt 0 ]; then
        echo ""
        echo "  Available models:"
        docker exec hrisa-ollama ollama list 2>/dev/null | tail -n +2 | awk '{printf "    - %s (%s)\n", $1, $2}'
    fi
else
    echo "  ❌ Ollama not accessible"
fi
echo ""

# Check model download progress
echo "📥 Model Download:"
if [ -f "/tmp/claude/tasks/be9e462.output" ]; then
    PROGRESS_LINE=$(tail -1 /tmp/claude/tasks/be9e462.output | grep 'pulling dde5aa3fc5ff')
    if [ -n "$PROGRESS_LINE" ]; then
        PERCENT=$(echo "$PROGRESS_LINE" | grep -o '[0-9]\+%' | head -1)
        SIZE=$(echo "$PROGRESS_LINE" | grep -o '[0-9]\+\.[0-9]\+ GB\|[0-9]\+ MB' | head -2 | tr '\n' '/' | sed 's/\/$//')
        SPEED=$(echo "$PROGRESS_LINE" | grep -o '[0-9]\+ KB/s\|[0-9]\+\.[0-9]\+ MB/s' | head -1)
        TIME=$(echo "$PROGRESS_LINE" | grep -o '[0-9]\+m[0-9]\+s' | tail -1)
        echo "  ⏳ llama3.2:latest: $PERCENT complete"
        echo "  📦 Size: $SIZE"
        echo "  ⚡ Speed: $SPEED"
        echo "  ⏰ ETA: $TIME"
    else
        echo "  ✅ No active downloads"
    fi
else
    echo "  ℹ️  No download tasks found"
fi
echo ""

# Check PDF support
echo "📄 PDF Support:"
if docker exec hrisa-web python3 -c "import pypdf" 2>/dev/null; then
    echo "  ✅ PDF libraries installed"
else
    echo "  ❌ PDF libraries not available"
fi
echo ""

echo "=========================================="
echo "  Commands:"
echo "=========================================="
echo "  ./deploy.sh status  - Check service status"
echo "  ./deploy.sh logs    - View service logs"
echo "  ./deploy.sh stop    - Stop all services"
echo "  ./deploy.sh restart - Restart services"
echo ""
echo "  Open Web UI: open http://localhost:8000"
echo "=========================================="
