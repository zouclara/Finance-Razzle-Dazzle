# Finance-Razzle-Dazzle

API-first financial reporting dashboard for B2B SaaS — Income Statement, Balance Sheet, and Cash Flow Statement, powered by your existing tool stack.

---

## Architecture

```
QuickBooks (GL)  ──┐
Stripe           ──┤
Mercury          ──┤─→ statements/ ─→ dashboard/app.py (Streamlit)
Brex             ──┤
Gusto            ──┤
HubSpot          ──┤
Google Sheets    ──┘
```

**QuickBooks is the source of truth.** The three statements pull directly from the QBO Reports API. The other integrations enrich and cross-check those numbers with real-time data.

---

## Getting Started

### 1. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure credentials

```bash
cp .env.example .env
# Fill in your API credentials — see the table below
```

### 3. Run the dashboard

```bash
streamlit run dashboard/app.py
```

The dashboard starts in **demo mode** (`USE_DEMO_DATA=true`) showing realistic sample data for a ~$2M ARR SaaS company. Set `USE_DEMO_DATA=false` after you've added credentials.

---

## API Credentials Checklist

### QuickBooks (required — source of truth for all 3 statements)
| Credential | Where to get it |
|---|---|
| `QB_CLIENT_ID` | developer.intuit.com → My Apps → Keys & OAuth |
| `QB_CLIENT_SECRET` | Same location |
| `QB_REALM_ID` | Your QBO company ID (visible in QBO URL after `/app/`) |
| `QB_ACCESS_TOKEN` | Run OAuth flow, then `python scripts/refresh_qb_token.py` |
| `QB_REFRESH_TOKEN` | Returned during OAuth flow |

**OAuth scopes:** `com.intuit.quickbooks.accounting`

> Access tokens expire every 1 hour. Refresh tokens last 100 days.
> Set up a cron job: `0 * * * * python /path/to/scripts/refresh_qb_token.py`

---

### Stripe (revenue enrichment + MRR/ARR)
| Credential | Where to get it |
|---|---|
| `STRIPE_SECRET_KEY` | dashboard.stripe.com → Developers → API keys |

Use a **Restricted Key** (not the secret key) with read-only access to:
`charges`, `subscriptions`, `invoices`, `balance`, `payouts`, `customers`, `refunds`

---

### Mercury (live cash balance + burn rate)
| Credential | Where to get it |
|---|---|
| `MERCURY_API_TOKEN` | app.mercury.com → Settings → API |

---

### Brex (corporate card balance + expense categories)
| Credential | Where to get it |
|---|---|
| `BREX_API_TOKEN` | dashboard.brex.com → Settings → Developer |

**Scopes:** `transactions.readonly`, `accounts.readonly`, `expenses.readonly`

---

### Gusto (payroll costs by department)
| Credential | Where to get it |
|---|---|
| `GUSTO_CLIENT_ID` | dev.gusto.com → OAuth Apps |
| `GUSTO_CLIENT_SECRET` | Same location |
| `GUSTO_COMPANY_ID` | Gusto dashboard URL or API response |
| `GUSTO_ACCESS_TOKEN` | OAuth flow |

---

### HubSpot (pipeline value + closed-won revenue)
| Credential | Where to get it |
|---|---|
| `HUBSPOT_ACCESS_TOKEN` | app.hubspot.com → Settings → Integrations → Private Apps |

**Scopes:** `crm.objects.deals.read`, `crm.objects.contacts.read`

---

### Google Sheets (manual journal entries / budget model)
| Credential | Where to get it |
|---|---|
| `GOOGLE_SERVICE_ACCOUNT_JSON` | console.cloud.google.com → IAM → Service Accounts → Create Key |
| `GOOGLE_SHEETS_SPREADSHEET_ID` | From your Sheets URL: `docs.google.com/spreadsheets/d/{ID}/` |

Enable the **Google Sheets API** in your GCP project, then share the spreadsheet with the service account email.

---

## Data Source → Statement Mapping

| Statement | Primary | Enrichment |
|---|---|---|
| **Income Statement** | QuickBooks P&L Report | Stripe (MRR/ARR), Gusto (payroll by dept), Brex (card expenses) |
| **Balance Sheet** | QuickBooks Balance Sheet | Mercury (live cash), Stripe (AR/deferred revenue), Brex (card balance) |
| **Cash Flow** | QuickBooks Cash Flow | Mercury (bank transactions), Stripe (payout timing), Gusto (payroll outflows) |

---

## Project Structure

```
Finance-Razzle-Dazzle/
├── config.py                    # All env vars in one place
├── requirements.txt
├── .env.example                 # Template — copy to .env
├── connectors/
│   ├── quickbooks.py            # QBO Reports API (P&L, BS, CF)
│   ├── stripe_connector.py      # Revenue, MRR, payouts
│   ├── mercury.py               # Banking, cash, burn
│   ├── brex.py                  # Card spend, balances
│   ├── gusto.py                 # Payroll by department
│   ├── hubspot.py               # Pipeline, closed-won
│   └── google_sheets.py        # Manual entries, budget
├── statements/
│   ├── income_statement.py      # Builds P&L from QBO + enrichment
│   ├── balance_sheet.py         # Builds BS from QBO + Mercury
│   ├── cash_flow.py             # Builds CF from QBO + Mercury
│   └── demo_data.py             # Realistic sample data (USE_DEMO_DATA=true)
├── dashboard/
│   └── app.py                   # Streamlit dashboard
└── scripts/
    └── refresh_qb_token.py      # Rotate QB OAuth tokens
```

---

## SaaS-Specific Considerations

### Revenue Recognition
- Stripe charges when cash is collected; QBO P&L shows recognized revenue
- For annual plans, Stripe will show full payment but QBO will spread it over 12 months
- Deferred Revenue on the Balance Sheet = unearned annual plan payments

### Payroll Allocation (P&L buckets)
Gusto gives you headcount but not GL accounts. Map departments manually:

| Gusto Department | P&L Line |
|---|---|
| Engineering | R&D or COGS (if customer-facing) |
| Customer Success | COGS |
| Sales | Sales & Marketing |
| Marketing | Sales & Marketing |
| Finance / HR / Legal | G&A |

### Burn Rate
- Calculated from Mercury transactions (most accurate) or QBO cash flow
- Net burn = cash out - cash in (operating only, exclude fundraising)
- Runway = ending cash / average monthly burn

### CAC Calculation (add to dashboard next)
```
CAC = (Sales payroll + Marketing payroll + Advertising) / New customers
    = (Gusto[Sales+Mktg] + Brex[Ads]) / HubSpot[closed_won_count]
```