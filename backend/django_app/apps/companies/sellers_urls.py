"""URL patterns for sellers."""
from django.urls import path
from apps.companies import sellers_views as views

app_name = "sellers"

urlpatterns = [
    path("", views.seller_list, name="list"),
    path("new/", views.seller_create, name="create"),
    path("<int:pk>/edit/", views.seller_edit, name="edit"),
    path("<int:pk>/delete/", views.seller_delete, name="delete"),
    path("export/csv/", views.export_sellers_csv, name="export_csv"),
    path("export/excel/", views.export_sellers_excel, name="export_excel"),
]
