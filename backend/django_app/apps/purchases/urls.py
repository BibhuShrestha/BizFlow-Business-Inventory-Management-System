"""URL patterns for purchases."""
from django.urls import path
from apps.purchases import views

app_name = "purchases"

urlpatterns = [
    path("", views.purchase_list, name="list"),
    path("new/", views.purchase_create, name="create"),
    path("<int:pk>/", views.purchase_detail, name="detail"),
    path("<int:pk>/delete/", views.purchase_delete, name="delete"),
    path("<int:pk>/cancel/", views.purchase_delete, name="cancel"),
    path("export/csv/", views.export_csv, name="export_csv"),
    path("export/excel/", views.export_excel, name="export_excel"),
]
