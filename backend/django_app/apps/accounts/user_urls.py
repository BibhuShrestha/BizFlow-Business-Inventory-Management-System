"""URL patterns for administrative user management."""
from django.urls import path
from apps.accounts import user_views as views

app_name = "users"

urlpatterns = [
    path("", views.user_list, name="list"),
    path("new/", views.user_create, name="create"),
    path("create/", views.user_create, name="create_alias"),
    path("<int:pk>/edit/", views.user_edit, name="edit"),
    path("<int:pk>/delete/", views.user_delete, name="delete"),
]
