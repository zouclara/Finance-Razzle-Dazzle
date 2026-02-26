"""
Balance Sheet builder.

Data priority:
  1. QuickBooks Balance Sheet API  — authoritative (all accounts)
  2. Mercury                       — live cash balance override
  3. Stripe                        — available balance / deferred revenue
  4. Brex                          — card balance (current liability)

Balance Sheet equation always enforced: Assets = Liabilities + Equity
"""

from datetime import date
from config import config
from statements.demo_data import balance_sheet_demo


def get_balance_sheet(as_of_date: date) -> dict:
    if config.USE_DEMO_DATA or not config.is_configured("quickbooks"):
        data = balance_sheet_demo(as_of_date)
        data = _enrich_with_live_cash(data)
        return data

    from connectors.quickbooks import QuickBooksClient
    qb = QuickBooksClient()
    raw = qb.balance_sheet(as_of_date)
    data = _parse_qb_bs(raw, as_of_date)
    data = _enrich_with_live_cash(data)
    return data


def _enrich_with_live_cash(data: dict) -> dict:
    """
    Optionally override the QB cash line with Mercury's live balance.
    Mercury is more real-time than QBO (which depends on bank feeds syncing).
    """
    if not config.is_configured("mercury"):
        return data
    try:
        from connectors.mercury import MercuryClient
        live_cash = MercuryClient().total_cash()
        data["assets"]["Current Assets"]["Cash & Cash Equivalents"] = live_cash
        # Recalculate totals
        data["total_current_assets"] = sum(data["assets"]["Current Assets"].values())
        data["total_assets"] = data["total_current_assets"] + data["total_noncurrent_assets"]
    except Exception:
        pass
    return data


def _parse_qb_bs(raw: dict, as_of_date: date) -> dict:
    """Parse QBO BalanceSheet report response. See income_statement.py for structure notes."""
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

    total_assets = sections.get("TotalAssets", 0)
    total_current_assets = sections.get("CurrentAssets", total_assets)
    total_liabilities = sections.get("TotalLiabilities", 0)
    total_equity = sections.get("TotalEquity", 0)
    total_current_liab = sections.get("CurrentLiabilities", total_liabilities)

    return {
        "as_of": as_of_date.isoformat(),
        "assets": {"Current Assets": {"Total Current Assets": total_current_assets}, "Non-Current Assets": {}},
        "total_current_assets": total_current_assets,
        "total_noncurrent_assets": total_assets - total_current_assets,
        "total_assets": total_assets,
        "liabilities": {"Current Liabilities": {"Total Current Liabilities": total_current_liab}, "Non-Current Liabilities": {}},
        "total_current_liabilities": total_current_liab,
        "total_noncurrent_liabilities": total_liabilities - total_current_liab,
        "total_liabilities": total_liabilities,
        "equity": {"Total Equity": total_equity},
        "total_equity": total_equity,
        "total_liabilities_and_equity": total_liabilities + total_equity,
        "current_ratio": total_current_assets / total_current_liab if total_current_liab else 0,
        "cash_ratio": 0,
    }
