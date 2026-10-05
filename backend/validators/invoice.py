"""Invoice and financial amount validation."""
from decimal import Decimal
from core.exceptions import ValidationError


def validate_positive_amount(amount: Decimal, field_name: str = "amount") -> Decimal:
    """Ensure financial amount is non-negative."""
    if amount < 0:
        raise ValidationError(f"{field_name} cannot be negative.", field=field_name)
    return amount


def validate_positive_quantity(quantity: int, field_name: str = "quantity") -> int:
    """Ensure quantity is strictly positive (>= 1)."""
    if quantity <= 0:
        raise ValidationError(f"{field_name} must be at least 1.", field=field_name)
    return quantity