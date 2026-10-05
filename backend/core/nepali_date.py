"""
Nepali Date Service — Bikram Sambat (BS) calendar support.
Converts between AD (Gregorian) and BS dates.
"""
import logging
from datetime import date

logger = logging.getLogger(__name__)


class NepaliDateService:
    """AD to BS and BS to AD calendar conversion utilities."""

    @staticmethod
    def ad_to_bs(ad_date: date) -> str | None:
        """
        Convert a Gregorian date to Nepali BS date string (YYYY-MM-DD).

        Args:
            ad_date: Python date object in Gregorian calendar.

        Returns:
            BS date string (e.g. '2081-01-15') or None on failure.
        """
        try:
            from nepali_datetime import date as nepali_date

            bs = nepali_date.from_datetime_date(ad_date)
            return bs.strftime("%Y-%m-%d")
        except Exception as e:
            logger.error("Failed to convert AD %s to BS: %s", ad_date, e)
            return None

    @staticmethod
    def bs_to_ad(bs_year: int, bs_month: int, bs_day: int) -> date | None:
        """
        Convert a Nepali BS date to Gregorian date.

        Args:
            bs_year: Bikram Sambat year.
            bs_month: Month (1-12).
            bs_day: Day (1-32 depending on month).

        Returns:
            Python date object or None on failure.
        """
        try:
            from nepali_datetime import date as nepali_date

            bs = nepali_date(bs_year, bs_month, bs_day)
            return bs.to_datetime_date()
        except Exception as e:
            logger.error("Failed to convert BS %s-%s-%s to AD: %s", bs_year, bs_month, bs_day, e)
            return None

    @staticmethod
    def format_bs(ad_date: date) -> str:
        """
        Format a Gregorian date as BS date string for display.

        Returns:
            Formatted BS string or empty string on failure.
        """
        result = NepaliDateService.ad_to_bs(ad_date)
        return result or ""

    @staticmethod
    def format_nepali_date(ad_date: date) -> str:
        """Format a Gregorian date as BS date string."""
        return NepaliDateService.format_bs(ad_date)
