#!/bin/bash
# Run database migrations

set -e

# Check if .env file exists
if [ -f .env ]; then
    echo "Loading environment from .env file..."
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "Error: DATABASE_URL environment variable not set"
    echo "Please create a .env file with DATABASE_URL or export it manually"
    exit 1
fi

# Run migrations using alembic directly
echo "Running database migrations..."
alembic upgrade head

echo "✓ Migrations completed successfully!"
