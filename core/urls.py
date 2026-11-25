from django.urls import path
from . import views
urlpatterns=[
 path("",views.dashboard,name="dashboard"), path("company/new/",views.organization_create,name="organization_create"),
 path("new/journal/",views.journal_create,name="journal_create"), path("reports/",views.reports,name="reports"),
 path("<str:model_name>/",views.list_view,name="list"), path("<str:model_name>/new/",views.create_view,name="create"),
]
