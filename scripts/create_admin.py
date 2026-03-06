#!/usr/bin/env python3
"""Create an admin user manually."""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from hrisa_code.web.db.database import init_database
from hrisa_code.web.auth.user_service import UserService


async def create_admin_user(email: str):
    """Create an admin user.

    Args:
        email: Admin user email address
    """
    # Check if DATABASE_URL is set
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("Error: DATABASE_URL environment variable not set")
        print("Please set DATABASE_URL to your PostgreSQL connection string")
        print("Example: export DATABASE_URL='postgresql://user:pass@localhost:5432/dbname'")
        sys.exit(1)

    print(f"Connecting to database...")

    try:
        # Initialize database
        db = await init_database(database_url)

        # Create user service
        user_service = UserService()

        # Get session and create admin user
        async with db.get_session() as session:
            # Check if user already exists
            existing_user = await user_service.get_user_by_email(session, email)
            if existing_user:
                print(f"✗ User {email} already exists with role: {existing_user.role}")

                # Offer to upgrade to admin
                if existing_user.role != "admin":
                    response = input(f"Update {email} to admin role? (y/n): ")
                    if response.lower() == "y":
                        updated_user = await user_service.update_user_role(
                            session, existing_user.id, "admin"
                        )
                        await session.commit()
                        print(f"✓ User {email} upgraded to admin!")
                    else:
                        print("Cancelled.")
                sys.exit(0)

            # Create new admin user
            user = await user_service.create_user(
                session=session,
                email=email,
                role="admin",
            )

            await session.commit()

            print(f"✓ Admin user created successfully!")
            print(f"  Email: {user.email}")
            print(f"  Role: {user.role}")
            print(f"  ID: {user.id}")
            print(f"\nThe user can now log in at: {os.getenv('APP_BASE_URL', 'http://localhost:8000')}")

    except Exception as e:
        print(f"Error creating admin user: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python create_admin.py <email>")
        print("Example: python create_admin.py admin@example.com")
        sys.exit(1)

    email = sys.argv[1]

    # Validate email format
    if "@" not in email or "." not in email.split("@")[1]:
        print(f"Error: '{email}' does not appear to be a valid email address")
        sys.exit(1)

    # Run async function
    asyncio.run(create_admin_user(email))


if __name__ == "__main__":
    main()
