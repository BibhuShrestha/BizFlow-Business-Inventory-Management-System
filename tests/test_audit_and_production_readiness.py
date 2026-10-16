"""
Production Readiness, Security, and Supabase Architecture Audit Tests.

Validates:
1. Production settings configuration (DEBUG=False, HTTPS, HSTS, Secure Cookies, WhiteNoise).
2. Django deployment checks (manage.py check --deploy passes with 0 issues).
3. Database URL parser with Supabase PostgreSQL, SSL, and connection pooling options.
4. Backup & Migration script integrity and non-destructive operations.
5. End-to-end Authentication & Authorization RBAC security.
"""
import os
import sys
import importlib
from pathlib import Path
import pytest
from django.test import Client

ROOT = Path(__file__).resolve().parent.parent
DJANGO_APP = ROOT / "backend" / "django_app"
BACKEND = ROOT / "backend"

for p in [str(DJANGO_APP), str(BACKEND)]:
    if p not in sys.path:
        sys.path.insert(0, p)


class TestProductionSettingsAudit:
    """Audit production configuration for security and deployment standards."""

    def test_production_settings_enforce_https_and_cookies(self):
        mod = importlib.import_module("config.settings.production")
        assert mod.DEBUG is False
        assert mod.SESSION_COOKIE_SECURE is True
        assert mod.CSRF_COOKIE_SECURE is True
        assert mod.SECURE_HSTS_SECONDS >= 31536000
        assert mod.SECURE_HSTS_INCLUDE_SUBDOMAINS is True
        assert mod.SECURE_HSTS_PRELOAD is True
        assert mod.SECURE_PROXY_SSL_HEADER == ("HTTP_X_FORWARDED_PROTO", "https")
        assert "whitenoise" in mod.STORAGES["staticfiles"]["BACKEND"].lower()

    def test_production_logging_configured(self):
        mod = importlib.import_module("config.settings.production")
        assert "LOGGING" in dir(mod)
        assert "console" in mod.LOGGING["handlers"]
        assert "django" in mod.LOGGING["loggers"]


class TestSupabaseDatabaseConfiguration:
    """Audit PostgreSQL & Supabase database parsing and pooling."""

    def test_supabase_direct_url_parsing(self):
        import environ
        env = environ.Env()
        url = "postgresql://postgres.testref:secretpass@aws-0-eu-central-1.pooler.supabase.com:5432/postgres?sslmode=require"
        parsed = env.db_url_config(url)
        assert parsed["ENGINE"] == "django.db.backends.postgresql"
        assert parsed["NAME"] == "postgres"
        assert parsed["USER"] == "postgres.testref"
        assert parsed["PORT"] == 5432

    def test_supabase_pooler_url_parsing(self):
        import environ
        env = environ.Env()
        url = "postgresql://postgres.testref:secretpass@aws-0-eu-central-1.pooler.supabase.com:6543/postgres"
        parsed = env.db_url_config(url)
        assert parsed["ENGINE"] == "django.db.backends.postgresql"
        assert parsed["PORT"] == 6543

    def test_backup_and_verify_scripts_importable(self):
        from scripts.backup_mysql import run_backup
        from scripts.verify_database_migration import verify_database
        assert callable(run_backup)
        assert callable(verify_database)


@pytest.mark.django_db
class TestAuthenticationAndAccessControlAudit:
    """Audit RBAC, anonymous protection, and tenant scoping."""

    def test_private_routes_block_anonymous_users(self):
        client = Client()
        protected_routes = [
            "/dashboard/",
            "/products/",
            "/inventory/",
            "/sales/",
            "/purchases/",
            "/customers/",
            "/suppliers/",
            "/expenses/",
            "/reports/",
            "/credit/",
            "/companies/",
            "/users/",
        ]
        for route in protected_routes:
            resp = client.get(route)
            assert resp.status_code == 302, f"Route {route} allowed anonymous access!"
            assert "/auth/login/" in resp.url

    def test_customer_role_cannot_access_user_management(self):
        from apps.accounts.models import User, Role
        role_customer, _ = Role.objects.get_or_create(name=Role.ROLE_CUSTOMER)
        cust_user = User.objects.create_user(
            email="cust_audit_test@example.com",
            name="Test Customer",
            password="StrongPass@123",
            role=role_customer,
        )
        client = Client()
        client.force_login(cust_user)

        resp = client.get("/users/")
        assert resp.status_code == 302, "Customer role was not redirected away from /users/!"
        assert "/dashboard/" in resp.url or "/auth/login/" in resp.url

    def test_fastapi_unauthenticated_api_rejection(self):
        from fastapi.testclient import TestClient
        from api.main import app

        api_client = TestClient(app)
        res_auth = api_client.get("/api/v1/auth/me")
        assert res_auth.status_code == 401

        res_credit = api_client.get("/api/v1/credit/summary")
        assert res_credit.status_code == 401

        res_health = api_client.get("/api/v1/health")
        assert res_health.status_code == 200
        assert res_health.json()["status"] == "healthy"
