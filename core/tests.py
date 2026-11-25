from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .models import Organization, Account, JournalEntry, JournalLine
from .services import post_journal
class LedgerTests(TestCase):
    def setUp(self):
        self.org=Organization.objects.create(name="Test Co")
        self.cash=Account.objects.create(organization=self.org,code="1000",name="Cash",account_type="ASSET")
        self.capital=Account.objects.create(organization=self.org,code="3000",name="Capital",account_type="EQUITY")
    def test_balanced_journal_posts(self):
        e=JournalEntry.objects.create(organization=self.org,entry_number="JE-1")
        JournalLine.objects.create(entry=e,account=self.cash,debit=Decimal("100"))
        JournalLine.objects.create(entry=e,account=self.capital,credit=Decimal("100"))
        post_journal(e)
        e.refresh_from_db(); self.assertEqual(e.status,"POSTED")
    def test_unbalanced_journal_rejected(self):
        e=JournalEntry.objects.create(organization=self.org,entry_number="JE-2")
        JournalLine.objects.create(entry=e,account=self.cash,debit=Decimal("100"))
        JournalLine.objects.create(entry=e,account=self.capital,credit=Decimal("90"))
        with self.assertRaises(ValidationError): post_journal(e)
