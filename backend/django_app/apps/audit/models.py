"""
Audit models: AuditLog, Notification, EmailLog, ExportLog.
"""
from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """System activity and security audit trail."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
    )
    module = models.CharField(max_length=128)
    action = models.CharField(max_length=128)
    record_type = models.CharField(max_length=64, blank=True, default="")
    record_id = models.IntegerField(null=True, blank=True)
    description = models.TextField(blank=True, default="")
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)
    ip_address = models.CharField(max_length=64, blank=True, default="")
    user_agent = models.CharField(max_length=255, blank=True, default="")
    success = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_logs"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.module} - {self.action} at {self.created_at}"


class Notification(models.Model):
    """In-app notifications for users."""

    PRIORITY_CRITICAL = "critical"
    PRIORITY_HIGH = "high"
    PRIORITY_NORMAL = "normal"
    PRIORITY_INFO = "info"
    PRIORITY_CHOICES = [
        (PRIORITY_CRITICAL, "Critical"),
        (PRIORITY_HIGH, "High"),
        (PRIORITY_NORMAL, "Normal"),
        (PRIORITY_INFO, "Informational"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    company = models.ForeignKey(
        "companies.Company",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="notifications",
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=64, default="general", db_index=True)
    priority = models.CharField(max_length=32, choices=PRIORITY_CHOICES, default=PRIORITY_NORMAL, db_index=True)
    module = models.CharField(max_length=64, blank=True, default="general", db_index=True)
    record_id = models.IntegerField(null=True, blank=True)
    dedup_key = models.CharField(max_length=255, blank=True, default="", db_index=True)
    link = models.CharField(max_length=255, blank=True, default="")
    is_popup = models.BooleanField(default=False)
    popup_dismissed = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"[{self.priority.upper()}] {self.title} -> {self.user.email}"

    @property
    def badge_class(self) -> str:
        mapping = {
            "critical": "badge-danger",
            "high": "badge-warning",
            "normal": "badge-info",
            "info": "badge-success",
        }
        return mapping.get(self.priority, "badge-info")


class NotificationPreference(models.Model):
    """User preferences for business alerts, notifications, and optional SMS."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_preferences",
    )
    # Stock preferences
    notify_low_stock = models.BooleanField(default=True)
    notify_critical_stock = models.BooleanField(default=True)
    notify_out_of_stock = models.BooleanField(default=True)
    notify_stock_received = models.BooleanField(default=True)
    notify_stock_restored = models.BooleanField(default=True)
    # Payment preferences
    notify_payment_due = models.BooleanField(default=True)
    notify_payment_overdue = models.BooleanField(default=True)
    # Cheque preferences
    notify_cheque_due_soon = models.BooleanField(default=True)
    notify_cheque_due_today = models.BooleanField(default=True)
    notify_cheque_overdue = models.BooleanField(default=True)
    # Receivables & Payables preferences
    notify_receivable_due = models.BooleanField(default=True)
    notify_receivable_overdue = models.BooleanField(default=True)
    notify_payable_due = models.BooleanField(default=True)
    notify_payable_overdue = models.BooleanField(default=True)
    # SMS & Popup channels
    sms_enabled = models.BooleanField(default=False)
    sms_phone_number = models.CharField(max_length=32, blank=True, default="")
    popup_enabled = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "notification_preferences"

    def __str__(self) -> str:
        return f"Notification Preferences ({self.user.email})"


class SMSLog(models.Model):
    """Audit log of dispatched SMS messages with cost-control and delivery tracking."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="sms_logs",
    )
    recipient = models.CharField(max_length=32, db_index=True)
    message = models.TextField()
    notification_type = models.CharField(max_length=64, default="general")
    status = models.CharField(max_length=32, default="Sent", db_index=True)
    provider = models.CharField(max_length=64, default="mock")
    dedup_key = models.CharField(max_length=255, blank=True, default="", db_index=True)
    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "sms_logs"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"SMS to {self.recipient} [{self.status}] at {self.created_at}"


class EmailLog(models.Model):
    """Log of dispatched transactional emails."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="email_logs",
    )
    recipient = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)
    message = models.TextField()
    status = models.CharField(max_length=64, default="Sent")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "email_logs"
        ordering = ["-created_at"]


class ExportLog(models.Model):
    """Audit of report exports (Excel, PDF, CSV)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="export_logs",
    )
    module = models.CharField(max_length=128)
    format = models.CharField(max_length=32)
    filters = models.JSONField(null=True, blank=True)
    record_count = models.IntegerField(default=0)
    success = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "export_logs"
        ordering = ["-created_at"]