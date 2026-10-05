"""
Credit and Cheque management models.
"""
from decimal import Decimal
from django.conf import settings
from django.db import models
from django.utils import timezone


class Cheque(models.Model):
    """
    Cheque Management for Cheques Given to Suppliers (Payables)
    and Cheques Received from Customers (Receivables).
    """

    TYPE_GIVEN = "GIVEN"
    TYPE_RECEIVED = "RECEIVED"
    TYPE_CHOICES = [
        (TYPE_GIVEN, "Cheque Given (Supplier)"),
        (TYPE_RECEIVED, "Cheque Received (Customer)"),
    ]

    STATUS_PENDING = "PENDING"
    STATUS_CLEARED = "CLEARED"
    STATUS_BOUNCED = "BOUNCED"
    STATUS_CANCELLED = "CANCELLED"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_CLEARED, "Cleared"),
        (STATUS_BOUNCED, "Bounced"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    company = models.ForeignKey(
        "companies.Company",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="cheques",
    )
    cheque_type = models.CharField(
        max_length=16,
        choices=TYPE_CHOICES,
        default=TYPE_RECEIVED,
        db_index=True,
    )
    cheque_number = models.CharField(max_length=64, db_index=True)
    bank_name = models.CharField(max_length=128, db_index=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    cheque_date = models.DateField(db_index=True)

    customer = models.ForeignKey(
        "sales.Customer",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="cheques",
    )
    supplier = models.ForeignKey(
        "purchases.Supplier",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="cheques",
    )
    sale = models.ForeignKey(
        "sales.Sale",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="cheques",
    )
    purchase = models.ForeignKey(
        "purchases.Purchase",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="cheques",
    )
    payment = models.ForeignKey(
        "sales.Payment",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="cheques",
    )

    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
    )
    notes = models.TextField(blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="cheques_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cheques"
        ordering = ["cheque_date", "-id"]
        indexes = [
            models.Index(fields=["company", "status", "cheque_date"]),
            models.Index(fields=["cheque_type", "status"]),
        ]

    def __str__(self) -> str:
        return f"Cheque #{self.cheque_number} ({self.bank_name}) - Rs. {self.amount} [{self.status}]"

    @property
    def party_name(self) -> str:
        if self.customer:
            return self.customer.name
        if self.supplier:
            return self.supplier.name
        return "N/A"

    @property
    def days_until_due(self) -> int:
        """Returns days until due (negative if overdue)."""
        today = timezone.localdate()
        return (self.cheque_date - today).days

    @property
    def is_overdue(self) -> bool:
        return self.status == self.STATUS_PENDING and self.days_until_due < 0

    @property
    def is_due_today(self) -> bool:
        return self.status == self.STATUS_PENDING and self.days_until_due == 0

    @property
    def is_due_soon(self) -> bool:
        return self.status == self.STATUS_PENDING and 0 < self.days_until_due <= 7

    @property
    def due_status_display(self) -> str:
        if self.status != self.STATUS_PENDING:
            return self.get_status_display()
        if self.days_until_due < 0:
            return f"Overdue ({abs(self.days_until_due)}d)"
        if self.days_until_due == 0:
            return "Due Today"
        if self.days_until_due == 1:
            return "Due Tomorrow"
        return f"Due in {self.days_until_due} days"

    @property
    def status_badge_class(self) -> str:
        if self.status == self.STATUS_CLEARED:
            return "badge-success"
        if self.status == self.STATUS_BOUNCED:
            return "badge-danger"
        if self.status == self.STATUS_CANCELLED:
            return "badge-secondary"
        if self.is_overdue or self.is_due_today:
            return "badge-danger"
        if self.days_until_due <= 3:
            return "badge-warning"
        return "badge-info"
