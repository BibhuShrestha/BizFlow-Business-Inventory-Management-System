"""URL patterns for sales invoices."""
from django.urls import path
from apps.sales import views

app_name = "sales"

urlpatterns = [
    path("", views.sale_list, name="list"),
    path("new/", views.sale_create, name="create"),
    path("<int:pk>/", views.sale_detail, name="detail"),
    path("<int:pk>/delete/", views.sale_delete, name="delete"),
    path("<int:pk>/cancel/", views.sale_delete, name="cancel"),
    path("export/csv/", views.export_csv, name="export_csv"),
    path("export/excel/", views.export_excel, name="export_excel"),
]
