"""
Custom template tags and filters for Nepali dates, currency, and UI helpers.
"""
from datetime import date, datetime
from decimal import Decimal
from django import template
from services.nepali_date import NepaliDateService

register = template.Library()


@register.filter(name="nepali_date")
def nepali_date_filter(val) -> str:
    """Format an AD date or datetime into BS (Bikram Sambat) string."""
    if not val:
        return "-"
    try:
        return NepaliDateService.format_nepali_date(val)
    except Exception:
        return str(val)


@register.filter(name="nepali_currency")
def nepali_currency_filter(val) -> str:
    """Format a number or Decimal as Nepali rupees (Rs. 1,234.50)."""
    if val is None or val == "":
        return "Rs. 0.00"
    try:
        d = Decimal(str(val))
        return f"Rs. {d:,.2f}"
    except Exception:
        return f"Rs. {val}"


@register.filter(name="format_currency")
def format_currency_filter(val) -> str:
    """Format without prefix: 1,234.50."""
    if val is None or val == "":
        return "0.00"
    try:
        d = Decimal(str(val))
        return f"{d:,.2f}"
    except Exception:
        return str(val)


@register.filter(name="get_item")
def get_item(dictionary, key):
    """Retrieve key from dict in templates."""
    if isinstance(dictionary, dict):
        return dictionary.get(key, "")
    return ""

