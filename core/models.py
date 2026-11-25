from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

class Organization(models.Model):
    name = models.CharField(max_length=180)
    legal_name = models.CharField(max_length=180, blank=True)
    country = models.CharField(max_length=2, default="IN")
    currency = models.CharField(max_length=3, default="INR")
    tax_id = models.CharField(max_length=40, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.name

class Membership(models.Model):
    ROLE = [("OWNER","Owner"),("ADMIN","Admin"),("ACCOUNTANT","Accountant"),("VIEWER","Viewer")]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE, default="OWNER")
    class Meta: unique_together = ("user","organization")

class Contact(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    kind = models.CharField(max_length=10, choices=[("CUSTOMER","Customer"),("VENDOR","Vendor")])
    name = models.CharField(max_length=180)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    tax_id = models.CharField(max_length=40, blank=True)
    address = models.TextField(blank=True)
    opening_balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    def __str__(self): return self.name

class Account(models.Model):
    TYPES = [("ASSET","Asset"),("LIABILITY","Liability"),("EQUITY","Equity"),("INCOME","Income"),("EXPENSE","Expense")]
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=120)
    account_type = models.CharField(max_length=12, choices=TYPES)
    is_control = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    class Meta: unique_together = ("organization","code")
    def __str__(self): return f"{self.code} - {self.name}"

class JournalEntry(models.Model):
    STATUS = [("DRAFT","Draft"),("POSTED","Posted"),("VOID","Void")]
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    entry_number = models.CharField(max_length=30)
    date = models.DateField(default=timezone.localdate)
    memo = models.CharField(max_length=240, blank=True)
    status = models.CharField(max_length=10, choices=STATUS, default="DRAFT")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: unique_together = ("organization","entry_number")
    @property
    def debit_total(self): return sum((x.debit for x in self.lines.all()), Decimal("0"))
    @property
    def credit_total(self): return sum((x.credit for x in self.lines.all()), Decimal("0"))
    def clean(self):
        if self.pk and self.status == "POSTED" and self.lines.count() < 2:
            raise ValidationError("A posted journal requires at least two lines.")

class JournalLine(models.Model):
    entry = models.ForeignKey(JournalEntry, related_name="lines", on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.PROTECT)
    description = models.CharField(max_length=200, blank=True)
    debit = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    def clean(self):
        if self.debit < 0 or self.credit < 0 or (self.debit and self.credit):
            raise ValidationError("Enter a non-negative debit OR credit, not both.")
        if self.account_id and self.entry_id and self.account.organization_id != self.entry.organization_id:
            raise ValidationError("Account and journal must belong to the same organization.")

class Document(models.Model):
    TYPES = [("INVOICE","Sales invoice"),("BILL","Vendor bill"),("EXPENSE","Expense"),("RECEIPT","Receipt"),("PAYMENT","Payment")]
    STATUS = [("DRAFT","Draft"),("APPROVED","Approved"),("POSTED","Posted"),("VOID","Void")]
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    doc_type = models.CharField(max_length=12, choices=TYPES)
    number = models.CharField(max_length=40)
    contact = models.ForeignKey(Contact, null=True, blank=True, on_delete=models.PROTECT)
    date = models.DateField(default=timezone.localdate)
    due_date = models.DateField(null=True, blank=True)
    description = models.CharField(max_length=240, blank=True)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=STATUS, default="DRAFT")
    journal = models.ForeignKey(JournalEntry, null=True, blank=True, on_delete=models.SET_NULL)
    class Meta: unique_together = ("organization","doc_type","number")
    def save(self,*args,**kwargs):
        self.total = self.subtotal + self.tax_amount
        super().save(*args,**kwargs)

class DocumentLine(models.Model):
    document = models.ForeignKey(Document, related_name="lines", on_delete=models.CASCADE)
    description = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=12, decimal_places=3, default=1)
    unit_price = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_rate = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    @property
    def amount(self): return self.quantity * self.unit_price

class BankAccount(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    institution = models.CharField(max_length=120, blank=True)
    account_last4 = models.CharField(max_length=4, blank=True)
    currency = models.CharField(max_length=3, default="INR")
    opening_balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    active = models.BooleanField(default=True)

class BankTransaction(models.Model):
    bank_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.localdate)
    description = models.CharField(max_length=240)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    reference = models.CharField(max_length=100, blank=True)
    reconciled = models.BooleanField(default=False)

class TaxRate(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    name = models.CharField(max_length=80)
    rate = models.DecimalField(max_digits=6, decimal_places=2)
    tax_type = models.CharField(max_length=30, default="GST")
    active = models.BooleanField(default=True)

class Product(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    sku = models.CharField(max_length=60)
    name = models.CharField(max_length=160)
    unit = models.CharField(max_length=20, default="unit")
    sales_price = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    purchase_price = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    stock_qty = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    reorder_level = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    class Meta: unique_together = ("organization","sku")

class Budget(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    period_start = models.DateField()
    period_end = models.DateField()
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    account = models.ForeignKey(Account, on_delete=models.PROTECT)

class IntegrationConnection(models.Model):
    PROVIDERS = [("QUICKBOOKS","QuickBooks Online"),("ZOHO","Zoho Books"),("TALLY","TallyPrime"),("XERO","Xero"),("SAGE","Sage"),("FRESHBOOKS","FreshBooks")]
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    provider = models.CharField(max_length=20, choices=PROVIDERS)
    environment = models.CharField(max_length=10, choices=[("SANDBOX","Sandbox"),("PRODUCTION","Production")], default="SANDBOX")
    external_company_id = models.CharField(max_length=120, blank=True)
    access_token = models.TextField(blank=True)
    refresh_token = models.TextField(blank=True)
    token_expires_at = models.DateTimeField(null=True, blank=True)
    connected = models.BooleanField(default=False)
    last_sync_at = models.DateTimeField(null=True, blank=True)
    # Production deployments should encrypt credentials using a managed KMS/secret store.
    class Meta: unique_together = ("organization","provider")

class SyncLog(models.Model):
    connection = models.ForeignKey(IntegrationConnection, on_delete=models.CASCADE)
    direction = models.CharField(max_length=10, choices=[("IMPORT","Import"),("EXPORT","Export")])
    entity = models.CharField(max_length=40)
    status = models.CharField(max_length=12, choices=[("SUCCESS","Success"),("FAILED","Failed"),("PENDING","Pending")], default="PENDING")
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=80)
    code = models.SlugField(unique=True)
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_users = models.PositiveIntegerField(default=1)
    active = models.BooleanField(default=True)

class Subscription(models.Model):
    organization = models.OneToOneField(Organization, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    status = models.CharField(max_length=12, choices=[("TRIAL","Trial"),("ACTIVE","Active"),("PAST_DUE","Past due"),("CANCELLED","Cancelled")], default="TRIAL")
    started_at = models.DateField(default=timezone.localdate)
    renews_at = models.DateField(null=True, blank=True)

class AuditEvent(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=100)
    object_type = models.CharField(max_length=80, blank=True)
    object_id = models.CharField(max_length=80, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
