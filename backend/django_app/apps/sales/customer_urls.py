"""URL patterns for customer management."""
from django.urls import path
from apps.sales import customer_views as views

app_name = "customers"

urlpatterns = [
    path("", views.customer_list, name="list"),
    path("new/", views.customer_create, name="create"),
    path("<int:pk>/", views.customer_detail, name="detail"),
    path("<int:pk>/edit/", views.customer_edit, name="edit"),
    path("<int:pk>/delete/", views.customer_delete, name="delete"),
]
