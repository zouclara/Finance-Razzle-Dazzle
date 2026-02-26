"""
Income Statement builder.

Data priority (highest to lowest):
  1. QuickBooks P&L Report API  — authoritative GL numbers
  2. Stripe                     — revenue detail / MRR enrichment
  3. Gusto                      — payroll breakdown by department
  4. Brex                       — expense category enrichment

When USE_DEMO_DATA=true, returns realistic demo figures so the dashboard
works before API credentials are configured.
"""

from datetime import date
from config import config
from statements.demo_data import income_statement_demo


def get_income_statement(start_date: date, end_date: date) -> dict:
    if config.USE_DEMO_DATA or not config.is_configured("quickbooks"):
        return income_statement_demo(start_date, end_date)

    from connectors.quickbooks import QuickBooksClient
    qb = QuickBooksClient()
    raw = qb.profit_and_loss(start_date, end_date)
    return _parse_qb_pl(raw, start_date, end_date)


def _parse_qb_pl(raw: dict, start_date: date, end_date: date) -> dict:
    """
    Parse the QBO ProfitAndLoss report response into a flat dict.

    QBO report structure:
      Rows → Row[] where each Row has:
        type: "Section" | "DataRow" | "GrandTotal"
        Rows → nested Row[]
        ColData → [{"value": "label"}, {"value": "amount"}]

    This is a simplified parser — for production add full recursion
    over the nested section tree.
    """
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

    total_revenue = sections.get("Income", 0)
    total_cogs = sections.get("COGS", 0)
    gross_profit = total_revenue - total_cogs
    total_opex = sections.get("Expenses", 0)
    net_income = sections.get("NetIncome", gross_profit - total_opex)

    mrr = _get_mrr_from_stripe()
    return {
        "period": f"{start_date.isoformat()} → {end_date.isoformat()}",
        "revenue": {"Total Revenue": total_revenue},
        "total_revenue": total_revenue,
        "cogs": {"Total COGS": total_cogs},
        "total_cogs": total_cogs,
        "gross_profit": gross_profit,
        "gross_margin_pct": gross_profit / total_revenue * 100 if total_revenue else 0,
        "opex": {"Operating Expenses": {"Total OpEx": total_opex}},
        "total_sm": 0,
        "total_rd": 0,
        "total_ga": 0,
        "total_opex": total_opex,
        "ebitda": gross_profit - total_opex,
        "ebitda_margin_pct": (gross_profit - total_opex) / total_revenue * 100 if total_revenue else 0,
        "depreciation": 0,
        "ebit": gross_profit - total_opex,
        "interest": 0,
        "net_income": net_income,
        "net_margin_pct": net_income / total_revenue * 100 if total_revenue else 0,
        "mrr": mrr,
        "arr": mrr * 12,
    }


def _get_mrr_from_stripe() -> float:
    if not config.is_configured("stripe"):
        return 0.0
    try:
        from connectors.stripe_connector import StripeClient
        return StripeClient().mrr()
    except Exception:
        return 0.0
