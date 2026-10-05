"""
Companies models: Company, Seller.
"""
from django.db import models


class Company(models.Model):
    """A business entity/company in the multi-tenant system."""

    company_name = models.CharField(max_length=255, db_index=True)
    company_phone = models.CharField(max_length=32, blank=True, default="", db_index=True)
    vat_pan_number = models.CharField(max_length=64, blank=True, default="", db_index=True)
    address = models.TextField(blank=True, default="")
    logo_url = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "companies"
        ordering = ["company_name"]
        verbose_name_plural = "companies"

    def __str__(self) -> str:
        return self.company_name


class Seller(models.Model):
    """A seller representative belonging to a company."""

    seller_name = models.CharField(max_length=255, db_index=True)
    seller_phone = models.CharField(max_length=32, blank=True, default="", db_index=True)
    company = models.ForeignKey(
        Company,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="sellers",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sellers"
        ordering = ["seller_name"]

    @property
    def display_name(self) -> str:
        if self.seller_phone:
            return f"{self.seller_name} - {self.seller_phone}"
        return self.seller_name

    def __str__(self) -> str:
        return self.display_name