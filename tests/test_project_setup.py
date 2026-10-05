"""
Part 2 — Project scaffold tests.

These tests verify:
  1. The Django project can be imported and configured without errors.
  2. All expected Django apps are registered in INSTALLED_APPS.
  3. The password strength validator (pure-Python domain code) works correctly.
  4. Core exception hierarchy is importable.
  5. The original Flask project is untouched.

These tests do NOT require a database connection.
"""
import importlib
import sys
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Helper: ensure backend/django_app is on sys.path before Django imports
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).resolve().parent.parent
_DJANGO_APP = _ROOT / "backend" / "django_app"
_BACKEND = _ROOT / "backend"
for _p in [str(_DJANGO_APP), str(_BACKEND)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)


# ---------------------------------------------------------------------------
# 1. Django settings import
# ---------------------------------------------------------------------------
class TestDjangoSettings:
    """Verify settings modules are importable and correctly structured."""

    def test_base_settings_importable(self):
        mod = importlib.import_module("config.settings.base")
        assert hasattr(mod, "INSTALLED_APPS")
        assert hasattr(mod, "AUTH_USER_MODEL")
        assert hasattr(mod, "DATABASES")

    def test_auth_user_model_is_custom(self):
        mod = importlib.import_module("config.settings.base")
        assert mod.AUTH_USER_MODEL == "accounts.User", (
            "AUTH_USER_MODEL must be set to 'accounts.User' from the start "
            "to avoid breaking Django migrations later."
        )

    def test_testing_settings_use_sqlite_memory(self):
        mod = importlib.import_module("config.settings.testing")
        db = mod.DATABASES["default"]
        assert db["ENGINE"] == "django.db.backends.sqlite3"
        assert db["NAME"] == ":memory:" or "memory" in db["NAME"]

    def test_all_local_apps_in_installed_apps(self):
        mod = importlib.import_module("config.settings.base")
        expected = [
            "apps.accounts",
            "apps.companies",
            "apps.inventory",
            "apps.sales",
            "apps.purchases",
            "apps.accounting",
            "apps.reports",
            "apps.audit",
            "apps.core_app",
        ]
        for app in expected:
            assert app in mod.INSTALLED_APPS, f"{app} missing from INSTALLED_APPS"


# ---------------------------------------------------------------------------
# 2. Django system check (django.setup() + check framework)
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestDjangoSystemCheck:
    """Run the Django system check framework."""

    def test_django_check_passes(self):
        """django.core.management.call_command('check') should exit cleanly."""
        import django
        from django.core.management import call_command
        from io import StringIO

        out = StringIO()
        # This raises SystemCheckError if any check fails.
        call_command("check", stdout=out, stderr=out)
        output = out.getvalue()
        assert "System check identified no issues" in output or output.strip() == "", (
            f"Django system check reported issues:\n{output}"
        )


# ---------------------------------------------------------------------------
# 3. Password validator (pure-Python domain code)
# ---------------------------------------------------------------------------
class TestPasswordValidator:
    """Verify the migrated password strength validator works correctly."""

    def _import_validator(self):
        return importlib.import_module("domain.validators.password")

    def test_valid_password_passes(self):
        mod = self._import_validator()
        result = mod.check_password_strength("Secure@123")
        assert result.valid is True
        assert result.errors == []

    def test_too_short_fails(self):
        mod = self._import_validator()
        result = mod.check_password_strength("Ab@1")
        assert result.valid is False
        assert any("8 characters" in e for e in result.errors)

    def test_missing_uppercase_fails(self):
        mod = self._import_validator()
        result = mod.check_password_strength("secure@123")
        assert result.valid is False
        assert any("uppercase" in e for e in result.errors)

    def test_missing_lowercase_fails(self):
        mod = self._import_validator()
        result = mod.check_password_strength("SECURE@123")
        assert result.valid is False
        assert any("lowercase" in e for e in result.errors)

    def test_missing_digit_fails(self):
        mod = self._import_validator()
        result = mod.check_password_strength("Secure@abc")
        assert result.valid is False
        assert any("number" in e for e in result.errors)

    def test_missing_special_char_fails(self):
        mod = self._import_validator()
        result = mod.check_password_strength("Secure1234")
        assert result.valid is False
        assert any("special" in e for e in result.errors)

    def test_validate_password_raises_on_invalid(self):
        mod = self._import_validator()
        with pytest.raises(ValueError, match="Password must"):
            mod.validate_password("weak")

    def test_validate_password_returns_valid(self):
        mod = self._import_validator()
        result = mod.validate_password("Secure@123")
        assert result == "Secure@123"


