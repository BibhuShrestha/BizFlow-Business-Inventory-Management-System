"""
Nepali Date Service (Bikram Sambat BS <-> Gregorian AD).

Provides pure-Python date utilities for business reporting and invoice display
using the nepali-datetime library.
"""
from datetime import date, datetime
import nepali_datetime


class NepaliDateService:
    """Utilities for converting and formatting Nepali Bikram Sambat (BS) dates."""

    @staticmethod
    def today_bs() -> nepali_datetime.date:
        """Return today's date in Bikram Sambat."""
        return nepali_datetime.date.today()

    @staticmethod
    def today_bs_str() -> str:
        """Return today's date in BS as YYYY-MM-DD string."""
        return str(nepali_datetime.date.today())

    @staticmethod
    def ad_to_bs(ad_date: date | datetime | str) -> nepali_datetime.date:
        """Convert a Gregorian (AD) date to Bikram Sambat (BS)."""
        if isinstance(ad_date, str):
            ad_date = datetime.strptime(ad_date[:10], "%Y-%m-%d").date()
        elif isinstance(ad_date, datetime):
            ad_date = ad_date.date()
        return nepali_datetime.date.from_datetime_date(ad_date)

    @staticmethod
    def bs_to_ad(bs_year: int, bs_month: int, bs_day: int) -> date:
        """Convert Bikram Sambat (BS) year, month, day to Gregorian (AD) date."""
        bs_date = nepali_datetime.date(bs_year, bs_month, bs_day)
        return bs_date.to_datetime_date()

    @staticmethod
    def format_bs(bs_date: nepali_datetime.date, fmt: str = "%Y-%m-%d") -> str:
        """Format a BS date."""
        return bs_date.strftime(fmt)
    @staticmethod
    def format_nepali_date(ad_date: date) -> str:
        """Format a Gregorian date as BS date string."""
        return NepaliDateService.format_bs(ad_date)
