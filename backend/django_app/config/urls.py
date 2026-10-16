"""Root URL configuration for the Business Inventory Management System."""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse, HttpResponse
from django.contrib.sitemaps.views import sitemap
from apps.core_app.sitemaps import StaticPageSitemap


def health_check(request):
    """Basic health-check endpoint. Returns 200 + JSON status."""
    try:
        from django.db import connection
        connection.ensure_connection()
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    return JsonResponse({"status": "healthy", "database": db_status})


def robots_txt(request):
    """Serve robots.txt to instruct search engines. Private app pages are disallowed."""
    site_url = getattr(settings, "SITE_URL", "http://localhost:8000")
    lines = [
        "User-agent: *",
        "",
        "# Disallow all private/authenticated application areas",
        "Disallow: /admin/",
        "Disallow: /dashboard/",
        "Disallow: /products/",
        "Disallow: /inventory/",
        "Disallow: /sales/",
        "Disallow: /purchases/",
        "Disallow: /customers/",
        "Disallow: /suppliers/",
        "Disallow: /expenses/",
        "Disallow: /reports/",
        "Disallow: /credit/",
        "Disallow: /companies/",
        "Disallow: /sellers/",
        "Disallow: /users/",
        "Disallow: /api/",
        "Disallow: /health/",
        "",
        "# Allow public pages",
        "Allow: /$",
        "Allow: /auth/login/",
        "Allow: /auth/register/",
        "Allow: /auth/forgot-password/",
        "",
        f"Sitemap: {site_url}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")


sitemaps = {
    "static": StaticPageSitemap,
}

urlpatterns = [
    # Django admin
    path("admin/", admin.site.urls),

    # Health check
    path("health/", health_check, name="health_check"),

    # Fast favicon handler
    path("favicon.ico", lambda r: HttpResponse(status=204)),
    path("favicon.png", lambda r: HttpResponse(status=204)),

    # SEO: robots.txt and sitemap.xml (public)
    path("robots.txt", robots_txt, name="robots_txt"),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django.contrib.sitemaps.views.sitemap"),

    # Main dashboard & landing
    path("", include("apps.dashboard.urls")),

    # Authentication & User accounts
    path("auth/", include("apps.accounts.urls")),
    path("users/", include("apps.accounts.user_urls")),

    # Companies & Sellers
    path("companies/", include("apps.companies.urls")),
    path("sellers/", include("apps.companies.sellers_urls")),

    # Products & Inventory Stock
    path("products/", include("apps.inventory.urls")),
    path("inventory/", include("apps.inventory.stock_urls")),

    # Customers & Sales Invoices
    path("customers/", include("apps.sales.customer_urls")),
    path("sales/", include("apps.sales.urls")),

    # Suppliers & Purchase Bills
    path("suppliers/", include("apps.purchases.supplier_urls")),
    path("purchases/", include("apps.purchases.urls")),

    # Operational Expenses
    path("expenses/", include("apps.accounting.expense_urls")),

    # Reports & Daybook
    path("reports/", include("apps.reports.urls")),

    # Receivables & Payables Management
    path("credit/", include("apps.credit.urls")),

    # Central Import & Export (Excel, CSV, JSON)
    path("import-export/", include("apps.core_app.urls")),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# ---------------------------------------------------------------------------
# Custom HTTP error handlers (Part 14)
# ---------------------------------------------------------------------------
handler404 = "apps.core_app.views.error_404"
handler500 = "apps.core_app.views.error_500"
handler403 = "apps.core_app.views.error_403"
handler400 = "apps.core_app.views.error_400"
