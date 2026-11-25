from django import forms
from .models import Organization, Contact, Account, JournalEntry, JournalLine, Document, BankAccount, Product, IntegrationConnection
class OrganizationForm(forms.ModelForm):
    class Meta: model=Organization; fields=["name","legal_name","country","currency","tax_id"]
class ContactForm(forms.ModelForm):
    class Meta: model=Contact; fields=["kind","name","email","phone","tax_id","address","opening_balance"]
class AccountForm(forms.ModelForm):
    class Meta: model=Account; fields=["code","name","account_type","is_control","active"]
class DocumentForm(forms.ModelForm):
    class Meta: model=Document; fields=["doc_type","number","contact","date","due_date","description","subtotal","tax_amount","status"]
class BankAccountForm(forms.ModelForm):
    class Meta: model=BankAccount; fields=["name","institution","account_last4","currency","opening_balance"]
class ProductForm(forms.ModelForm):
    class Meta: model=Product; fields=["sku","name","unit","sales_price","purchase_price","stock_qty","reorder_level"]
class IntegrationForm(forms.ModelForm):
    class Meta: model=IntegrationConnection; fields=["provider","environment","external_company_id"]
