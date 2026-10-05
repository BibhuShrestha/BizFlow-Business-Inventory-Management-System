"""
Purchases models: Supplier, Purchase, PurchaseItem.
"""
from decimal import Decimal
from django.db import models


class Supplier(models.Model):
    """Vendor or supplier selling goods to the business."""

    name = models.CharField(max_length=255, db_index=True)
    phone = models.CharField(max_length=32, blank=True, default="")
    email = models.EmailField(max_length=255, null=True, blank=True)
    address = models.TextField(blank=True, default="")
    opening_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    company = models.ForeignKey(
        "companies.Company",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="suppliers",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "suppliers"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Purchase(models.Model):
    """Purchase invoice / vendor bill."""

    STATUS_DUE = "Due"
    STATUS_PARTIAL = "Partial"
    STATUS_PAID = "Paid"
    STATUS_CHOICES = [
        (STATUS_DUE, "Due"),
        (STATUS_PARTIAL, "Partial"),
        (STATUS_PAID, "Paid"),
    ]

    purchase_number = models.CharField(max_length=64, unique=True, db_index=True)
    bill_number = models.CharField(max_length=64, blank=True, default="", db_index=True)
    supplier = models.ForeignKey(
        Supplier,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="purchases",
    )
    company = models.ForeignKey(
        "companies.Company",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="purchases",
    )
    purchase_date = models.DateTimeField()
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    payment_status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_DUE)
    payment_method = models.CharField(max_length=32, default="Cash")
    cheque_number = models.CharField(max_length=64, blank=True, default="")
    cheque_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True, db_index=True)
    notes = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "purchases"
        ordering = ["-purchase_date", "-id"]

    def __str__(self) -> str:
        return f"Purchase {self.purchase_number} ({self.total})"

    @property
    def subtotal(self) -> Decimal:
        """Calculate subtotal before discount and tax."""
        items_subtotal = self.items.aggregate(models.Sum("total"))["total__sum"]
        if items_subtotal is not None:
            return items_subtotal
        return (self.total + self.discount - self.tax).quantize(Decimal("0.01"))

    @property
    def paid_amount(self) -> Decimal:
        """Total payments made for this purchase."""
        total_p = self.payments.filter(status__iexact="Completed").aggregate(models.Sum("amount"))["amount__sum"]
        if total_p is not None:
            return total_p
        if self.payment_status == self.STATUS_PAID:
            return self.total
        return Decimal("0.00")

    @property
    def remaining_amount(self) -> Decimal:
        """Outstanding balance I owe supplier."""
        rem = self.total - self.paid_amount
        return max(Decimal("0.00"), rem.quantize(Decimal("0.01")))

    @property
    def is_overdue(self) -> bool:
        """Check if bill is overdue."""
        from django.utils import timezone
        if self.remaining_amount <= Decimal("0.00"):
            return False
        if not self.due_date:
            return False
        return self.due_date < timezone.localdate()

    @property
    def calculated_status(self) -> str:
        """Auto-calculated credit status."""
        if self.remaining_amount <= Decimal("0.00"):
            return "Paid"
        if self.is_overdue:
            return "Overdue"
        if self.paid_amount > Decimal("0.00"):
            return "Partially Paid"
        return "Unpaid"


class PurchaseItem(models.Model):
    """Line item on a purchase bill."""

    purchase = models.ForeignKey(
        Purchase,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        "inventory.Product",
        on_delete=models.RESTRICT,
        related_name="purchase_items",
    )
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "purchase_items"

    def __str__(self) -> str:
        return f"{self.product.name} x {self.quantity} on {self.purchase.purchase_number}"