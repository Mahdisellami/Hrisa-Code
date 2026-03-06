#!/bin/bash

# Monitor model download progress
echo "Monitoring llama3.2:latest download..."
echo "Started at: $(date)"
echo ""

while true; do
    # Check if model is available
    if docker exec hrisa-ollama ollama list 2>/dev/null | grep -q "llama3.2:latest"; then
        echo ""
        echo "=========================================="
        echo "✓ MODEL DOWNLOAD COMPLETE!"
        echo "=========================================="
        echo "Completed at: $(date)"
        echo ""
        docker exec hrisa-ollama ollama list
        echo ""
        echo "You can now create agents in the Web UI at http://localhost:8000"
        exit 0
    fi

    # Show current progress from download task output
    if [ -f "/tmp/claude/tasks/be9e462.output" ]; then
        PROGRESS=$(tail -1 /tmp/claude/tasks/be9e462.output | grep -o '[0-9]\+%' | head -1)
        if [ -n "$PROGRESS" ]; then
            echo "[$(date +%H:%M:%S)] Download progress: $PROGRESS"
        fi
    fi

    sleep 60
done
