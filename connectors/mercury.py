"""
Mercury connector.

Mercury is the primary cash source of truth for:
  - Real-time bank balances (Balance Sheet: cash line)
  - Inflows and outflows (Cash Flow Statement enrichment)
  - Burn rate calculation

API docs: https://docs.mercury.com/reference
Token: app.mercury.com → Settings → API
"""

import requests
from datetime import date
from config import config

MERCURY_BASE_URL = "https://api.mercury.com/api/v1"


class MercuryClient:

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {config.MERCURY_API_TOKEN}",
            "Accept": "application/json",
        }

    def accounts(self) -> list[dict]:
        """All Mercury accounts with live balances."""
        resp = requests.get(
            f"{MERCURY_BASE_URL}/accounts",
            headers=self._headers(),
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json().get("accounts", [])

    def total_cash(self) -> float:
        """Sum of all Mercury account balances in USD."""
        return sum(
            acct.get("currentBalance", 0) for acct in self.accounts()
        )

    def transactions(self, start_date: date, end_date: date) -> list[dict]:
        """
        All transactions in the date range across all accounts.
        Kind: 'credit' (money in) or 'debit' (money out).
        """
        results = []
        for acct in self.accounts():
            account_id = acct["id"]
            resp = requests.get(
                f"{MERCURY_BASE_URL}/account/{account_id}/transactions",
                headers=self._headers(),
                params={
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                    "limit": 500,
                },
                timeout=20,
            )
            resp.raise_for_status()
            results.extend(resp.json().get("transactions", []))
        return results

    def monthly_burn(self, start_date: date, end_date: date) -> dict:
        """
        Net cash change for the period.
        Burn = total debits (outflows) - total credits (inflows).
        """
        txns = self.transactions(start_date, end_date)
        inflows = sum(t["amount"] for t in txns if t.get("kind") == "credit")
        outflows = sum(t["amount"] for t in txns if t.get("kind") == "debit")
        return {
            "inflows": inflows,
            "outflows": outflows,
            "net_burn": outflows - inflows,
        }
