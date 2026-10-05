"""Parties models: Customer, Supplier."""
from decimal import Decimal

from django.db import models


class Customer(models.Model):
    """A customer who buys from the business."""

    name = models.CharField(max_length=255, db_index=True)
    phone = models.CharField(max_length=32, blank=True, default="")
    email = models.EmailField(unique=True, null=True, blank=True)
    address = models.TextField(blank=True, default="")
    opening_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "parties_customer"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Supplier(models.Model):
    """A supplier who sells goods to the business."""

    name = models.CharField(max_length=255, db_index=True)
    phone = models.CharField(max_length=32, blank=True, default="")
    email = models.EmailField(unique=True, null=True, blank=True)
    address = models.TextField(blank=True, default="")
    opening_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "parties_supplier"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name
