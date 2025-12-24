#!/bin/bash
# Stop Hrisa Code services

set -e

echo "🛑 Stopping Hrisa Code services..."

docker compose down

echo "✅ Services stopped"
echo ""
echo "Note: Volumes (models, config, history) are preserved"
echo "To remove volumes, run: docker compose down -v"
