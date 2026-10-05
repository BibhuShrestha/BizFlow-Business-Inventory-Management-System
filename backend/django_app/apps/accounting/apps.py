"""Django AppConfig for the 'accounting' application.

Expenses, chart of accounts, and journal entries
"""
from django.apps import AppConfig


class AccountingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounting"
    label = "accounting"
    verbose_name = "Expenses, chart of accounts, and journal entries"

    def ready(self):
        # Import signal handlers when the app is fully loaded.
        # (Signals will be registered in Part 3 onwards.)
        pass
