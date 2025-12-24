#!/bin/bash
# Start Hrisa Code with Docker Compose

set -e

echo "🚀 Starting Hrisa Code services..."
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running"
    echo "Please start Docker Desktop and try again"
    exit 1
fi

# Create workspace directory if it doesn't exist
mkdir -p workspace

# Start Ollama service
echo "📦 Starting Ollama service..."
docker compose up -d ollama

# Wait for Ollama to be healthy
echo "⏳ Waiting for Ollama to be ready..."
timeout=60
counter=0
until docker compose exec ollama ollama list > /dev/null 2>&1; do
    sleep 2
    counter=$((counter + 2))
    if [ $counter -ge $timeout ]; then
        echo "❌ Timeout waiting for Ollama to start"
        exit 1
    fi
done

echo "✅ Ollama is ready!"
echo ""
echo "📋 Next steps:"
echo "  1. Pull models: ./scripts/docker-pull-models.sh"
echo "  2. Start chat:  ./scripts/docker-chat.sh"
echo "  3. List models: ./scripts/docker-models.sh"
echo ""
echo "Or use docker compose commands directly:"
echo "  docker compose --profile setup run --rm ollama-pull"
echo "  docker compose run --rm hrisa hrisa chat"
