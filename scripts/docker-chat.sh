#!/bin/bash
# Start interactive chat session with Hrisa Code

set -e

# Get model name from argument or use default
MODEL="${1:-codellama}"

echo "💬 Starting Hrisa Code chat with model: $MODEL"
echo ""

# Make sure workspace directory exists
mkdir -p workspace

# Run interactive chat
docker compose run --rm \
    -v "$(pwd)/workspace:/workspace" \
    hrisa hrisa chat --model "$MODEL"
