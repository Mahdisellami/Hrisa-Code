#!/bin/bash
# Clean up Docker resources

set -e

echo "🧹 Cleaning up Hrisa Code Docker resources..."
echo ""
echo "⚠️  WARNING: This will remove:"
echo "  - All containers"
echo "  - All volumes (including downloaded models)"
echo "  - Network"
echo ""
read -p "Are you sure? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled"
    exit 0
fi

docker compose down -v --remove-orphans

echo ""
echo "✅ Cleanup complete"
