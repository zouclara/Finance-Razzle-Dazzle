"""
HubSpot connector.

HubSpot bridges your SLG motion into the financial picture:
  - Pipeline value (forecasted revenue)
  - Closed-won revenue by period (for revenue reconciliation vs Stripe/QBO)
  - CAC calculation: marketing + sales spend / new customers

Useful for: revenue forecasting, CAC payback period, SaaS metrics alongside P&L.

API docs: https://developers.hubspot.com/docs/api/crm/deals
Token: app.hubspot.com → Settings → Integrations → Private Apps
Scopes: crm.objects.deals.read, crm.objects.contacts.read
"""

import requests
from datetime import date, datetime
from config import config

HUBSPOT_BASE_URL = "https://api.hubapi.com"


class HubSpotClient:

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {config.HUBSPOT_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }

    def pipeline_value(self) -> dict:
        """
        Total open pipeline value by stage.
        Multiply by stage probability for weighted pipeline.
        """
        payload = {
            "filterGroups": [
                {"filters": [{"propertyName": "dealstage", "operator": "NEQ", "value": "closedlost"}]}
            ],
            "properties": ["dealname", "amount", "dealstage", "closedate"],
            "limit": 200,
        }
        resp = requests.post(
            f"{HUBSPOT_BASE_URL}/crm/v3/objects/deals/search",
            headers=self._headers(),
            json=payload,
            timeout=20,
        )
        resp.raise_for_status()
        deals = resp.json().get("results", [])

        by_stage: dict[str, float] = {}
        for deal in deals:
            stage = deal["properties"].get("dealstage", "unknown")
            amount = float(deal["properties"].get("amount") or 0)
            by_stage[stage] = by_stage.get(stage, 0) + amount

        return {
            "by_stage": by_stage,
            "total_open_pipeline": sum(by_stage.values()),
        }

    def closed_won_in_period(self, start_date: date, end_date: date) -> float:
        """Closed-won deal value in the period — cross-check vs Stripe revenue."""
        start_ts = int(datetime.combine(start_date, datetime.min.time()).timestamp() * 1000)
        end_ts = int(datetime.combine(end_date, datetime.max.time()).timestamp() * 1000)

        payload = {
            "filterGroups": [
                {
                    "filters": [
                        {"propertyName": "dealstage", "operator": "EQ", "value": "closedwon"},
                        {"propertyName": "closedate", "operator": "GTE", "value": str(start_ts)},
                        {"propertyName": "closedate", "operator": "LTE", "value": str(end_ts)},
                    ]
                }
            ],
            "properties": ["amount", "closedate"],
            "limit": 200,
        }
        resp = requests.post(
            f"{HUBSPOT_BASE_URL}/crm/v3/objects/deals/search",
            headers=self._headers(),
            json=payload,
            timeout=20,
        )
        resp.raise_for_status()
        deals = resp.json().get("results", [])
        return sum(float(d["properties"].get("amount") or 0) for d in deals)

    def new_customers_count(self, start_date: date, end_date: date) -> int:
        """Count of closed-won deals in the period — denominator for CAC."""
        start_ts = int(datetime.combine(start_date, datetime.min.time()).timestamp() * 1000)
        end_ts = int(datetime.combine(end_date, datetime.max.time()).timestamp() * 1000)

        payload = {
            "filterGroups": [
                {
                    "filters": [
                        {"propertyName": "dealstage", "operator": "EQ", "value": "closedwon"},
                        {"propertyName": "closedate", "operator": "GTE", "value": str(start_ts)},
                        {"propertyName": "closedate", "operator": "LTE", "value": str(end_ts)},
                    ]
                }
            ],
            "limit": 200,
        }
        resp = requests.post(
            f"{HUBSPOT_BASE_URL}/crm/v3/objects/deals/search",
            headers=self._headers(),
            json=payload,
            timeout=20,
        )
        resp.raise_for_status()
        return resp.json().get("total", 0)
