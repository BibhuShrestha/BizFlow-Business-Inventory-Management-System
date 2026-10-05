"""Django AppConfig for the 'accounts' application.

User accounts, roles, authentication tokens
"""
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    label = "accounts"
    verbose_name = "User accounts, roles, authentication tokens"

    def ready(self):
        # Import signal handlers when the app is fully loaded.
        # (Signals will be registered in Part 3 onwards.)
        pass
