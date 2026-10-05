"""Tax, PAN, and VAT validation utilities."""
import re
from decimal import Decimal
from core.exceptions import ValidationError


def validate_pan_vat(pan_vat: str | None) -> str:
    """
    Validate a Nepali PAN or VAT number.
    Must be exactly 9 numeric digits if provided.
    """
    if not pan_vat:
        return ""
    cleaned = pan_vat.strip()
    if not re.match(r"^\d{9}$", cleaned):
        raise ValidationError("PAN/VAT number must be exactly 9 digits.", field="pan_vat")
    return cleaned


def calculate_tax(amount: Decimal, tax_rate: Decimal) -> Decimal:
    """Calculate tax for an amount given tax rate percentage."""
    if tax_rate <= 0:
        return Decimal("0.00")
    return (amount * (tax_rate / Decimal("100"))).quantize(Decimal("0.01"))