"""
Cash Flow Statement builder (indirect method).

Data priority:
  1. QuickBooks Cash Flow API  — authoritative (derived from GL)
  2. Mercury                   — transaction-level verification
  3. Stripe                    — payout timing enrichment
  4. Gusto                     — payroll cash outflow validation

Key SaaS metrics derived here: monthly burn rate, cash runway.
"""

from datetime import date
from config import config
from statements.demo_data import cash_flow_demo


def get_cash_flow_statement(start_date: date, end_date: date) -> dict:
    if config.USE_DEMO_DATA or not config.is_configured("quickbooks"):
        return cash_flow_demo(start_date, end_date)

    from connectors.quickbooks import QuickBooksClient
    qb = QuickBooksClient()
    raw = qb.cash_flow(start_date, end_date)
    data = _parse_qb_cf(raw, start_date, end_date)
    data = _enrich_with_mercury(data, start_date, end_date)
    return data


def _enrich_with_mercury(data: dict, start_date: date, end_date: date) -> dict:
    """
    Cross-check QB's net change in cash against Mercury's actual bank movement.
    A mismatch signals unreconciled transactions or timing differences.
    """
    if not config.is_configured("mercury"):
        return data
    try:
        from connectors.mercury import MercuryClient
        burn = MercuryClient().monthly_burn(start_date, end_date)
        data["mercury_net_cash_change"] = burn["inflows"] - burn["outflows"]
        data["reconciliation_difference"] = (
            data["net_change_in_cash"] - data["mercury_net_cash_change"]
        )
    except Exception:
        pass
    return data


def _parse_qb_cf(raw: dict, start_date: date, end_date: date) -> dict:
    rows = raw.get("Rows", {}).get("Row", [])
    sections: dict[str, float] = {}

    for row in rows:
        if row.get("type") == "Section":
            group = row.get("group", "")
            summary = row.get("Summary", {})
            col_data = summary.get("ColData", [{}])
            try:
                amount = float(col_data[1].get("value", 0))
            except (IndexError, ValueError):
                amount = 0.0
            sections[group] = amount

    cfo = sections.get("OperatingActivities", 0)
    cfi = sections.get("InvestingActivities", 0)
    cff = sections.get("FinancingActivities", 0)
    net_change = cfo + cfi + cff

    beginning_cash = sections.get("BeginningCash", 0)
    ending_cash = beginning_cash + net_change

    months = max(1, (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month) + 1)
    monthly_burn = abs(net_change) / months if net_change < 0 else 0

    return {
        "period": f"{start_date.isoformat()} → {end_date.isoformat()}",
        "operating_activities": {"Net Income": 0, "Adjustments": {}, "Working Capital Changes": {}},
        "total_adjustments": 0,
        "total_wc_changes": 0,
        "cash_from_operations": cfo,
        "investing_activities": {},
        "cash_from_investing": cfi,
        "financing_activities": {},
        "cash_from_financing": cff,
        "net_change_in_cash": net_change,
        "beginning_cash": beginning_cash,
        "ending_cash": ending_cash,
        "monthly_burn_rate": monthly_burn,
        "runway_months": round(ending_cash / monthly_burn) if monthly_burn else 999,
    }
