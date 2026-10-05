"""Django AppConfig for the 'reports' application.

Business summary and day-book reports (no models)
"""
from django.apps import AppConfig


class ReportsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.reports"
    label = "reports"
    verbose_name = "Business summary and day-book reports (no models)"

    def ready(self):
        # Import signal handlers when the app is fully loaded.
        # (Signals will be registered in Part 3 onwards.)
        pass
