"""
Sitemap configuration for BizFlow public pages.

Only public, indexable pages are included.
All authenticated/private dashboard/ERP views are EXCLUDED.
"""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticPageSitemap(Sitemap):
    """Sitemap for static public pages only (landing, login, register)."""
    changefreq = "monthly"
    priority = 0.8
    protocol = "https"

    def items(self):
        # Only include genuinely public pages
        return [
            "dashboard:home",
            "accounts:login",
            "accounts:register",
        ]

    def location(self, item):
        return reverse(item)
