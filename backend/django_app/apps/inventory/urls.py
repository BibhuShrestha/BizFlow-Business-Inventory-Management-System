"""URL patterns for inventory products and categories."""
from django.urls import path
from apps.inventory import views

app_name = "inventory"

urlpatterns = [
    path("", views.product_list, name="product_list"),
    path("new/", views.product_create, name="product_create"),
    path("<int:pk>/edit/", views.product_edit, name="product_edit"),
    path("<int:pk>/delete/", views.product_delete, name="product_delete"),
    path("export/csv/", views.export_csv, name="export_csv"),
    path("export/excel/", views.export_excel, name="export_excel"),
    path("sample-template/", views.sample_template, name="sample_template"),
    path("template/", views.sample_template, name="template"),
    path("import/", views.import_products, name="import_products"),
    path("import-alias/", views.import_products, name="import"),
    path("categories/", views.category_list, name="category_list"),
    path("categories/new/", views.category_create, name="category_create"),
    path("categories/<int:pk>/edit/", views.category_edit, name="category_edit"),
    path("categories/<int:pk>/delete/", views.category_delete, name="category_delete"),
]
