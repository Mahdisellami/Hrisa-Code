#!/bin/bash
# Pull Ollama models

set -e

echo "📥 Pulling Ollama models..."
echo ""

# Check if a specific model is requested
MODEL="${1:-codellama}"

echo "Pulling model: $MODEL"
docker compose exec ollama ollama pull "$MODEL"

echo ""
echo "✅ Model pulled successfully!"
echo ""
echo "Available models:"
docker compose exec ollama ollama list
