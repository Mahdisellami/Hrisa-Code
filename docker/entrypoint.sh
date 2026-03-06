#!/bin/bash
set -e

# Start Ollama service in background
/bin/ollama serve &

# Wait for Ollama to start
echo "Waiting for Ollama to start..."
until curl -s http://localhost:11434/api/tags > /dev/null 2>&1; do
  echo "Still waiting for Ollama..."
  sleep 2
done

echo "Ollama is running!"

# Pull models if specified
if [ -n "$OLLAMA_MODELS" ]; then
  IFS=',' read -ra MODELS <<< "$OLLAMA_MODELS"
  for model in "${MODELS[@]}"; do
    echo "Pulling model: $model"
    /bin/ollama pull "$model"
  done
fi

echo "Setup complete! Ollama is ready."

# Keep container running
wait
