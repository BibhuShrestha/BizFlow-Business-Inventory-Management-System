"""
Transaction models: Sale, SaleItem, Purchase, PurchaseItem, Payment, Expense.
"""
from decimal import Decimal

from django.conf import settings
from django.db import models


PAYMENT_METHOD_CHOICES = [
    ("Cash", "Cash"),
    ("Cheque", "Cheque"),
    ("Bank Transfer", "Bank Transfer"),
    ("QR / Mobile Pay", "QR / Mobile Pay"),
    ("Credit", "Credit"),
]

PAYMENT_STATUS_CHOICES = [
    ("Due", "Due"),
    ("Partial", "Partial"),
    ("Paid", "Paid"),
]


class Sale(models.Model):
    """A completed sales invoice with line items."""

    invoice_number = models.CharField(max_length=64, unique=True, db_index=True)
    bill_number = models.CharField(max_length=64, blank=True, default="", db_index=True)
    customer = models.ForeignKey(
        "parties.Customer",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="sales",
    )
    sale_date = models.DateTimeField()
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    payment_status = models.CharField(
        max_length=32, choices=PAYMENT_STATUS_CHOICES, default="Due"
    )
    payment_method = models.CharField(
        max_length=32, choices=PAYMENT_METHOD_CHOICES, default="Cash"
    )
    cheque_number = models.CharField(max_length=64, blank=True, default="")
    cheque_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="sales_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "transactions_sale"
        ordering = ["-sale_date"]

    def __str__(self) -> str:
        return f"Sale {self.invoice_number}"


class SaleItem(models.Model):
    """A line item in a sale."""

    sale = models.ForeignKey("transactions.Sale", on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        "inventory.Product", on_delete=models.RESTRICT, related_name="sale_items"
    )
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "transactions_saleitem"

    def __str__(self) -> str:
        return f"SaleItem(sale={self.sale_id}, product={self.product_id})"


class Purchase(models.Model):
    """A purchase order (stock replenishment) from a supplier."""

    purchase_number = models.CharField(max_length=64, unique=True, db_index=True)
    bill_number = models.CharField(max_length=64, blank=True, default="", db_index=True)
    supplier = models.ForeignKey(
        "parties.Supplier",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="purchases",
    )
    purchase_date = models.DateTimeField()
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    payment_status = models.CharField(
        max_length=32, choices=PAYMENT_STATUS_CHOICES, default="Due"
    )
    payment_method = models.CharField(
        max_length=32, choices=PAYMENT_METHOD_CHOICES, default="Cash"
    )
    cheque_number = models.CharField(max_length=64, blank=True, default="")
    cheque_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="purchases_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "transactions_purchase"
        ordering = ["-purchase_date"]

    def __str__(self) -> str:
        return f"Purchase {self.purchase_number}"


class PurchaseItem(models.Model):
    """A line item in a purchase order."""

    purchase = models.ForeignKey(
        "transactions.Purchase", on_delete=models.CASCADE, related_name="items"
    )
    product = models.ForeignKey(
        "inventory.Product", on_delete=models.RESTRICT, related_name="purchase_items"
    )
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "transactions_purchaseitem"

    def __str__(self) -> str:
        return f"PurchaseItem(purchase={self.purchase_id}, product={self.product_id})"


class Payment(models.Model):
    """A payment recorded against a sale or purchase."""

    PAYMENT_STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Completed", "Completed"),
        ("Cancelled", "Cancelled"),
        ("Bounced", "Bounced"),
    ]

    payment_date = models.DateTimeField()
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    payment_method = models.CharField(max_length=32, choices=PAYMENT_METHOD_CHOICES, default="Cash")
    status = models.CharField(max_length=32, choices=PAYMENT_STATUS_CHOICES, default="Completed")
    reference = models.CharField(max_length=255, blank=True, default="")
    remarks = models.TextField(blank=True, default="")
    cheque_number = models.CharField(max_length=64, blank=True, default="")
    cheque_date = models.DateTimeField(null=True, blank=True)
    bank_name = models.CharField(max_length=128, blank=True, default="")
    qr_reference = models.CharField(max_length=255, blank=True, default="")
    sale = models.ForeignKey(
        "transactions.Sale",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="payments",
    )
    purchase = models.ForeignKey(
        "transactions.Purchase",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="payments",
    )
    customer = models.ForeignKey(
        "parties.Customer",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="payments",
    )
    supplier = models.ForeignKey(
        "parties.Supplier",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="payments",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "transactions_payment"
        ordering = ["-payment_date"]

    def __str__(self) -> str:
        return f"Payment {self.amount} ({self.payment_method})"


class Expense(models.Model):
    """A business expense."""

    category = models.CharField(max_length=128, db_index=True)
    description = models.TextField(blank=True, default="")
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    expense_date = models.DateTimeField()
    payment_method = models.CharField(
        max_length=32, choices=PAYMENT_METHOD_CHOICES, default="Cash"
    )
    reference = models.CharField(max_length=255, blank=True, default="")
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="expenses",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "transactions_expense"
        ordering = ["-expense_date"]

    def __str__(self) -> str:
        return f"Expense {self.category} {self.amount}"
