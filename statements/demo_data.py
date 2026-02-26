"""
Realistic demo data for a B2B SaaS startup (~$2M ARR, Series A stage).
Used when USE_DEMO_DATA=true so the dashboard works before credentials are live.
"""

from datetime import date


def income_statement_demo(start_date: date, end_date: date) -> dict:
    months = max(1, (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month) + 1)
    scale = months / 12

    revenue = {
        "Subscription Revenue": round(1_820_000 * scale),
        "Professional Services": round(180_000 * scale),
    }
    total_revenue = sum(revenue.values())

    cogs = {
        "Hosting & Infrastructure": round(91_000 * scale),
        "Customer Success (Payroll)": round(210_000 * scale),
        "Third-Party Software (COGS)": round(36_400 * scale),
        "Payment Processing Fees": round(18_200 * scale),
    }
    total_cogs = sum(cogs.values())
    gross_profit = total_revenue - total_cogs

    opex = {
        "Sales & Marketing": {
            "Sales Payroll": round(480_000 * scale),
            "Marketing Payroll": round(180_000 * scale),
            "Advertising & Demand Gen": round(240_000 * scale),
            "Sales Tools & Software": round(36_000 * scale),
        },
        "Research & Development": {
            "Engineering Payroll": round(560_000 * scale),
            "R&D Software & Tools": round(48_000 * scale),
        },
        "General & Administrative": {
            "G&A Payroll": round(240_000 * scale),
            "Legal & Professional": round(72_000 * scale),
            "Office & Facilities": round(36_000 * scale),
            "Insurance": round(18_000 * scale),
            "Other G&A": round(24_000 * scale),
        },
    }
    total_sm = sum(opex["Sales & Marketing"].values())
    total_rd = sum(opex["Research & Development"].values())
    total_ga = sum(opex["General & Administrative"].values())
    total_opex = total_sm + total_rd + total_ga

    ebitda = gross_profit - total_opex
    depreciation = round(12_000 * scale)
    ebit = ebitda - depreciation
    interest = round(4_800 * scale)
    net_income = ebit - interest

    return {
        "period": f"{start_date.isoformat()} → {end_date.isoformat()}",
        "revenue": revenue,
        "total_revenue": total_revenue,
        "cogs": cogs,
        "total_cogs": total_cogs,
        "gross_profit": gross_profit,
        "gross_margin_pct": gross_profit / total_revenue * 100 if total_revenue else 0,
        "opex": opex,
        "total_sm": total_sm,
        "total_rd": total_rd,
        "total_ga": total_ga,
        "total_opex": total_opex,
        "ebitda": ebitda,
        "ebitda_margin_pct": ebitda / total_revenue * 100 if total_revenue else 0,
        "depreciation": depreciation,
        "ebit": ebit,
        "interest": interest,
        "net_income": net_income,
        "net_margin_pct": net_income / total_revenue * 100 if total_revenue else 0,
        # SaaS enrichment (from Stripe)
        "mrr": 151_667,
        "arr": 1_820_000,
    }


def balance_sheet_demo(as_of_date: date) -> dict:
    assets = {
        "Current Assets": {
            "Cash & Cash Equivalents": 1_240_000,   # Mercury
            "Stripe Balance (Available)": 48_300,   # Stripe
            "Accounts Receivable": 210_000,          # QB
            "Prepaid Expenses": 36_000,
        },
        "Non-Current Assets": {
            "Property & Equipment (Net)": 42_000,
            "Intangible Assets": 18_000,
            "Security Deposits": 12_000,
        },
    }
    total_current_assets = sum(assets["Current Assets"].values())
    total_noncurrent_assets = sum(assets["Non-Current Assets"].values())
    total_assets = total_current_assets + total_noncurrent_assets

    liabilities = {
        "Current Liabilities": {
            "Accounts Payable": 68_000,
            "Brex Card Balance": 24_000,             # Brex
            "Accrued Payroll & Benefits": 62_000,    # Gusto
            "Deferred Revenue": 145_000,             # Stripe (annual plans)
            "Other Accrued Liabilities": 18_000,
        },
        "Non-Current Liabilities": {
            "Long-Term Debt": 0,
            "Deferred Rent": 8_000,
        },
    }
    total_current_liab = sum(liabilities["Current Liabilities"].values())
    total_noncurrent_liab = sum(liabilities["Non-Current Liabilities"].values())
    total_liabilities = total_current_liab + total_noncurrent_liab

    equity = {
        "Common Stock": 5_000,
        "Additional Paid-In Capital": 4_800_000,
        "Retained Earnings (Deficit)": -(total_liabilities + 5_000 + 4_800_000 - total_assets),
    }
    total_equity = sum(equity.values())

    return {
        "as_of": as_of_date.isoformat(),
        "assets": assets,
        "total_current_assets": total_current_assets,
        "total_noncurrent_assets": total_noncurrent_assets,
        "total_assets": total_assets,
        "liabilities": liabilities,
        "total_current_liabilities": total_current_liab,
        "total_noncurrent_liabilities": total_noncurrent_liab,
        "total_liabilities": total_liabilities,
        "equity": equity,
        "total_equity": total_equity,
        "total_liabilities_and_equity": total_liabilities + total_equity,
        # Key ratios
        "current_ratio": total_current_assets / total_current_liab if total_current_liab else 0,
        "cash_ratio": assets["Current Assets"]["Cash & Cash Equivalents"] / total_current_liab if total_current_liab else 0,
    }


def cash_flow_demo(start_date: date, end_date: date) -> dict:
    months = max(1, (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month) + 1)
    scale = months / 12

    operating = {
        "Net Income": round(-368_200 * scale),
        "Adjustments": {
            "Depreciation & Amortization": round(12_000 * scale),
            "Stock-Based Compensation": round(96_000 * scale),
        },
        "Working Capital Changes": {
            "Increase in Accounts Receivable": round(-42_000 * scale),
            "Increase in Deferred Revenue": round(72_000 * scale),
            "Increase in Accounts Payable": round(18_000 * scale),
            "Change in Accrued Liabilities": round(8_000 * scale),
            "Change in Prepaid Expenses": round(-6_000 * scale),
        },
    }
    total_adjustments = sum(operating["Adjustments"].values())
    total_wc_changes = sum(operating["Working Capital Changes"].values())
    cfo = operating["Net Income"] + total_adjustments + total_wc_changes

    investing = {
        "Capital Expenditures": round(-18_000 * scale),
        "Purchase of Intangibles": round(-6_000 * scale),
    }
    cfi = sum(investing.values())

    financing = {
        "Proceeds from Stock Issuance": 0,
        "Repayment of Debt": 0,
    }
    cff = sum(financing.values())

    # From Mercury
    beginning_cash = 1_450_000
    net_change = cfo + cfi + cff
    ending_cash = beginning_cash + net_change

    return {
        "period": f"{start_date.isoformat()} → {end_date.isoformat()}",
        "operating_activities": operating,
        "total_adjustments": total_adjustments,
        "total_wc_changes": total_wc_changes,
        "cash_from_operations": cfo,
        "investing_activities": investing,
        "cash_from_investing": cfi,
        "financing_activities": financing,
        "cash_from_financing": cff,
        "net_change_in_cash": net_change,
        "beginning_cash": beginning_cash,
        "ending_cash": ending_cash,
        # Burn metrics (from Mercury)
        "monthly_burn_rate": round(abs(net_change) / months),
        "runway_months": round(ending_cash / (abs(net_change) / months)) if net_change < 0 else 999,
    }
