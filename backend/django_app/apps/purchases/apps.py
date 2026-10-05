"""Django AppConfig for the 'purchases' application.

Suppliers, purchase orders, and purchase line items
"""
from django.apps import AppConfig


class PurchasesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.purchases"
    label = "purchases"
    verbose_name = "Suppliers, purchase orders, and purchase line items"

    def ready(self):
        # Import signal handlers when the app is fully loaded.
        # (Signals will be registered in Part 3 onwards.)
        pass
