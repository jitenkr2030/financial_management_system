from django.contrib import admin
from .models import *
for model in [Organization,Membership,Contact,Account,JournalEntry,JournalLine,Document,DocumentLine,BankAccount,BankTransaction,TaxRate,Product,Budget,IntegrationConnection,SyncLog,SubscriptionPlan,Subscription,AuditEvent]:
    admin.site.register(model)
