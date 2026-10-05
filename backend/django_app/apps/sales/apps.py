"""Django AppConfig for the 'sales' application.

Customers, sales invoices, and sale line items
"""
from django.apps import AppConfig


class SalesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.sales"
    label = "sales"
    verbose_name = "Customers, sales invoices, and sale line items"

    def ready(self):
        # Import signal handlers when the app is fully loaded.
        # (Signals will be registered in Part 3 onwards.)
        pass
