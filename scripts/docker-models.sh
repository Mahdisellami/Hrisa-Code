#!/bin/bash
# List available Ollama models

set -e

echo "📋 Available Ollama models:"
echo ""

docker compose exec ollama ollama list
