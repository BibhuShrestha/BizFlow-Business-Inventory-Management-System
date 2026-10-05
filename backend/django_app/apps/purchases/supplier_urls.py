"""URL patterns for supplier management."""
from django.urls import path
from apps.purchases import supplier_views as views

app_name = "suppliers"

urlpatterns = [
    path("", views.supplier_list, name="list"),
    path("new/", views.supplier_create, name="create"),
    path("<int:pk>/", views.supplier_detail, name="detail"),
    path("<int:pk>/edit/", views.supplier_edit, name="edit"),
    path("<int:pk>/delete/", views.supplier_delete, name="delete"),
]
