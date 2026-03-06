#!/usr/bin/env python3
"""Run Alembic database migrations."""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from alembic import command
from alembic.config import Config as AlembicConfig


def run_migrations():
    """Run database migrations using Alembic."""
    # Check if DATABASE_URL is set
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("Error: DATABASE_URL environment variable not set")
        print("Please set DATABASE_URL to your PostgreSQL connection string")
        print("Example: export DATABASE_URL='postgresql://user:pass@localhost:5432/dbname'")
        sys.exit(1)

    print(f"Running migrations with database: {database_url.split('@')[1] if '@' in database_url else database_url}")

    # Create Alembic config
    alembic_ini = project_root / "alembic.ini"
    if not alembic_ini.exists():
        print(f"Error: alembic.ini not found at {alembic_ini}")
        sys.exit(1)

    config = AlembicConfig(str(alembic_ini))

    try:
        # Run migrations
        print("Running database migrations...")
        command.upgrade(config, "head")
        print("✓ Migrations completed successfully!")

    except Exception as e:
        print(f"Error running migrations: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_migrations()
