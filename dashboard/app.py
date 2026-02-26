"""
Finance-Razzle-Dazzle — Streamlit Dashboard

Run:  streamlit run dashboard/app.py
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config
from statements.income_statement import get_income_statement
from statements.balance_sheet import get_balance_sheet
from statements.cash_flow import get_cash_flow_statement

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title=f"{config.COMPANY_NAME} — Financial Dashboard",
    page_icon="📊",
    layout="wide",
)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("Finance-Razzle-Dazzle")
    st.caption(config.COMPANY_NAME)
    st.divider()

    if config.USE_DEMO_DATA:
        st.warning("Demo mode — showing sample data. Set USE_DEMO_DATA=false in .env to connect live APIs.")

    view = st.radio(
        "Statement",
        ["Income Statement", "Balance Sheet", "Cash Flow Statement"],
        index=0,
    )
    st.divider()

    # Date controls
    today = date.today()
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "From",
            value=date(today.year, 1, 1),
            max_value=today,
        )
    with col2:
        end_date = st.date_input(
            "To",
            value=today,
            max_value=today,
        )

    st.divider()

    # Integration status
    st.subheader("Integrations")
    integrations = ["quickbooks", "stripe", "mercury", "brex", "gusto", "hubspot", "google_sheets"]
    labels = {
        "quickbooks": "QuickBooks",
        "stripe": "Stripe",
        "mercury": "Mercury",
        "brex": "Brex",
        "gusto": "Gusto",
        "hubspot": "HubSpot",
        "google_sheets": "Google Sheets",
    }
    for key in integrations:
        status = "✅" if config.is_configured(key) else "⚪"
        st.caption(f"{status} {labels[key]}")


# ── Helper: format currency ─────────────────────────────────────────────────────
def fmt(value: float, prefix: str = "$") -> str:
    if abs(value) >= 1_000_000:
        return f"{prefix}{value/1_000_000:.2f}M"
    if abs(value) >= 1_000:
        return f"{prefix}{value/1_000:.1f}K"
    return f"{prefix}{value:,.0f}"


def delta_color(value: float) -> str:
    return "normal" if value >= 0 else "inverse"


# ── Income Statement ────────────────────────────────────────────────────────────
if view == "Income Statement":
    data = get_income_statement(start_date, end_date)

    st.title("Income Statement (P&L)")
    st.caption(data["period"])

    # Top KPIs
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Revenue", fmt(data["total_revenue"]))
    k2.metric("Gross Profit", fmt(data["gross_profit"]),
              f"{data['gross_margin_pct']:.1f}% margin")
    k3.metric("EBITDA", fmt(data["ebitda"]),
              f"{data['ebitda_margin_pct']:.1f}% margin")
    k4.metric("Net Income", fmt(data["net_income"]),
              f"{data['net_margin_pct']:.1f}% margin")
    k5.metric("ARR (Stripe)", fmt(data.get("arr", 0)))

    st.divider()

    col_left, col_right = st.columns([2, 1])

    with col_left:
        # Waterfall chart
        categories = ["Revenue", "(-) COGS", "Gross Profit", "(-) S&M", "(-) R&D", "(-) G&A", "EBITDA"]
        values = [
            data["total_revenue"],
            -data["total_cogs"],
            data["gross_profit"],
            -data["total_sm"],
            -data["total_rd"],
            -data["total_ga"],
            data["ebitda"],
        ]
        colors = ["#2196F3" if v >= 0 else "#F44336" for v in values]

        fig = go.Figure(go.Bar(
            x=categories,
            y=values,
            marker_color=colors,
            text=[fmt(v) for v in values],
            textposition="outside",
        ))
        fig.update_layout(
            title="P&L Waterfall",
            yaxis_title="USD",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            height=400,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        # Margin summary
        st.subheader("Margin Summary")
        metrics = [
            ("Gross Margin", data["gross_margin_pct"]),
            ("EBITDA Margin", data["ebitda_margin_pct"]),
            ("Net Margin", data["net_margin_pct"]),
        ]
        for label, pct in metrics:
            color = "#4CAF50" if pct >= 0 else "#F44336"
            st.markdown(f"**{label}**")
            st.progress(max(0, min(100, int(abs(pct)))) / 100)
            st.caption(f"{pct:.1f}%")

    st.divider()

    # Detailed line items
    st.subheader("Revenue")
    rev_df = pd.DataFrame(
        [(k, v) for k, v in data["revenue"].items()],
        columns=["Line Item", "Amount ($)"],
    )
    st.dataframe(rev_df, use_container_width=True, hide_index=True)

    st.subheader("Cost of Goods Sold")
    cogs_df = pd.DataFrame(
        [(k, v) for k, v in data["cogs"].items()],
        columns=["Line Item", "Amount ($)"],
    )
    st.dataframe(cogs_df, use_container_width=True, hide_index=True)

    st.subheader("Operating Expenses")
    for bucket, items in data["opex"].items():
        with st.expander(bucket):
            opex_df = pd.DataFrame(
                [(k, v) for k, v in items.items()],
                columns=["Line Item", "Amount ($)"],
            )
            st.dataframe(opex_df, use_container_width=True, hide_index=True)

    # OpEx pie
    opex_labels = list(data["opex"].keys())
    opex_values = [data["total_sm"], data["total_rd"], data["total_ga"]]
    if any(v > 0 for v in opex_values):
        fig2 = px.pie(
            values=opex_values,
            names=opex_labels,
            title="OpEx Breakdown",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        st.plotly_chart(fig2, use_container_width=True)


# ── Balance Sheet ───────────────────────────────────────────────────────────────
elif view == "Balance Sheet":
    data = get_balance_sheet(end_date)

    st.title("Balance Sheet")
    st.caption(f"As of {data['as_of']}")

    # Sanity check
    diff = abs(data["total_assets"] - data["total_liabilities_and_equity"])
    if diff > 1:
        st.error(f"Balance Sheet out of balance by {fmt(diff)} — check your GL.")

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Assets", fmt(data["total_assets"]))
    k2.metric("Total Liabilities", fmt(data["total_liabilities"]))
    k3.metric("Total Equity", fmt(data["total_equity"]))
    k4.metric("Current Ratio", f"{data['current_ratio']:.2f}x")

    st.divider()

    col_a, col_l = st.columns(2)

    with col_a:
        st.subheader("Assets")
        for section, items in data["assets"].items():
            with st.expander(section, expanded=True):
                for k, v in items.items():
                    cols = st.columns([3, 1])
                    cols[0].caption(k)
                    cols[1].caption(fmt(v))
        st.markdown(f"**Total Assets: {fmt(data['total_assets'])}**")

    with col_l:
        st.subheader("Liabilities & Equity")
        for section, items in data["liabilities"].items():
            with st.expander(section, expanded=True):
                for k, v in items.items():
                    cols = st.columns([3, 1])
                    cols[0].caption(k)
                    cols[1].caption(fmt(v))
        st.markdown(f"**Total Liabilities: {fmt(data['total_liabilities'])}**")

        with st.expander("Equity", expanded=True):
            for k, v in data["equity"].items():
                cols = st.columns([3, 1])
                cols[0].caption(k)
                cols[1].caption(fmt(v))
        st.markdown(f"**Total Equity: {fmt(data['total_equity'])}**")

    st.divider()

    # Assets vs Liabilities+Equity visual
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Assets", x=["Balance Sheet"], y=[data["total_assets"]], marker_color="#2196F3"))
    fig.add_trace(go.Bar(name="Liabilities", x=["Balance Sheet"], y=[data["total_liabilities"]], marker_color="#F44336"))
    fig.add_trace(go.Bar(name="Equity", x=["Balance Sheet"], y=[data["total_equity"]], marker_color="#4CAF50"))
    fig.update_layout(
        barmode="group",
        title="Assets vs Liabilities & Equity",
        yaxis_title="USD",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=350,
    )
    st.plotly_chart(fig, use_container_width=True)


# ── Cash Flow Statement ─────────────────────────────────────────────────────────
elif view == "Cash Flow Statement":
    data = get_cash_flow_statement(start_date, end_date)

    st.title("Cash Flow Statement")
    st.caption(data["period"])

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Operating Cash Flow", fmt(data["cash_from_operations"]))
    k2.metric("Net Change in Cash", fmt(data["net_change_in_cash"]))
    k3.metric("Monthly Burn Rate", fmt(data["monthly_burn_rate"]))
    k4.metric(
        "Cash Runway",
        f"{data['runway_months']} mo" if data['runway_months'] < 999 else "∞",
    )

    st.divider()

    col_l, col_r = st.columns([1, 1])

    with col_l:
        # Waterfall: CFO → CFI → CFF → Ending Cash
        fig = go.Figure(go.Waterfall(
            name="Cash Flow",
            orientation="v",
            measure=["relative", "relative", "relative", "total"],
            x=["Operating", "Investing", "Financing", "Ending Cash"],
            y=[
                data["cash_from_operations"],
                data["cash_from_investing"],
                data["cash_from_financing"],
                data["ending_cash"],
            ],
            connector={"line": {"color": "rgb(63, 63, 63)"}},
            increasing={"marker": {"color": "#4CAF50"}},
            decreasing={"marker": {"color": "#F44336"}},
            totals={"marker": {"color": "#2196F3"}},
        ))
        fig.update_layout(
            title="Cash Flow Waterfall",
            yaxis_title="USD",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            height=400,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.subheader("Operating Activities")
        ops = data["operating_activities"]
        st.metric("Net Income", fmt(ops.get("Net Income", 0)))

        if ops.get("Adjustments"):
            st.caption("**Non-cash adjustments**")
            for k, v in ops["Adjustments"].items():
                cols = st.columns([3, 1])
                cols[0].caption(k)
                cols[1].caption(fmt(v))

        if ops.get("Working Capital Changes"):
            st.caption("**Working capital changes**")
            for k, v in ops["Working Capital Changes"].items():
                cols = st.columns([3, 1])
                cols[0].caption(k)
                cols[1].caption(fmt(v))

        st.markdown(f"**Cash from Operations: {fmt(data['cash_from_operations'])}**")

        st.divider()
        st.subheader("Investing Activities")
        for k, v in data.get("investing_activities", {}).items():
            cols = st.columns([3, 1])
            cols[0].caption(k)
            cols[1].caption(fmt(v))
        st.markdown(f"**Cash from Investing: {fmt(data['cash_from_investing'])}**")

        st.divider()
        st.subheader("Financing Activities")
        for k, v in data.get("financing_activities", {}).items():
            cols = st.columns([3, 1])
            cols[0].caption(k)
            cols[1].caption(fmt(v))
        st.markdown(f"**Cash from Financing: {fmt(data['cash_from_financing'])}**")

    st.divider()

    col_b, col_e = st.columns(2)
    col_b.metric("Beginning Cash", fmt(data["beginning_cash"]))
    col_e.metric("Ending Cash", fmt(data["ending_cash"]))

    if "reconciliation_difference" in data:
        diff = data["reconciliation_difference"]
        if abs(diff) > 1000:
            st.warning(
                f"Mercury reconciliation difference: {fmt(diff)}. "
                "This may indicate unsynced bank transactions in QuickBooks."
            )
        else:
            st.success("Mercury reconciliation: cash matches within tolerance.")
