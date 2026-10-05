"""Django AppConfig for the 'companies' application.

Company profiles and seller representatives
"""
from django.apps import AppConfig


class CompaniesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.companies"
    label = "companies"
    verbose_name = "Company profiles and seller representatives"

    def ready(self):
        # Import signal handlers when the app is fully loaded.
        # (Signals will be registered in Part 3 onwards.)
        pass
