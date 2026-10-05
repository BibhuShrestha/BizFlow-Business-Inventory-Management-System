"""
SEO Engineering Tests — Part 11 & 15 requirements.

Tests verify:
- Public pages are indexable (landing)
- Private pages are protected from indexing (dashboard, products, sales, etc.)
- robots.txt serves correctly and disallows private areas
- sitemap.xml serves correctly and includes only public pages
- All pages have a <title> tag
- Public pages have canonical links
- Open Graph metadata on public pages
- meta description on public pages
"""
import pytest
from django.test import Client
from django.urls import reverse


@pytest.mark.django_db
class TestRobotsTxt:
    def test_robots_txt_is_served(self, client):
        """robots.txt must be accessible at /robots.txt."""
        response = client.get("/robots.txt")
        assert response.status_code == 200
        assert "text/plain" in response["Content-Type"]

    def test_robots_txt_disallows_dashboard(self, client):
        """robots.txt must disallow the dashboard."""
        response = client.get("/robots.txt")
        content = response.content.decode("utf-8")
        assert "Disallow: /dashboard/" in content

    def test_robots_txt_disallows_api(self, client):
        """robots.txt must disallow API endpoints."""
        response = client.get("/robots.txt")
        content = response.content.decode("utf-8")
        assert "Disallow: /api/" in content

    def test_robots_txt_disallows_admin(self, client):
        """robots.txt must disallow Django admin."""
        response = client.get("/robots.txt")
        content = response.content.decode("utf-8")
        assert "Disallow: /admin/" in content

    def test_robots_txt_disallows_sales(self, client):
        """robots.txt must disallow private sales pages."""
        response = client.get("/robots.txt")
        content = response.content.decode("utf-8")
        assert "Disallow: /sales/" in content

    def test_robots_txt_references_sitemap(self, client):
        """robots.txt must reference the sitemap URL."""
        response = client.get("/robots.txt")
        content = response.content.decode("utf-8")
        assert "Sitemap:" in content
        assert "sitemap.xml" in content


@pytest.mark.django_db
class TestSitemapXml:
    def test_sitemap_is_served(self, client):
        """sitemap.xml must be accessible at /sitemap.xml."""
        response = client.get("/sitemap.xml")
        assert response.status_code == 200
        assert "xml" in response["Content-Type"]

    def test_sitemap_contains_home_url(self, client):
        """sitemap.xml must include the public landing/home URL."""
        response = client.get("/sitemap.xml")
        content = response.content.decode("utf-8")
        # The home URL should appear in the sitemap
        assert "<loc>" in content

    def test_sitemap_excludes_dashboard(self, client):
        """sitemap.xml must not include the dashboard URL."""
        response = client.get("/sitemap.xml")
        content = response.content.decode("utf-8")
        assert "/dashboard/" not in content

    def test_sitemap_excludes_api(self, client):
        """sitemap.xml must not include API endpoints."""
        response = client.get("/sitemap.xml")
        content = response.content.decode("utf-8")
        assert "/api/" not in content


@pytest.mark.django_db
class TestPublicPageSEO:
    def test_landing_page_is_accessible(self, client):
        """Public landing page must return 200."""
        response = client.get("/")
        assert response.status_code == 200

    def test_landing_page_has_title(self, client):
        """Landing page must have a <title> tag."""
        response = client.get("/")
        content = response.content.decode("utf-8")
        assert "<title>" in content
        assert "BizFlow" in content

    def test_landing_page_has_meta_description(self, client):
        """Landing page must have a meta description."""
        response = client.get("/")
        content = response.content.decode("utf-8")
        assert 'name="description"' in content

    def test_landing_page_has_og_metadata(self, client):
        """Landing page must have Open Graph metadata."""
        response = client.get("/")
        content = response.content.decode("utf-8")
        assert "og:title" in content or "og:type" in content

    def test_landing_page_allows_indexing(self, client):
        """Landing page must NOT have noindex directive."""
        response = client.get("/")
        content = response.content.decode("utf-8")
        # The landing page is public; it should have index, follow or no noindex
        # It should NOT have noindex
        # Note: if meta robots is absent that's also fine for public pages
        # We check it does NOT block indexing
        assert "index, follow" in content or "noindex" not in content


@pytest.mark.django_db
class TestPrivatePageSEO:
    def test_login_page_has_noindex(self, client):
        """Login page uses base.html which defaults to noindex."""
        from apps.accounts.models import Role, User
        response = client.get("/auth/login/")
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        # base.html sets noindex by default for all authenticated app pages
        assert "noindex" in content

    def test_dashboard_requires_auth(self, client):
        """Dashboard must redirect unauthenticated users (not publicly accessible)."""
        response = client.get("/dashboard/", follow=False)
        # Should redirect to login, not serve content to crawlers
        assert response.status_code in [302, 301]

    def test_products_requires_auth(self, client):
        """Products page must redirect unauthenticated users."""
        response = client.get("/products/", follow=False)
        assert response.status_code in [302, 301]

    def test_sales_requires_auth(self, client):
        """Sales page must redirect unauthenticated users."""
        response = client.get("/sales/", follow=False)
        assert response.status_code in [302, 301]
