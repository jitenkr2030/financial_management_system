from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import JournalEntry, JournalLine, AuditEvent

@transaction.atomic
def post_journal(entry, user=None):
    entry = JournalEntry.objects.select_for_update().get(pk=entry.pk)
    if entry.status == "POSTED": return entry
    lines = list(entry.lines.select_related("account"))
    if len(lines) < 2: raise ValidationError("A journal must contain at least two lines.")
    debit = sum((x.debit for x in lines), Decimal("0"))
    credit = sum((x.credit for x in lines), Decimal("0"))
    if debit <= 0 or debit != credit: raise ValidationError("Journal debits and credits must balance and be greater than zero.")
    if any(x.account.organization_id != entry.organization_id for x in lines):
        raise ValidationError("Cross-organization account line is not permitted.")
    entry.status = "POSTED"; entry.save(update_fields=["status"])
    AuditEvent.objects.create(organization=entry.organization,user=user,action="journal.posted",object_type="JournalEntry",object_id=str(entry.pk))
    return entry
