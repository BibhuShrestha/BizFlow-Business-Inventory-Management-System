"""
Accounting models: ExpenseCategory, Expense, Account, JournalEntry, JournalEntryItem.
"""
from decimal import Decimal
from django.conf import settings
from django.db import models


class ExpenseCategory(models.Model):
    """Categorization for business expenses (Rent, Utilities, Salary, etc.)."""

    name = models.CharField(max_length=128, unique=True, db_index=True)
    description = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "expense_categories"
        verbose_name_plural = "expense categories"

    def __str__(self) -> str:
        return self.name


class Expense(models.Model):
    """Operational business expense entry."""

    category = models.CharField(max_length=128)
    description = models.TextField(blank=True, default="")
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    expense_date = models.DateTimeField()
    payment_method = models.CharField(max_length=32, default="Cash")
    reference = models.CharField(max_length=255, blank=True, default="")
    company = models.ForeignKey(
        "companies.Company",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="expenses",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="expenses",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "expenses"
        ordering = ["-expense_date", "-id"]

    def __str__(self) -> str:
        return f"{self.category}: {self.amount}"


class Account(models.Model):
    """Chart of Accounts ledger account."""

    name = models.CharField(max_length=128, unique=True, db_index=True)
    code = models.CharField(max_length=32, unique=True, db_index=True)
    description = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "accounts"
        ordering = ["code"]

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class JournalEntry(models.Model):
    """General Journal entry header."""

    entry_date = models.DateTimeField()
    description = models.TextField()
    reference_type = models.CharField(max_length=64, blank=True, default="")
    reference_id = models.IntegerField(null=True, blank=True)
    company = models.ForeignKey(
        "companies.Company",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="journal_entries",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "journal_entries"
        ordering = ["-entry_date", "-id"]
        verbose_name_plural = "journal entries"

    def __str__(self) -> str:
        return f"Journal #{self.id} on {self.entry_date}"


class JournalEntryItem(models.Model):
    """Debit/Credit line on a journal entry."""

    journal_entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.CASCADE,
        related_name="items",
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.RESTRICT,
        related_name="journal_items",
    )
    debit = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    credit = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))

    class Meta:
        db_table = "journal_entry_items"

    def __str__(self) -> str:
        return f"{self.account.name} (Dr {self.debit}, Cr {self.credit})"