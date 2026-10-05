"""
Inventory models: Category, Product, StockMovement, StockAdjustment.
"""
from decimal import Decimal
from django.conf import settings
from django.db import models


class Category(models.Model):
    """Product categorization."""

    name = models.CharField(max_length=128, unique=True, db_index=True)
    description = models.CharField(max_length=255, blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "categories"
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    """An inventory product record."""

    sku = models.CharField(max_length=64, unique=True, db_index=True)
    name = models.CharField(max_length=255, db_index=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.RESTRICT,
        related_name="products",
    )
    company = models.ForeignKey(
        "companies.Company",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="products",
    )
    seller = models.ForeignKey(
        "companies.Seller",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="products",
    )
    unit = models.CharField(max_length=32, default="pcs")
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    minimum_stock = models.IntegerField(default=0)
    critical_stock = models.IntegerField(default=0, help_text="Critical low stock alert threshold")
    current_stock = models.IntegerField(default=0)
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "products"
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.sku})"

    @property
    def stock_value(self) -> Decimal:
        """Returns the total valuation of current stock on hand."""
        return Decimal(self.current_stock) * self.purchase_price

    @property
    def effective_critical_stock(self) -> int:
        """Returns configured critical threshold or defaults to ~33% of minimum stock (at least 1)."""
        if self.critical_stock > 0:
            return self.critical_stock
        if self.minimum_stock > 1:
            return max(1, self.minimum_stock // 3)
        return 0

    @property
    def stock_status(self) -> str:
        """Returns normalized stock status: normal, low, critical, out_of_stock."""
        if self.current_stock <= 0:
            return "out_of_stock"
        if self.effective_critical_stock > 0 and self.current_stock <= self.effective_critical_stock:
            return "critical"
        if self.minimum_stock > 0 and self.current_stock <= self.minimum_stock:
            return "low"
        return "normal"

    @property
    def stock_status_display(self) -> str:
        """User-friendly label for stock status."""
        status_map = {
            "out_of_stock": "Out of Stock",
            "critical": "Critical Stock",
            "low": "Low Stock",
            "normal": "In Stock",
        }
        return status_map.get(self.stock_status, "In Stock")

    @property
    def stock_badge_class(self) -> str:
        """CSS badge class for stock status."""
        badge_map = {
            "out_of_stock": "badge-danger",
            "critical": "badge-danger",
            "low": "badge-warning",
            "normal": "badge-success",
        }
        return badge_map.get(self.stock_status, "badge-success")


class StockMovement(models.Model):
    """Ledger of all stock changes (inward, outward, adjustments)."""

    MOVEMENT_IN = "IN"
    MOVEMENT_OUT = "OUT"
    MOVEMENT_CHOICES = [
        (MOVEMENT_IN, "Stock In"),
        (MOVEMENT_OUT, "Stock Out"),
    ]

    REFERENCE_SALE = "SALE"
    REFERENCE_PURCHASE = "PURCHASE"
    REFERENCE_ADJUSTMENT = "ADJUSTMENT"
    REFERENCE_SALE_CANCEL = "SALE_CANCEL"
    REFERENCE_PURCHASE_CANCEL = "PURCHASE_CANCEL"

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="stock_movements",
    )
    movement_type = models.CharField(max_length=32, choices=MOVEMENT_CHOICES, default=MOVEMENT_IN)
    quantity = models.IntegerField(default=0)
    reference_type = models.CharField(max_length=64, default=REFERENCE_ADJUSTMENT)
    reference_id = models.IntegerField(null=True, blank=True)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "stock_movements"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.product.name} {self.movement_type} {self.quantity}"


class StockAdjustment(models.Model):
    """Manual inventory count adjustments."""

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="adjustments",
    )
    adjustment_type = models.CharField(max_length=16, default="IN")
    quantity = models.IntegerField(default=0)
    reason = models.TextField(blank=True, default="")
    adjusted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "stock_adjustments"
        ordering = ["-created_at"]