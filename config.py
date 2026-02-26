import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    COMPANY_NAME: str = os.getenv("COMPANY_NAME", "My SaaS Co")
    FISCAL_YEAR_START_MONTH: int = int(os.getenv("FISCAL_YEAR_START_MONTH", "1"))
    USE_DEMO_DATA: bool = os.getenv("USE_DEMO_DATA", "true").lower() == "true"

    # QuickBooks
    QB_CLIENT_ID: str = os.getenv("QB_CLIENT_ID", "")
    QB_CLIENT_SECRET: str = os.getenv("QB_CLIENT_SECRET", "")
    QB_REALM_ID: str = os.getenv("QB_REALM_ID", "")
    QB_ACCESS_TOKEN: str = os.getenv("QB_ACCESS_TOKEN", "")
    QB_REFRESH_TOKEN: str = os.getenv("QB_REFRESH_TOKEN", "")
    QB_ENVIRONMENT: str = os.getenv("QB_ENVIRONMENT", "production")

    # Stripe
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")

    # Mercury
    MERCURY_API_TOKEN: str = os.getenv("MERCURY_API_TOKEN", "")

    # Brex
    BREX_API_TOKEN: str = os.getenv("BREX_API_TOKEN", "")

    # Gusto
    GUSTO_COMPANY_ID: str = os.getenv("GUSTO_COMPANY_ID", "")
    GUSTO_ACCESS_TOKEN: str = os.getenv("GUSTO_ACCESS_TOKEN", "")

    # HubSpot
    HUBSPOT_ACCESS_TOKEN: str = os.getenv("HUBSPOT_ACCESS_TOKEN", "")

    # Google Sheets
    GOOGLE_SERVICE_ACCOUNT_JSON: str = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    GOOGLE_SHEETS_SPREADSHEET_ID: str = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID", "")

    @property
    def qb_base_url(self) -> str:
        if self.QB_ENVIRONMENT == "sandbox":
            return "https://sandbox-quickbooks.api.intuit.com"
        return "https://quickbooks.api.intuit.com"

    def is_configured(self, integration: str) -> bool:
        checks = {
            "quickbooks": bool(self.QB_ACCESS_TOKEN and self.QB_REALM_ID),
            "stripe": bool(self.STRIPE_SECRET_KEY),
            "mercury": bool(self.MERCURY_API_TOKEN),
            "brex": bool(self.BREX_API_TOKEN),
            "gusto": bool(self.GUSTO_ACCESS_TOKEN and self.GUSTO_COMPANY_ID),
            "hubspot": bool(self.HUBSPOT_ACCESS_TOKEN),
            "google_sheets": bool(self.GOOGLE_SERVICE_ACCOUNT_JSON and self.GOOGLE_SHEETS_SPREADSHEET_ID),
        }
        return checks.get(integration, False)


config = Config()
