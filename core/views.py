from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import *
from .forms import *
from .services import post_journal

def current_org(request):
    org_id = request.session.get("organization_id")
    if org_id:
        org = Organization.objects.filter(pk=org_id, membership_set__user=request.user).first()
        if org: return org
    membership = Membership.objects.filter(user=request.user).select_related("organization").first()
    return membership.organization if membership else None

@login_required
def dashboard(request):
    org = current_org(request)
    if not org: return redirect("organization_create")
    request.session["organization_id"] = org.pk
    docs = Document.objects.filter(organization=org)
    posted = JournalEntry.objects.filter(organization=org,status="POSTED")
    context = {"org":org,"sales":docs.filter(doc_type="INVOICE").aggregate(v=Sum("total"))["v"] or 0,
      "purchases":docs.filter(doc_type="BILL").aggregate(v=Sum("total"))["v"] or 0,
      "expenses":docs.filter(doc_type="EXPENSE").aggregate(v=Sum("total"))["v"] or 0,
      "journals":posted.count(),"recent_docs":docs.order_by("-date","-id")[:8],
      "bank_accounts":BankAccount.objects.filter(organization=org).count(),
      "contacts":Contact.objects.filter(organization=org).count()}
    return render(request,"core/dashboard.html",context)

@login_required
def organization_create(request):
    if request.method=="POST":
        form=OrganizationForm(request.POST)
        if form.is_valid():
            org=form.save(); Membership.objects.create(user=request.user,organization=org,role="OWNER")
            request.session["organization_id"]=org.pk
            seed_accounts(org)
            messages.success(request,"Company created. Your starter chart of accounts is ready.")
            return redirect("dashboard")
    else: form=OrganizationForm()
    return render(request,"core/form.html",{"form":form,"title":"Create company"})

def seed_accounts(org):
    defaults=[("1000","Cash","ASSET"),("1100","Bank","ASSET"),("1200","Accounts receivable","ASSET"),
    ("1500","Inventory","ASSET"),("2000","Accounts payable","LIABILITY"),("2100","GST payable","LIABILITY"),
    ("3000","Owner equity","EQUITY"),("4000","Sales revenue","INCOME"),("5000","Cost of goods sold","EXPENSE"),
    ("6000","Operating expenses","EXPENSE")]
    for code,name,typ in defaults: Account.objects.get_or_create(organization=org,code=code,defaults={"name":name,"account_type":typ})

@login_required
def list_view(request, model_name):
    org=current_org(request)
    if not org: return redirect("organization_create")
    models={"contacts":Contact,"accounts":Account,"documents":Document,"banking":BankAccount,"products":Product,
            "journals":JournalEntry,"integrations":IntegrationConnection,"budgets":Budget}
    model=models.get(model_name)
    if not model: return redirect("dashboard")
    qs=model.objects.filter(organization=org).order_by("-id")
    return render(request,"core/list.html",{"title":model_name.replace("_"," ").title(),"items":qs,"kind":model_name})

@login_required
def create_view(request, model_name):
    org=current_org(request)
    if not org: return redirect("organization_create")
    forms={"contacts":ContactForm,"documents":DocumentForm,"banking":BankAccountForm,"products":ProductForm,"integrations":IntegrationForm,"accounts":AccountForm}
    form_cls=forms.get(model_name)
    if not form_cls: return redirect("dashboard")
    form=form_cls(request.POST or None)
    if request.method=="POST" and form.is_valid():
        obj=form.save(commit=False); obj.organization=org
        if model_name=="documents" and obj.contact and obj.contact.organization_id!=org.pk:
            form.add_error("contact","Select a contact in this company.")
        else:
            obj.save(); messages.success(request,"Record saved."); return redirect("list",model_name=model_name)
    return render(request,"core/form.html",{"form":form,"title":"New "+model_name[:-1]})

@login_required
def journal_create(request):
    org=current_org(request)
    if not org: return redirect("organization_create")
    accounts=Account.objects.filter(organization=org,active=True)
    if request.method=="POST":
        entry=JournalEntry.objects.create(organization=org,entry_number=request.POST.get("entry_number") or f"JE-{timezone.now():%Y%m%d%H%M%S}",date=request.POST.get("date") or timezone.localdate(),memo=request.POST.get("memo",""),created_by=request.user)
        try:
            for i in range(1,5):
                aid=request.POST.get(f"account_{i}")
                if aid:
                    JournalLine.objects.create(entry=entry,account=get_object_or_404(accounts,pk=aid),description=request.POST.get(f"description_{i}",""),
                      debit=Decimal(request.POST.get(f"debit_{i}") or "0"),credit=Decimal(request.POST.get(f"credit_{i}") or "0"))
            post_journal(entry,request.user)
            messages.success(request,"Balanced journal posted.")
            return redirect("list",model_name="journals")
        except Exception as exc:
            entry.delete(); messages.error(request,f"Journal not posted: {exc}")
    return render(request,"core/journal_form.html",{"accounts":accounts})

@login_required
def reports(request):
    org=current_org(request)
    if not org: return redirect("organization_create")
    lines=JournalLine.objects.filter(entry__organization=org,entry__status="POSTED").values("account__code","account__name","account__account_type").annotate(debits=Sum("debit"),credits=Sum("credit")).order_by("account__code")
    return render(request,"core/reports.html",{"rows":lines,"org":org})
