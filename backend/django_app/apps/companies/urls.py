"""URL patterns for companies application."""
from django.urls import path
from apps.companies import views

app_name = "companies"

urlpatterns = [
    path("", views.company_list, name="list"),
    path("new/", views.company_create, name="create"),
    path("<int:pk>/edit/", views.company_edit, name="edit"),
    path("<int:pk>/delete/", views.company_delete, name="delete"),
    path("<int:pk>/switch/", views.set_active_company, name="switch"),
    path("<int:pk>/set-active/", views.set_active_company, name="set_active"),
    path("export/csv/", views.export_csv, name="export_csv"),
    path("export/excel/", views.export_excel, name="export_excel"),
]
