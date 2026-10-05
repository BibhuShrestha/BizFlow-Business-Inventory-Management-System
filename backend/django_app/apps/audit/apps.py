"""Django AppConfig for the 'audit' application.

Audit logs, login history, email logs, export logs, notifications
"""
from django.apps import AppConfig


class AuditConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.audit"
    label = "audit"
    verbose_name = "Audit logs, login history, email logs, export logs, notifications"

    def ready(self):
        # Import signal handlers when the app is fully loaded.
        # (Signals will be registered in Part 3 onwards.)
        pass
