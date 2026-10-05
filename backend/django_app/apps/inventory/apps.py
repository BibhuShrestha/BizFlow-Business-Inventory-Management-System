"""Django AppConfig for the 'inventory' application.

Products, categories, and stock movements
"""
from django.apps import AppConfig


class InventoryConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.inventory"
    label = "inventory"
    verbose_name = "Products, categories, and stock movements"

    def ready(self):
        # Import signal handlers when the app is fully loaded.
        # (Signals will be registered in Part 3 onwards.)
        pass
