"""
QuickBooks Online connector.

QuickBooks is the general ledger and primary source of truth for all three
financial statements. The Reports API returns pre-built P&L, Balance Sheet,
and Cash Flow data that mirrors what you see in QBO.

OAuth 2.0 flow: developer.intuit.com → My Apps → Keys & OAuth
Scopes needed: com.intuit.quickbooks.accounting
"""

import requests
from datetime import date, timedelta
from typing import Any
from config import config


class QuickBooksClient:
    """Thin wrapper around the QBO v3 Reports API."""

    def __init__(self):
        self.base_url = config.qb_base_url
        self.realm_id = config.QB_REALM_ID
        self.access_token = config.QB_ACCESS_TOKEN

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
        }

    def _get_report(self, report_name: str, params: dict) -> dict[str, Any]:
        url = f"{self.base_url}/v3/company/{self.realm_id}/reports/{report_name}"
        resp = requests.get(url, headers=self._headers(), params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def profit_and_loss(
        self,
        start_date: date,
        end_date: date,
        accounting_method: str = "Accrual",
    ) -> dict[str, Any]:
        """
        Returns the full P&L report from QBO.
        The response includes Revenue, COGS, Gross Profit, and all OpEx lines.
        """
        return self._get_report(
            "ProfitAndLoss",
            {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "accounting_method": accounting_method,
            },
        )

    def balance_sheet(
        self,
        as_of_date: date,
        accounting_method: str = "Accrual",
    ) -> dict[str, Any]:
        """
        Returns the Balance Sheet as of a specific date.
        Covers Assets, Liabilities, and Equity.
        """
        return self._get_report(
            "BalanceSheet",
            {
                "start_date": as_of_date.replace(day=1).isoformat(),
                "end_date": as_of_date.isoformat(),
                "accounting_method": accounting_method,
            },
        )

    def cash_flow(
        self,
        start_date: date,
        end_date: date,
    ) -> dict[str, Any]:
        """
        Returns the Cash Flow Statement (indirect method).
        Covers Operating, Investing, and Financing activities.
        """
        return self._get_report(
            "CashFlow",
            {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
        )

    def refresh_access_token(self) -> str:
        """
        Exchange the refresh token for a new access token.
        QBO access tokens expire after 1 hour; refresh tokens last 100 days.
        Store the returned tokens in your .env or secrets manager.
        """
        resp = requests.post(
            "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer",
            auth=(config.QB_CLIENT_ID, config.QB_CLIENT_SECRET),
            data={
                "grant_type": "refresh_token",
                "refresh_token": config.QB_REFRESH_TOKEN,
            },
            timeout=15,
        )
        resp.raise_for_status()
        tokens = resp.json()
        return tokens["access_token"]
