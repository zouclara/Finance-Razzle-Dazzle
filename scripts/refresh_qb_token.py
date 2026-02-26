"""
QuickBooks OAuth Token Refresh

Run this script to rotate your QB access token when it expires (every 1 hour).
Refresh tokens last 100 days — run this at least once per week via cron.

Usage:
    python scripts/refresh_qb_token.py

It will print the new access_token and refresh_token.
Update your .env file with the new values.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from connectors.quickbooks import QuickBooksClient
from config import config

if __name__ == "__main__":
    if not config.QB_CLIENT_ID or not config.QB_REFRESH_TOKEN:
        print("ERROR: QB_CLIENT_ID and QB_REFRESH_TOKEN must be set in .env")
        sys.exit(1)

    client = QuickBooksClient()
    new_token = client.refresh_access_token()
    print(f"\nNew QB_ACCESS_TOKEN:\n{new_token}\n")
    print("Update QB_ACCESS_TOKEN in your .env file.")
