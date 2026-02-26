"""
Brex connector.

Brex enriches the Income Statement (expense categories) and Balance Sheet
(accounts payable / credit card balance) with:
  - Corporate card spend by category
  - Cash accounts (if using Brex banking)
  - Outstanding card balance (a current liability)

API docs: https://developer.brex.com/
Token: dashboard.brex.com → Settings → Developer → API tokens
Scopes: transactions.readonly, accounts.readonly, expenses.readonly
"""

import requests
from datetime import date
from config import config

BREX_BASE_URL = "https://platform.brexapis.com"


class BrexClient:

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {config.BREX_API_TOKEN}",
            "Content-Type": "application/json",
        }

    def accounts(self) -> list[dict]:
        """All Brex cash and card accounts with current balances."""
        resp = requests.get(
            f"{BREX_BASE_URL}/v2/accounts/cash",
            headers=self._headers(),
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json().get("items", [])

    def card_balance(self) -> float:
        """
        Outstanding corporate card balance — a current liability on the Balance Sheet.
        Represented as a negative number (money owed).
        """
        resp = requests.get(
            f"{BREX_BASE_URL}/v2/accounts/card",
            headers=self._headers(),
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        balance = data.get("current_balance", {}).get("amount", 0)
        return balance / 100  # Brex returns amounts in cents

    def transactions(self, start_date: date, end_date: date) -> list[dict]:
        """
        Cash account transactions (debit card / ACH transfers).
        For card expenses see card_transactions().
        """
        resp = requests.get(
            f"{BREX_BASE_URL}/v2/transactions/cash/primary",
            headers=self._headers(),
            params={
                "posted_at_start": f"{start_date.isoformat()}T00:00:00Z",
                "posted_at_end": f"{end_date.isoformat()}T23:59:59Z",
            },
            timeout=20,
        )
        resp.raise_for_status()
        return resp.json().get("items", [])

    def card_transactions(self, start_date: date, end_date: date) -> list[dict]:
        """
        Corporate card transactions with merchant category codes.
        Use these to validate/enrich expense categories in QBO.
        """
        resp = requests.get(
            f"{BREX_BASE_URL}/v2/transactions/card/primary",
            headers=self._headers(),
            params={
                "posted_at_start": f"{start_date.isoformat()}T00:00:00Z",
                "posted_at_end": f"{end_date.isoformat()}T23:59:59Z",
            },
            timeout=20,
        )
        resp.raise_for_status()
        return resp.json().get("items", [])

    def spend_by_category(self, start_date: date, end_date: date) -> dict[str, float]:
        """Aggregate card spend by expense category for the period."""
        txns = self.card_transactions(start_date, end_date)
        by_category: dict[str, float] = {}
        for t in txns:
            category = t.get("merchant_category", "Uncategorized")
            amount = t.get("amount", {}).get("amount", 0) / 100
            by_category[category] = by_category.get(category, 0) + amount
        return by_category
