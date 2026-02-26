"""
Gusto connector.

Gusto is the source of truth for payroll — your largest cost line.
Key use cases for financial statements:
  - Income Statement: total wages by department (COGS vs S&M vs R&D vs G&A)
  - Cash Flow: payroll cash outflows by pay period
  - Balance Sheet: accrued wages (if payroll spans a period-end)

API docs: https://docs.gusto.com/app-integrations/reference
OAuth app: dev.gusto.com
Scopes: payrolls:read, employees:read, companies:read
"""

import requests
from datetime import date
from config import config

GUSTO_BASE_URL = "https://api.gusto.com"


class GustoClient:

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {config.GUSTO_ACCESS_TOKEN}",
            "X-Gusto-API-Version": "2024-03-01",
            "Content-Type": "application/json",
        }

    def company(self) -> dict:
        resp = requests.get(
            f"{GUSTO_BASE_URL}/v1/companies/{config.GUSTO_COMPANY_ID}",
            headers=self._headers(),
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()

    def payrolls(self, start_date: date, end_date: date) -> list[dict]:
        """
        All processed payrolls in the date range.
        Each payroll has gross_pay, employee_benefits, employer_taxes.
        """
        resp = requests.get(
            f"{GUSTO_BASE_URL}/v1/companies/{config.GUSTO_COMPANY_ID}/payrolls",
            headers=self._headers(),
            params={
                "processed": True,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            timeout=20,
        )
        resp.raise_for_status()
        return resp.json()

    def total_payroll_cost(self, start_date: date, end_date: date) -> dict:
        """
        Aggregate payroll costs for the period.
        Returns gross wages, employer taxes, benefits — the full employer cost.
        """
        payrolls = self.payrolls(start_date, end_date)
        gross_wages = 0.0
        employer_taxes = 0.0
        benefits = 0.0

        for p in payrolls:
            totals = p.get("totals", {})
            gross_wages += float(totals.get("gross_pay", 0))
            employer_taxes += float(totals.get("employer_taxes", 0))
            benefits += float(totals.get("benefits", 0))

        return {
            "gross_wages": gross_wages,
            "employer_taxes": employer_taxes,
            "benefits": benefits,
            "total_employer_cost": gross_wages + employer_taxes + benefits,
        }

    def employees_by_department(self) -> dict[str, list[dict]]:
        """
        Employees grouped by department — use to allocate wages to P&L buckets:
          Engineering → COGS (or R&D)
          Customer Success → COGS
          Sales → Sales & Marketing
          Marketing → Sales & Marketing
          Finance/Ops/HR → G&A
        """
        resp = requests.get(
            f"{GUSTO_BASE_URL}/v1/companies/{config.GUSTO_COMPANY_ID}/employees",
            headers=self._headers(),
            params={"include": "jobs"},
            timeout=20,
        )
        resp.raise_for_status()
        employees = resp.json()

        by_dept: dict[str, list] = {}
        for emp in employees:
            dept = emp.get("department", "Unassigned")
            by_dept.setdefault(dept, []).append(emp)
        return by_dept
