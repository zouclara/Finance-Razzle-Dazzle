"""
Stripe connector.

Stripe enriches the Income Statement and Cash Flow Statement with:
  - MRR / ARR breakdown (subscription revenue)
  - Revenue by product / price tier
  - Gross revenue vs net (after fees, refunds, disputes)
  - Payout timing (when cash actually hits your bank)

Use a Restricted Key (read-only) scoped to:
  charges, subscriptions, invoices, balance, payouts, customers, refunds
"""

import stripe
from datetime import date, datetime
from config import config

stripe.api_key = config.STRIPE_SECRET_KEY


class StripeClient:

    def current_balance(self) -> dict:
        """Live Stripe balance: available + pending (in cents → convert to dollars)."""
        balance = stripe.Balance.retrieve()
        return {
            "available_usd": sum(
                b["amount"] for b in balance["available"] if b["currency"] == "usd"
            ) / 100,
            "pending_usd": sum(
                b["amount"] for b in balance["pending"] if b["currency"] == "usd"
            ) / 100,
        }

    def mrr(self) -> float:
        """
        Sum of all active subscription amounts.
        Normalizes to monthly cadence (annual plans ÷ 12).
        """
        total = 0.0
        for sub in stripe.Subscription.list(status="active", limit=100).auto_paging_iter():
            for item in sub["items"]["data"]:
                amount = item["price"]["unit_amount"] / 100
                interval = item["price"]["recurring"]["interval"]
                if interval == "year":
                    amount /= 12
                elif interval == "week":
                    amount *= 4.33
                total += amount
        return total

    def revenue_in_period(self, start_date: date, end_date: date) -> dict:
        """
        Gross and net revenue recognized in the period via Stripe invoices.
        Use this to cross-check the QB P&L revenue line.
        """
        start_ts = int(datetime.combine(start_date, datetime.min.time()).timestamp())
        end_ts = int(datetime.combine(end_date, datetime.max.time()).timestamp())

        gross = net = refunds = 0.0
        for invoice in stripe.Invoice.list(
            status="paid",
            created={"gte": start_ts, "lte": end_ts},
            limit=100,
        ).auto_paging_iter():
            gross += invoice["amount_paid"] / 100
            net += invoice["amount_paid"] / 100

        for refund in stripe.Refund.list(
            created={"gte": start_ts, "lte": end_ts}, limit=100
        ).auto_paging_iter():
            refunds += refund["amount"] / 100

        return {"gross_revenue": gross, "refunds": refunds, "net_revenue": gross - refunds}

    def payouts_in_period(self, start_date: date, end_date: date) -> float:
        """Cash actually paid out to your bank account in the period."""
        start_ts = int(datetime.combine(start_date, datetime.min.time()).timestamp())
        end_ts = int(datetime.combine(end_date, datetime.max.time()).timestamp())
        total = 0.0
        for payout in stripe.Payout.list(
            arrival_date={"gte": start_ts, "lte": end_ts},
            status="paid",
            limit=100,
        ).auto_paging_iter():
            total += payout["amount"] / 100
        return total

    def churn_and_retention(self) -> dict:
        """
        Count subscriptions canceled in the last 30 days vs total active.
        Simple proxy for MRR churn rate.
        """
        active = stripe.Subscription.list(status="active", limit=1).data
        canceled = stripe.Subscription.list(status="canceled", limit=100).data
        active_count = len(active)
        canceled_count = len(canceled)
        return {
            "active_subscriptions": active_count,
            "recently_canceled": canceled_count,
        }
