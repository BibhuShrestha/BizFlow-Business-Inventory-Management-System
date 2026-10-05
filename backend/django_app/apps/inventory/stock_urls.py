"""URL patterns for stock ledger and adjustments."""
from django.urls import path
from apps.inventory import stock_views as views

app_name = "stock"

urlpatterns = [
    path("", views.stock_movements, name="movements"),
    path("movements/", views.stock_movements, name="movements_alias"),
    path("adjust/", views.stock_adjust, name="adjust"),
]
