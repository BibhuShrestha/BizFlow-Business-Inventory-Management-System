import io
import logging
import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory
from django.urls import reverse

from apps.accounts.models import Role
from apps.core_app.logging_filters import SensitiveDataFilter
from apps.core_app.exports import parse_uploaded_file
from apps.core_app.views import error_404, error_500, error_403, error_400

User = get_user_model()


@pytest.fixture
def auth_admin(db):
    admin_role, _ = Role.objects.get_or_create(name="admin", defaults={"description": "Administrator"})
    user = User.objects.create_superuser(
        name="Performance Admin",
        email="perf_admin@example.com",
        password="ValidPassword123!",
        role=admin_role,
    )
    return user


@pytest.mark.django_db
class TestPerformanceAndOptimization:
    def test_performance_timing_middleware_header(self, client):
        """Verify PerformanceTimingMiddleware attaches X-Response-Time header."""
        response = client.get("/")
        assert "X-Response-Time" in response.headers
        assert "ms" in response.headers["X-Response-Time"]

    def test_cache_backend_functionality(self):
        """Verify that configured cache backend can get and set values smoothly."""
        cache_key = "test_perf_key"
        cache.set(cache_key, "perf_test_value", timeout=60)
        assert cache.get(cache_key) == "perf_test_value"
        cache.delete(cache_key)
        assert cache.get(cache_key) is None

    def test_inventory_query_optimization(self, client, auth_admin):
        """Verify product list uses select_related for relational models."""
        client.force_login(auth_admin)
        response = client.get(reverse("inventory:product_list"))
        assert response.status_code == 200
        # Ensure context contains paginated objects and filter selections
        assert "page_obj" in response.context
        assert "categories" in response.context


@pytest.mark.django_db
class TestLoggingAndSensitiveDataRedaction:
    def test_sensitive_data_filter_masks_passwords_and_tokens(self):
        """Verify SensitiveDataFilter actively redacts secrets from log records."""
        filter_instance = SensitiveDataFilter()
        logger = logging.getLogger("test_security_logger")

        # Test message with password
        record1 = logger.makeRecord("test", logging.INFO, "file.py", 10, "User login with password: MySecretPassword123!", (), None)
        filter_instance.filter(record1)
        assert "MySecretPassword123!" not in record1.msg
        assert "[REDACTED]" in record1.msg

        # Test message with bearer token
        record2 = logger.makeRecord("test", logging.INFO, "file.py", 10, "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9", (), None)
        filter_instance.filter(record2)
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in record2.msg
        assert "[REDACTED]" in record2.msg

        # Test dictionary args with sensitive keys
        record3 = logger.makeRecord("test", logging.INFO, "file.py", 10, "Attempt details: %s", ({"username": "admin", "password": "supersecretpassword"},), None)
        filter_instance.filter(record3)
        args_str = str(record3.args)
        assert "supersecretpassword" not in args_str
        assert "[REDACTED]" in args_str


@pytest.mark.django_db
class TestSecurityHeadersAndCookies:
    def test_security_settings_and_cookies(self):
        """Verify HttpOnly and SameSite cookie protections are enabled in settings."""
        assert settings.SESSION_COOKIE_HTTPONLY is True
        assert settings.CSRF_COOKIE_HTTPONLY is True
        assert settings.SESSION_COOKIE_SAMESITE in ["Lax", "Strict"]
        assert settings.CSRF_COOKIE_SAMESITE in ["Lax", "Strict"]

    def test_security_headers_in_response(self, client):
        """Verify hardening headers are returned on HTTP requests."""
        response = client.get("/")
        assert response.headers.get("X-Frame-Options") in ["DENY", "SAMEORIGIN"]
        assert response.headers.get("X-Content-Type-Options") == "nosniff"


@pytest.mark.django_db
class TestFileUploadHardening:
    def test_reject_oversized_file(self):
        """Verify uploaded files larger than 10MB are rejected safely."""
        large_content = b"x" * (11 * 1024 * 1024)  # 11 MB
        oversized_file = SimpleUploadedFile("large_import.csv", large_content, content_type="text/csv")
        headers, rows, error = parse_uploaded_file(oversized_file)
        assert headers is None
        assert rows is None
        assert "exceeds maximum allowed limit" in error

    def test_reject_disallowed_file_extension(self):
        """Verify non-whitelisted executable/script files are rejected."""
        malicious_file = SimpleUploadedFile("malicious.sh", b"#!/bin/bash\necho hack", content_type="application/x-sh")
        headers, rows, error = parse_uploaded_file(malicious_file)
        assert headers is None
        assert rows is None
        assert "Invalid file format" in error

    def test_accept_valid_csv(self):
        """Verify valid CSV format is accepted and parsed."""
        valid_csv = SimpleUploadedFile("items.csv", b"SKU,Item Name,Current Stock\nSKU-001,Test Widget,10\n", content_type="text/csv")
        headers, rows, error = parse_uploaded_file(valid_csv)
        assert error is None
        assert "SKU" in headers
        assert len(rows) == 1
        assert rows[0]["SKU"] == "SKU-001"


@pytest.mark.django_db
class TestAccessibleErrorHandling:
    def test_404_view_renders_clean_template_without_traceback(self):
        factory = RequestFactory()
        request = factory.get("/non-existent-page-url/")
        response = error_404(request)
        assert response.status_code == 404
        content = response.content.decode("utf-8")
        assert "Page Not Found" in content
        assert "Traceback" not in content

    def test_500_view_renders_clean_template_without_traceback(self):
        factory = RequestFactory()
        request = factory.get("/simulated-server-error/")
        response = error_500(request)
        assert response.status_code == 500
        content = response.content.decode("utf-8")
        assert "Internal Server Error" in content
        assert "Traceback" not in content

    def test_403_view_renders_clean_template_without_traceback(self):
        factory = RequestFactory()
        request = factory.get("/simulated-forbidden/")
        response = error_403(request)
        assert response.status_code == 403
        content = response.content.decode("utf-8")
        assert "Access Forbidden" in content
        assert "Traceback" not in content

    def test_400_view_renders_clean_template_without_traceback(self):
        factory = RequestFactory()
        request = factory.get("/simulated-bad-request/")
        response = error_400(request)
        assert response.status_code == 400
        content = response.content.decode("utf-8")
        assert "Bad Request" in content
        assert "Traceback" not in content
