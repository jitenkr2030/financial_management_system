# FinCore — Django Financial Management System

A runnable, modular foundation covering the six requested delivery phases. It includes a functioning Django application, company-level data ownership, double-entry journal posting validation, sales/purchase/expense document records, contacts, chart of accounts, bank accounts, inventory products, budgets, tax-rate records, integration connection registry, sync logs, subscriptions, audit events, admin, dashboards, reports and tests.

## Important scope / production notice
This ZIP is a runnable foundation, not a certified accounting package and not a fully approved live connector for every provider. QuickBooks, Zoho Books, TallyPrime, Xero, Sage and FreshBooks have adapter interfaces and connection registry, but live OAuth callbacks, provider-specific payload mapping, token encryption, webhook verification, retry queues and marketplace certification require provider credentials and implementation/testing against each provider's current API. GST returns/e-invoice/e-way bill, payroll statutory filing, bank feeds, payment collection and country-specific compliance are not represented as completed regulatory integrations. Have an India-qualified accountant and security reviewer validate accounting/tax rules before production use.

## Requirements
- Python 3.11+
- PostgreSQL 14+ recommended; SQLite is used by default for quick local startup.

## Windows / WSL installation
```bash
cd /mnt/c/Users/Lenovo
unzip financial_management_system.zip
cd financial_management_system
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate --run-syncdb
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
```
Open http://127.0.0.1:8000/ and sign in. Create a company on first login. The first company receives a starter chart of accounts.

## PostgreSQL
Create a database and user, then set in `.env`:
```env
DATABASE_URL=postgresql://fincore_user:strong_password@localhost:5432/fincore
DEBUG=False
SECRET_KEY=use-a-long-random-secret
ALLOWED_HOSTS=your-domain.com
```
Then run:
```bash
python manage.py migrate --run-syncdb
python manage.py createsuperuser
```

## Core workflows
1. Create company; a default chart of accounts is seeded.
2. Add customers/vendors under Customers & vendors.
3. Add sales invoices, vendor bills, expenses, receipts and payments as financial documents.
4. Create a journal using New journal. Posting is allowed only when total debits equal total credits and there are at least two lines.
5. Review posted ledger totals under Financial reports.
6. Configure bank accounts, products, tax rates, budgets and integration connection records through application screens/admin.

## Phase map
- V1: accounting foundation, contacts, documents, journal posting, bank accounts and trial-balance view.
- V2: organization/membership structure, tax-rate and GST-ready fields, products/inventory quantities, budgets, currency/country settings and dashboard analytics.
- V3: QuickBooks, Zoho Books and Tally adapter contracts plus connection/sync-log data models.
- V4: Xero, Sage and FreshBooks adapter contracts.
- V5: audit events and integration service extension points; connect an LLM provider and forecasting pipeline only after data governance and review controls are defined.
- V6: subscription plans/subscriptions and tenant membership foundation. Add a payment gateway, invoices, dunning, usage metering, tenant isolation review and regional hosting before commercial SaaS launch.

## Security checklist before deployment
- Set DEBUG=False, secure SECRET_KEY and ALLOWED_HOSTS.
- Encrypt provider tokens at rest with KMS/secret management; never expose tokens in admin.
- Add organization-scoped authorization to every API, view, export and background job.
- Add database backups, restore tests, audit retention, HTTPS, rate limits and monitoring.
- Add approval policies, immutable posted-ledger correction via reversal entries, period locks and idempotency keys.
- Run the test suite and external penetration/security review.
