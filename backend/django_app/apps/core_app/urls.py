"""
URL configuration for core_app: Central Import & Export.
"""
from django.urls import path
from apps.core_app import views

app_name = "core_app"

urlpatterns = [
    path("", views.import_export_hub, name="import_export_hub"),
    path("export/", views.export_dataset, name="export_dataset"),
    path("import/", views.import_dataset, name="import_dataset"),
]
