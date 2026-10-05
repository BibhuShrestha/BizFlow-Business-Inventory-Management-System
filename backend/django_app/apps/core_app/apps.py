"""Django AppConfig for the 'core_app' application.

Dashboard, landing page, health-check, and shared utilities
"""
from django.apps import AppConfig


class CoreAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core_app"
    label = "core"
    verbose_name = "Dashboard, landing page, health-check, and shared utilities"

    def ready(self):
        # Import signal handlers when the app is fully loaded.
        # (Signals will be registered in Part 3 onwards.)
        pass