# ---------------------------------------------------------------------------
# 4. Core exceptions importable
# ---------------------------------------------------------------------------
class TestCoreExceptions:
    """Verify the shared exception hierarchy is importable."""

    def test_all_exceptions_importable(self):
        mod = importlib.import_module("core.exceptions")
        for exc_name in [
            "AppError", "NotFoundError", "PermissionDeniedError",
            "ValidationError", "AuthenticationError", "ConflictError",
            "InsufficientStockError",
        ]:
            assert hasattr(mod, exc_name), f"{exc_name} missing from core.exceptions"

    def test_exception_hierarchy(self):
        mod = importlib.import_module("core.exceptions")
        assert issubclass(mod.NotFoundError, mod.AppError)
        assert issubclass(mod.PermissionDeniedError, mod.AppError)
        assert issubclass(mod.InsufficientStockError, mod.AppError)

    def test_insufficient_stock_message(self):
        from core.exceptions import InsufficientStockError
        err = InsufficientStockError("Widget", available=5, requested=10)
        assert "Widget" in str(err)
        assert "5" in str(err)
        assert "10" in str(err)


# ---------------------------------------------------------------------------
# 5. Original Flask project is untouched
# ---------------------------------------------------------------------------
class TestFlaskProjectIntegrity:
    """Verify the original Flask project was not modified."""

    def test_flask_project_exists(self):
        flask_root = _ROOT.parent / "business"
        assert flask_root.exists(), "Original Flask project directory must still exist"

    def test_flask_run_py_exists(self):
        run_py = _ROOT.parent / "business" / "run.py"
        assert run_py.exists(), "run.py in Flask project must not have been deleted"

    def test_flask_app_init_exists(self):
        app_init = _ROOT.parent / "business" / "app" / "__init__.py"
        assert app_init.exists(), "app/__init__.py in Flask project must not have been modified"

    def test_flask_config_exists(self):
        config = _ROOT.parent / "business" / "config.py"
        assert config.exists(), "config.py in Flask project must not have been deleted"

    def test_flask_models_folder_intact(self):
        models_dir = _ROOT.parent / "business" / "app" / "models"
        assert models_dir.is_dir(), "Flask models directory must still exist"
        model_files = list(models_dir.glob("*.py"))
        assert len(model_files) >= 20, (
            f"Expected at least 20 model files in Flask project, found {len(model_files)}"
        )


# ---------------------------------------------------------------------------
# 6. FastAPI health check
# ---------------------------------------------------------------------------
class TestFastAPIApp:
    """Verify FastAPI application boots and health endpoint returns 200."""

    def test_fastapi_health(self):
        from api.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)
        res = client.get("/api/v1/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"
        assert data["api"] == "fastapi"

# ---------------------------------------------------------------------------
# 7. Architecture & Shared Business Logic Tests (Part 4)
# ---------------------------------------------------------------------------
class TestSharedArchitecture:
    """Verify clean separation of interfaces, domain, services, and repositories."""

    def test_services_package_importable(self):
        from services import AuthService, StockService, SaleService, PurchaseService
        assert AuthService is not None
        assert StockService is not None
        assert SaleService is not None
        assert PurchaseService is not None

    def test_nepali_date_service(self):
        from services.nepali_date import NepaliDateService
        today_bs = NepaliDateService.today_bs_str()
        assert len(today_bs) == 10  # YYYY-MM-DD
        # Test known historical date conversion (2024-10-02 -> 2081-06-16)
        from datetime import date
        bs_date = NepaliDateService.ad_to_bs(date(2024, 10, 2))
        assert bs_date.year == 2081
        assert bs_date.month == 6
        assert bs_date.day == 16
        # Roundtrip back to AD
        ad_back = NepaliDateService.bs_to_ad(2081, 6, 16)
        assert ad_back == date(2024, 10, 2)

    def test_validators_package_importable(self):
        from validators import check_password_strength, validate_password
        assert callable(check_password_strength)
        assert callable(validate_password)
        res = check_password_strength("StrongPass@123")
        assert res.valid is True

    def test_repositories_package_importable(self):
        from repositories import BaseRepository
        assert BaseRepository is not None

    def test_integrations_package_importable(self):
        from integrations import EmailService, GoogleOAuthClient
        assert EmailService is not None
        assert GoogleOAuthClient is not None

    def test_database_url_flexibility(self):
        """Verify environment parses PostgreSQL, MySQL, and SQLite without lock-in."""
        import environ
        env = environ.Env()
        pg = env.db_url_config("postgresql://user:secret@localhost:5432/bizflow")
        assert pg["ENGINE"] == "django.db.backends.postgresql"
        assert pg["NAME"] == "bizflow"
        assert pg["USER"] == "user"

        mysql = env.db_url_config("mysql://user:secret@localhost:3306/bizflow")
        assert mysql["ENGINE"] == "django.db.backends.mysql"
        assert mysql["NAME"] == "bizflow"

        sqlite = env.db_url_config("sqlite:///bizflow.db")
        assert sqlite["ENGINE"] == "django.db.backends.sqlite3"