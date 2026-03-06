#!/usr/bin/env python3
"""
Render.com Deployment Automation Script
Uses Render API to configure environment variables and trigger deployment

PREREQUISITES:
1. Render API Key - Get from: https://dashboard.render.com/u/settings#api-keys
2. Render Service ID - Find in service URL: render.com/services/{SERVICE_ID}
3. PostgreSQL Database already created in Render (script will fetch Internal URL)

USAGE:
    export RENDER_API_KEY=your_api_key_here
    python scripts/deploy-to-render.py --service-id srv-xxxxx --database-id dpg-xxxxx

Or provide API key interactively:
    python scripts/deploy-to-render.py --service-id srv-xxxxx --database-id dpg-xxxxx
"""

import os
import sys
import json
import argparse
from typing import Dict, Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


class RenderAPIClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.render.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make HTTP request to Render API."""
        url = f"{self.base_url}{endpoint}"
        req_data = json.dumps(data).encode('utf-8') if data else None

        request = Request(url, data=req_data, headers=self.headers, method=method)

        try:
            with urlopen(request) as response:
                return json.loads(response.read().decode('utf-8'))
        except HTTPError as e:
            error_body = e.read().decode('utf-8')
            print(f"❌ HTTP Error {e.code}: {error_body}")
            raise
        except URLError as e:
            print(f"❌ URL Error: {e.reason}")
            raise

    def get_database_info(self, database_id: str) -> Dict:
        """Get PostgreSQL database information including Internal URL."""
        return self._request("GET", f"/postgres/{database_id}")

    def get_service_env_vars(self, service_id: str) -> Dict:
        """Get current environment variables for a service."""
        return self._request("GET", f"/services/{service_id}/env-vars")

    def update_service_env_vars(self, service_id: str, env_vars: Dict[str, str]) -> Dict:
        """Update environment variables for a service."""
        # Format env vars for Render API
        env_var_items = [{"key": k, "value": v} for k, v in env_vars.items()]
        return self._request("PUT", f"/services/{service_id}/env-vars", env_var_items)

    def trigger_deploy(self, service_id: str) -> Dict:
        """Trigger a manual deployment."""
        return self._request("POST", f"/services/{service_id}/deploys", {"clearCache": "do_not_clear"})


def get_gmail_app_password() -> str:
    """Prompt user for Gmail app password with instructions."""
    print("\n" + "="*60)
    print("Gmail App Password Setup")
    print("="*60)
    print("1. Enable 2FA on your Gmail account")
    print("2. Go to: https://myaccount.google.com/apppasswords")
    print("3. Create app password for 'Mail'")
    print("4. Copy the 16-character password (no spaces)")
    print("="*60 + "\n")

    password = input("Enter Gmail App Password: ").strip()
    if not password:
        print("❌ App password is required")
        sys.exit(1)
    return password


def main():
    parser = argparse.ArgumentParser(
        description="Automate Render.com deployment for Hrisa Code authentication system"
    )
    parser.add_argument(
        "--service-id",
        required=True,
        help="Render service ID (e.g., srv-xxxxx)",
    )
    parser.add_argument(
        "--database-id",
        required=True,
        help="Render PostgreSQL database ID (e.g., dpg-xxxxx)",
    )
    parser.add_argument(
        "--gmail",
        help="Gmail address for SMTP (will prompt if not provided)",
    )
    parser.add_argument(
        "--admin-email",
        help="Admin user email (optional, for documentation)",
    )
    parser.add_argument(
        "--skip-deploy",
        action="store_true",
        help="Skip triggering deployment (just update env vars)",
    )

    args = parser.parse_args()

    # Get API key from environment or prompt
    api_key = os.getenv("RENDER_API_KEY")
    if not api_key:
        print("\n⚠️  RENDER_API_KEY not found in environment")
        print("Get your API key from: https://dashboard.render.com/u/settings#api-keys\n")
        api_key = input("Enter Render API Key: ").strip()
        if not api_key:
            print("❌ API key is required")
            sys.exit(1)

    # Get Gmail credentials
    gmail_user = args.gmail or input("\nEnter Gmail address: ").strip()
    if not gmail_user:
        print("❌ Gmail address is required")
        sys.exit(1)

    gmail_password = get_gmail_app_password()

    # Read generated SECRET_KEY from .env.production
    secret_key = "30a909bcb8b888c5a2078b49a7d3f951f0c768dc5d3eb89f93054eb564ed836d"

    print("\n" + "="*60)
    print("Render Deployment Automation")
    print("="*60)
    print(f"Service ID: {args.service_id}")
    print(f"Database ID: {args.database_id}")
    print("="*60 + "\n")

    client = RenderAPIClient(api_key)

    # Step 1: Get database Internal URL
    print("Step 1: Fetching PostgreSQL database info...")
    try:
        db_info = client.get_database_info(args.database_id)
        database_url = db_info.get("internalConnectionString")
        if not database_url:
            print("❌ Could not retrieve Internal Database URL")
            print("   Please create PostgreSQL database in Render Dashboard first")
            sys.exit(1)
        print(f"✓ Database URL retrieved: {database_url[:30]}...")
    except Exception as e:
        print(f"❌ Failed to fetch database info: {e}")
        print("   Make sure:")
        print("   1. PostgreSQL database is created in Render")
        print("   2. Database ID is correct (dpg-xxxxx)")
        print("   3. API key has access to this database")
        sys.exit(1)

    # Step 2: Prepare environment variables
    print("\nStep 2: Preparing environment variables...")
    env_vars = {
        "DATABASE_URL": database_url,
        "SMTP_HOST": "smtp.gmail.com",
        "SMTP_PORT": "587",
        "SMTP_USER": gmail_user,
        "SMTP_PASSWORD": gmail_password,
        "SMTP_FROM_EMAIL": "noreply@hrisa.local",
        "APP_BASE_URL": "https://hrisa-backend.onrender.com",
        "SECRET_KEY": secret_key,
        "ALLOWED_ORIGINS": "https://hrisa-backend.onrender.com,https://hrisa-mywebsite.vercel.app",
        "SESSION_EXPIRY_DAYS": "30",
        "MAGIC_LINK_EXPIRY_MINUTES": "15",
        "DB_ECHO": "false",
        "LOG_LEVEL": "INFO",
    }

    print(f"✓ {len(env_vars)} environment variables prepared")

    # Step 3: Update environment variables
    print("\nStep 3: Updating environment variables in Render...")
    try:
        client.update_service_env_vars(args.service_id, env_vars)
        print("✓ Environment variables updated successfully")
    except Exception as e:
        print(f"❌ Failed to update environment variables: {e}")
        print("   Make sure:")
        print("   1. Service ID is correct (srv-xxxxx)")
        print("   2. API key has access to this service")
        sys.exit(1)

    # Step 4: Trigger deployment
    if not args.skip_deploy:
        print("\nStep 4: Triggering deployment...")
        try:
            deploy_info = client.trigger_deploy(args.service_id)
            deploy_id = deploy_info.get("id", "unknown")
            print(f"✓ Deployment triggered: {deploy_id}")
            print(f"   Monitor at: https://dashboard.render.com/services/{args.service_id}")
        except Exception as e:
            print(f"❌ Failed to trigger deployment: {e}")
            print("   You can manually trigger deployment in Render Dashboard")
    else:
        print("\nStep 4: Skipped (--skip-deploy flag)")
        print("   Trigger deployment manually in Render Dashboard")

    # Final instructions
    print("\n" + "="*60)
    print("Deployment Configuration Complete! ✓")
    print("="*60)
    print("\nNext steps:")
    print("1. Wait for Render to complete deployment (~5-10 minutes)")
    print("2. Go to Render Dashboard → Your Service → Shell → Launch Shell")
    print("3. Run migrations:")
    print("   alembic upgrade head")
    print("4. Create admin user:")
    admin_email = args.admin_email or "admin@yourdomain.com"
    print(f"   python scripts/create_admin.py {admin_email}")
    print("5. Test login at: https://hrisa-mywebsite.vercel.app")
    print("\nOr use the automated script:")
    print("   bash scripts/render-shell-setup.sh")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
