"""Provider adapter interfaces. Add provider credentials and OAuth callback handling before production use."""
class AccountingProvider:
    provider_code = "BASE"
    def authorize_url(self, state): raise NotImplementedError
    def exchange_code(self, code, redirect_uri): raise NotImplementedError
    def refresh(self, refresh_token): raise NotImplementedError
    def pull_customers(self, connection): raise NotImplementedError
    def pull_invoices(self, connection, since=None): raise NotImplementedError
    def push_invoice(self, connection, invoice): raise NotImplementedError

class QuickBooksAdapter(AccountingProvider): provider_code="QUICKBOOKS"
class ZohoBooksAdapter(AccountingProvider): provider_code="ZOHO"
class TallyAdapter(AccountingProvider): provider_code="TALLY"
class XeroAdapter(AccountingProvider): provider_code="XERO"
class SageAdapter(AccountingProvider): provider_code="SAGE"
class FreshBooksAdapter(AccountingProvider): provider_code="FRESHBOOKS"

PROVIDERS = {c.provider_code:c for c in [QuickBooksAdapter,ZohoBooksAdapter,TallyAdapter,XeroAdapter,SageAdapter,FreshBooksAdapter]}
