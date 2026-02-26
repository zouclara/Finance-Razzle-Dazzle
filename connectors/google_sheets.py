"""
Google Sheets connector.

Use Sheets as the escape hatch for anything not yet automated:
  - Manual journal entries (e.g. prepaid expenses, deferred revenue adjustments)
  - Budget vs actuals (paste QB actuals, compare to your Sheets model)
  - Headcount plan for payroll forecasting
  - Investor reporting templates

Setup:
  1. Create a Service Account at console.cloud.google.com
  2. Enable Google Sheets API
  3. Share your spreadsheet with the service account email
  4. Download the JSON key → set GOOGLE_SERVICE_ACCOUNT_JSON in .env

Tab naming convention this connector expects:
  "Manual Entries"   — date, account, debit, credit, memo
  "Budget"           — month, line_item, budgeted_amount
"""

from google.oauth2 import service_account
from googleapiclient.discovery import build
import pandas as pd
from config import config

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


class GoogleSheetsClient:

    def __init__(self):
        creds = service_account.Credentials.from_service_account_file(
            config.GOOGLE_SERVICE_ACCOUNT_JSON,
            scopes=SCOPES,
        )
        self.service = build("sheets", "v4", credentials=creds)
        self.spreadsheet_id = config.GOOGLE_SHEETS_SPREADSHEET_ID

    def _read_tab(self, tab_name: str) -> pd.DataFrame:
        result = (
            self.service.spreadsheets()
            .values()
            .get(spreadsheetId=self.spreadsheet_id, range=tab_name)
            .execute()
        )
        rows = result.get("values", [])
        if not rows:
            return pd.DataFrame()
        return pd.DataFrame(rows[1:], columns=rows[0])

    def manual_journal_entries(self) -> pd.DataFrame:
        """
        Read manual journal entries.
        Expected columns: date, account, debit, credit, memo
        """
        df = self._read_tab("Manual Entries")
        if df.empty:
            return df
        df["debit"] = pd.to_numeric(df.get("debit", 0), errors="coerce").fillna(0)
        df["credit"] = pd.to_numeric(df.get("credit", 0), errors="coerce").fillna(0)
        df["date"] = pd.to_datetime(df.get("date", ""), errors="coerce")
        return df

    def budget(self) -> pd.DataFrame:
        """
        Monthly budget by line item.
        Expected columns: month (YYYY-MM), line_item, budgeted_amount
        """
        df = self._read_tab("Budget")
        if df.empty:
            return df
        df["budgeted_amount"] = pd.to_numeric(
            df.get("budgeted_amount", 0), errors="coerce"
        ).fillna(0)
        return df
