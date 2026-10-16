"""
Comprehensive tests for Supabase Auth Client, User Sync, and Vercel Serverless Integration.
"""
import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.core.wsgi import WSGIHandler

ROOT = Path(__file__).resolve().parent.parent
DJANGO_APP = ROOT / "backend" / "django_app"
BACKEND = ROOT / "backend"

for p in [str(DJANGO_APP), str(BACKEND)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from apps.companies.models import Company
from integrations.supabase_client import SupabaseAuthClient
from domain.services.auth_service import AuthService

User = get_user_model()


@pytest.fixture
def test_company(db):
    return Company.objects.create(
        company_name="Test Corp",
        company_phone="9800000000",
        vat_pan_number="123456789",
        address="Kathmandu",
    )


class TestSupabaseAuthClient:
    """Test SupabaseAuthClient methods and user identity synchronization."""

    def test_client_configuration_detection(self, monkeypatch):
        monkeypatch.setenv("SUPABASE_URL", "https://xyzcompany.supabase.co")
        monkeypatch.setenv("SUPABASE_ANON_KEY", "test-anon-key")
        monkeypatch.setenv("SUPABASE_JWT_SECRET", "test-jwt-secret")

        assert SupabaseAuthClient.is_configured() is True
        assert SupabaseAuthClient.get_url() == "https://xyzcompany.supabase.co"
        assert SupabaseAuthClient.get_anon_key() == "test-anon-key"

        monkeypatch.delenv("SUPABASE_URL", raising=False)
        assert SupabaseAuthClient.is_configured() is False

    @pytest.mark.django_db
    def test_sync_to_django_user_creates_new_user(self, test_company):
        from apps.accounts.models import Role
        Role.objects.get_or_create(name=Role.ROLE_STAFF)

        supabase_user_data = {
            "id": "11111111-2222-3333-4444-555555555555",
            "email": "supabase.cashier@example.com",
            "user_metadata": {
                "first_name": "Supabase",
                "last_name": "Cashier",
            },
        }

        user = SupabaseAuthClient.sync_to_django_user(supabase_user_data)

        assert user.email == "supabase.cashier@example.com"
        assert user.supabase_uid == "11111111-2222-3333-4444-555555555555"
        assert user.name == "Supabase Cashier"
        assert user.is_active is True
        assert user.active_company == test_company

    @pytest.mark.django_db
    def test_sync_to_django_user_links_existing_email(self, test_company):
        from apps.accounts.models import Role
        role_mgr, _ = Role.objects.get_or_create(name=Role.ROLE_MANAGER)
        existing_user = User.objects.create_user(
            email="manager@example.com",
            name="Existing Manager",
            password="StrongPassword123!",
            role=role_mgr,
            active_company=test_company,
        )
        assert existing_user.supabase_uid is None

        supabase_user_data = {
            "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            "email": "manager@example.com",
            "user_metadata": {
                "name": "Updated Manager",
            },
        }

        synced_user = SupabaseAuthClient.sync_to_django_user(supabase_user_data)

        assert synced_user.id == existing_user.id
        assert synced_user.supabase_uid == "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"

    @patch("integrations.supabase_client.requests.post")
    def test_sign_in_with_password_success(self, mock_post, monkeypatch):
        monkeypatch.setenv("SUPABASE_URL", "https://xyzcompany.supabase.co")
        monkeypatch.setenv("SUPABASE_ANON_KEY", "test-anon-key")

        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "access_token": "mock-access-token",
            "refresh_token": "mock-refresh-token",
            "user": {
                "id": "user-uuid-1234",
                "email": "auth@example.com",
            },
        }
        mock_post.return_value = mock_resp

        result = SupabaseAuthClient.sign_in_with_password("auth@example.com", "SecretPass123!")
        assert result["access_token"] == "mock-access-token"
        assert result["user"]["email"] == "auth@example.com"


class TestAuthServiceHybridSupabase:
    """Test AuthService fallback and hybrid Supabase auth flow."""

    @pytest.mark.django_db
    def test_auth_service_authenticates_local_user_when_supabase_unconfigured(self, test_company):
        from apps.accounts.models import Role
        role_admin, _ = Role.objects.get_or_create(name=Role.ROLE_ADMIN)
        local_user = User.objects.create_user(
            email="local@example.com",
            name="Local Admin",
            password="ValidLocalPassword123!",
            role=role_admin,
            active_company=test_company,
            email_verified=True,
        )

        with patch.object(SupabaseAuthClient, "is_configured", return_value=False):
            authenticated = AuthService.authenticate("local@example.com", "ValidLocalPassword123!")
            assert authenticated is not None
            assert authenticated.email == "local@example.com"


class TestFastAPISupabaseJWTIntegration:
    """Test FastAPI dependency resolution with Supabase JWT tokens."""

    @pytest.mark.django_db
    def test_deps_resolves_supabase_user(self, test_company):
        from api.deps import get_current_user
        from apps.accounts.models import Role
        role_staff, _ = Role.objects.get_or_create(name=Role.ROLE_STAFF)

        user = User.objects.create_user(
            email="api.supabase@example.com",
            name="API Supabase",
            password="StrongApiPassword123!",
            role=role_staff,
            supabase_uid="99999999-8888-7777-6666-555555555555",
            active_company=test_company,
            email_verified=True,
        )

        # Payload simulating a Supabase GoTrue access token
        supabase_payload = {
            "sub": "99999999-8888-7777-6666-555555555555",
            "email": "api.supabase@example.com",
            "aud": "authenticated",
            "role": "authenticated",
        }

        resolved_user = get_current_user(payload=supabase_payload)
        assert resolved_user.id == user.id
        assert resolved_user.email == "api.supabase@example.com"
        assert resolved_user.role.name == "staff"


class TestVercelConfiguration:
    """Test Vercel serverless entrypoints and vercel.json structure."""

    def test_vercel_json_exists_and_valid(self):
        vercel_json_path = ROOT / "vercel.json"
        assert vercel_json_path.exists()

        with open(vercel_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data.get("version") == 2
        builds = data.get("builds", [])
        srcs = [b.get("src") for b in builds]
        assert "api/index.py" in srcs
        assert "api/fastapi_entrypoint.py" in srcs

        routes = data.get("routes", [])
        destinations = [r.get("dest") for r in routes]
        assert "api/index.py" in destinations

    def test_vercel_wsgi_entrypoint_importable(self):
        import importlib.util
        wsgi_path = ROOT / "api" / "index.py"
        assert wsgi_path.exists()
        spec = importlib.util.spec_from_file_location("vercel_wsgi_app", str(wsgi_path))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert hasattr(mod, "app")
        assert callable(mod.app)

    def test_vercel_fastapi_entrypoint_importable(self):
        import importlib.util
        from fastapi import FastAPI
        asgi_path = ROOT / "api" / "fastapi_entrypoint.py"
        assert asgi_path.exists()
        spec = importlib.util.spec_from_file_location("vercel_asgi_app", str(asgi_path))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert hasattr(mod, "app")
        assert isinstance(mod.app, FastAPI)
