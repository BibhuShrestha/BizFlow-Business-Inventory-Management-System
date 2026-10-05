"""
Unit and integration tests for Part 7: Authentication & Authorization.

Covers:
- Password hashing & legacy Werkzeug migration auto-upgrade
- Role hierarchy & permissions (Admin/Owner, Manager, Staff, Customer)
- Web session authentication & role decorators
- Token-based API authentication (access/refresh tokens, expiration, revocation)
- API role-based access control (RBAC)
"""
from datetime import UTC, datetime, timedelta
import pytest
from django.contrib.auth import get_user_model
from django.test import Client, RequestFactory
from django.urls import reverse
from fastapi.testclient import TestClient
from werkzeug.security import generate_password_hash

from apps.accounts.models import Role, RevokedToken
from apps.accounts.permissions import roles_required, admin_required, manager_required, staff_required
from core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    is_token_revoked,
    revoke_token,
)
from domain.services.auth_service import AuthService
from api.main import app

User = get_user_model()


@pytest.fixture
def roles(db):
    """Ensure standard system roles exist in test database."""
    r_admin, _ = Role.objects.get_or_create(name="admin", defaults={"description": "System Admin"})
    r_owner, _ = Role.objects.get_or_create(name="owner", defaults={"description": "Company Owner"})
    r_mgr, _ = Role.objects.get_or_create(name="manager", defaults={"description": "Store Manager"})
    r_staff, _ = Role.objects.get_or_create(name="staff", defaults={"description": "Store Staff"})
    r_cust, _ = Role.objects.get_or_create(name="customer", defaults={"description": "Customer"})
    return {
        "admin": r_admin,
        "owner": r_owner,
        "manager": r_mgr,
        "staff": r_staff,
        "customer": r_cust,
    }


@pytest.fixture
def users(db, roles):
    """Create test users for each role."""
    admin_user = User.objects.create_user(
        email="admin@bizflow.com",
        name="Admin User",
        password="AdminPassword123!",
        role=roles["admin"],
        email_verified=True,
    )
    owner_user = User.objects.create_user(
        email="owner@bizflow.com",
        name="Owner User",
        password="OwnerPassword123!",
        role=roles["owner"],
        email_verified=True,
    )
    manager_user = User.objects.create_user(
        email="manager@bizflow.com",
        name="Manager User",
        password="ManagerPassword123!",
        role=roles["manager"],
        email_verified=True,
    )
    staff_user = User.objects.create_user(
        email="staff@bizflow.com",
        name="Staff User",
        password="StaffPassword123!",
        role=roles["staff"],
        email_verified=True,
    )
    customer_user = User.objects.create_user(
        email="customer@bizflow.com",
        name="Customer User",
        password="CustomerPassword123!",
        role=roles["customer"],
        email_verified=True,
    )
    return {
        "admin": admin_user,
        "owner": owner_user,
        "manager": manager_user,
        "staff": staff_user,
        "customer": customer_user,
    }


# ==============================================================================
# 1. Password Hashing & Legacy Werkzeug Compatibility
# ==============================================================================
class TestPasswordHashingAndMigration:
    """Tests password hashing security and Werkzeug legacy hash auto-upgrade."""

    def test_legacy_werkzeug_hash_verification_and_auto_upgrade(self, db, roles):
        """Legacy Werkzeug scrypt/pbkdf2 hash verifies and auto-upgrades to Django PBKDF2."""
        werkzeug_hash = generate_password_hash("FlaskLegacyPwd123!")
        assert werkzeug_hash.startswith("scrypt:") or werkzeug_hash.startswith("pbkdf2:")

        user = User(
            email="migrated@flask.com",
            name="Migrated User",
            password=werkzeug_hash,
            role=roles["staff"],
            email_verified=True,
            is_active=True,
        )
        user.save()

        # Initial password in db is Werkzeug format
        assert user.password == werkzeug_hash

        # Verification succeeds
        assert user.check_password("FlaskLegacyPwd123!") is True

        # Refresh from database: hash must have been auto-upgraded to Django PBKDF2
        user.refresh_from_db()
        assert user.password != werkzeug_hash
        assert "$" in user.password and not user.password.startswith("scrypt:") and not user.password.startswith("FlaskLegacy")

        # Second verification with upgraded hash still succeeds
        assert user.check_password("FlaskLegacyPwd123!") is True

    def test_invalid_password_rejected(self, db, users):
        """Wrong password check returns False."""
        user = users["staff"]
        assert user.check_password("WrongPassword123!") is False

    def test_passwords_never_stored_plain(self, db, users):
        """Database stores hashed passwords, never plain strings."""
        for role_name, user in users.items():
            assert "AdminPassword123!" not in user.password
            assert "StaffPassword123!" not in user.password
            assert "$" in user.password and not user.password.startswith("scrypt:") and not user.password.startswith("FlaskLegacy")


# ==============================================================================
# 2. Role Hierarchy & Permissions
# ==============================================================================
class TestRoleHierarchyAndPermissions:
    """Verifies that Flask roles are preserved and permissions correctly enforced."""

    def test_role_properties(self, db, users):
        """Verify role flags match hierarchy."""
        admin = users["admin"]
        owner = users["owner"]
        manager = users["manager"]
        staff = users["staff"]
        customer = users["customer"]

        # Admin / Owner
        assert admin.is_admin is True
        assert admin.is_manager is True
        assert admin.is_staff_member is True
        assert admin.is_customer is False

        assert owner.is_admin is True
        assert owner.is_manager is True
        assert owner.is_staff_member is True

        # Manager
        assert manager.is_admin is False
        assert manager.is_manager is True
        assert manager.is_staff_member is True
        assert manager.is_customer is False

        # Staff
        assert staff.is_admin is False
        assert staff.is_manager is False
        assert staff.is_staff_member is True
        assert staff.is_customer is False

        # Customer
        assert customer.is_admin is False
        assert customer.is_manager is False
        assert customer.is_staff_member is False
        assert customer.is_customer is True

    def test_has_role_method(self, db, users):
        """Verify has_role method logic."""
        admin = users["admin"]
        manager = users["manager"]
        staff = users["staff"]

        # Admin always matches any role check
        assert admin.has_role("staff") is True
        assert admin.has_role("manager") is True
        assert admin.has_role("custom_role") is True

        # Manager matches manager and higher
        assert manager.has_role("manager") is True
        assert manager.has_role("admin") is False

        # Staff matches staff only
        assert staff.has_role("staff") is True
        assert staff.has_role("manager") is False


# ==============================================================================
# 3. Web Session Authentication (Django)
# ==============================================================================
class TestWebSessionAuthentication:
    """Tests Django session login, logout, and role decorators."""

    def test_web_login_and_session_creation(self, db, users):
        """Logging in via web form sets session cookie and redirects."""
        client = Client()
        response = client.post(
            "/auth/login/",
            {"email": "staff@bizflow.com", "password": "StaffPassword123!"},
            follow=False,
        )
        # Should redirect to dashboard
        assert response.status_code == 302
        assert response["Location"] == "dashboard:index" or "/dashboard" in response["Location"]
        assert client.session.get("_auth_user_id") == str(users["staff"].id)

    def test_web_login_invalid_credentials(self, db, users):
        """Invalid credentials show error and do not set session."""
        client = Client()
        response = client.post(
            "/auth/login/",
            {"email": "staff@bizflow.com", "password": "WrongPassword!"},
        )
        assert response.status_code == 200
        assert "_auth_user_id" not in client.session

    def test_web_logout(self, db, users):
        """Logout terminates session and redirects to login."""
        client = Client()
        client.force_login(users["staff"])
        assert client.session.get("_auth_user_id") == str(users["staff"].id)

        response = client.get("/auth/logout/", follow=False)
        assert response.status_code == 302
        assert client.session.get("_auth_user_id") is None

    def test_web_role_permission_decorator(self, db, users):
        """roles_required decorator permits allowed role and redirects unauthorized."""
        from django.http import HttpResponse

        @manager_required
        def dummy_manager_view(request):
            return HttpResponse("Manager Area")

        factory = RequestFactory()

        # 1. Admin accessing manager view -> Allowed
        req_admin = factory.get("/test-view/")
        req_admin.user = users["admin"]
        resp_admin = dummy_manager_view(req_admin)
        assert resp_admin.status_code == 200
        assert resp_admin.content == b"Manager Area"

        # 2. Staff accessing manager view -> Denied and redirected
        req_staff = factory.get("/test-view/")
        req_staff.user = users["staff"]
        # Add session and messages support for factory
        from django.contrib.sessions.middleware import SessionMiddleware
        from django.contrib.messages.middleware import MessageMiddleware
        sm = SessionMiddleware(lambda r: None)
        sm.process_request(req_staff)
        mm = MessageMiddleware(lambda r: None)
        mm.process_request(req_staff)

        resp_staff = dummy_manager_view(req_staff)
        assert resp_staff.status_code == 302
        assert "dashboard" in resp_staff["Location"]


# ==============================================================================
# 4. Token-Based Authentication for API Clients (FastAPI)
# ==============================================================================
@pytest.mark.django_db(transaction=True)
class TestAPITokenAuthentication:
    """Tests JWT authentication, refresh flow, expiration, and revocation."""

    def test_api_login_returns_jwt_tokens(self, db, users):
        """POST /api/v1/auth/login returns access token and refresh token."""
        client = TestClient(app)
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "staff@bizflow.com", "password": "StaffPassword123!"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "staff@bizflow.com"
        assert data["user"]["role"] == "staff"

    def test_api_get_me_with_bearer_token(self, db, users):
        """GET /api/v1/auth/me returns current user info when valid token provided."""
        client = TestClient(app)
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@bizflow.com", "password": "AdminPassword123!"},
        )
        token = login_resp.json()["access_token"]

        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "admin@bizflow.com"
        assert data["role"] == "admin"

    def test_api_refresh_token_flow(self, db, users):
        """POST /api/v1/auth/refresh issues a fresh access token."""
        client = TestClient(app)
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": "manager@bizflow.com", "password": "ManagerPassword123!"},
        )
        refresh_token = login_resp.json()["refresh_token"]

        refresh_resp = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_resp.status_code == 200
        data = refresh_resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_api_logout_revokes_tokens(self, db, users):
        """POST /api/v1/auth/logout revokes access token; subsequent calls fail with 401."""
        client = TestClient(app)
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": "staff@bizflow.com", "password": "StaffPassword123!"},
        )
        access_token = login_resp.json()["access_token"]

        # Verified before logout
        me_resp1 = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"})
        assert me_resp1.status_code == 200

        # Logout
        logout_resp = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert logout_resp.status_code == 200

        # Subsequent call with revoked token must fail with 401
        me_resp2 = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"})
        assert me_resp2.status_code == 401
        assert "revoked" in me_resp2.json()["detail"].lower()

    def test_api_unauthenticated_request_rejected(self, db):
        """Protected endpoint rejects missing or invalid token with 401."""
        client = TestClient(app)
        res1 = client.get("/api/v1/auth/me")
        assert res1.status_code == 401

        res2 = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid.jwt.token"})
        assert res2.status_code == 401
# ==============================================================================
# 5. Role-Based Access Control on API Endpoints
# ==============================================================================
@pytest.mark.django_db(transaction=True)
class TestAPIRoleBasedAccessControl:
    """Verifies RBAC enforcement on API routes using require_role/require_admin."""

    def test_admin_endpoint_access_control(self, db, users):
        """Admin/Owner allowed access, Staff/Customer rejected with 403 Forbidden."""
        from fastapi import APIRouter, Depends
        from api.deps import require_admin, require_manager, require_staff

        test_router = APIRouter(prefix="/api/v1/test-rbac")

        @test_router.get("/admin-only")
        def admin_route(user=Depends(require_admin)):
            return {"status": "ok", "user": user.email}

        @test_router.get("/manager-only")
        def manager_route(user=Depends(require_manager)):
            return {"status": "ok", "user": user.email}

        @test_router.get("/staff-only")
        def staff_route(user=Depends(require_staff)):
            return {"status": "ok", "user": user.email}

        app.include_router(test_router)
        client = TestClient(app)

        # Log in users to get tokens
        def get_token(email, pwd):
            resp = client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
            return resp.json()["access_token"]

        admin_token = get_token("admin@bizflow.com", "AdminPassword123!")
        owner_token = get_token("owner@bizflow.com", "OwnerPassword123!")
        manager_token = get_token("manager@bizflow.com", "ManagerPassword123!")
        staff_token = get_token("staff@bizflow.com", "StaffPassword123!")
        customer_token = get_token("customer@bizflow.com", "CustomerPassword123!")

        # 1. Admin route: Admin and Owner -> 200; Manager, Staff, Customer -> 403
        assert client.get("/api/v1/test-rbac/admin-only", headers={"Authorization": f"Bearer {admin_token}"}).status_code == 200
        assert client.get("/api/v1/test-rbac/admin-only", headers={"Authorization": f"Bearer {owner_token}"}).status_code == 200
        assert client.get("/api/v1/test-rbac/admin-only", headers={"Authorization": f"Bearer {manager_token}"}).status_code == 403
        assert client.get("/api/v1/test-rbac/admin-only", headers={"Authorization": f"Bearer {staff_token}"}).status_code == 403
        assert client.get("/api/v1/test-rbac/admin-only", headers={"Authorization": f"Bearer {customer_token}"}).status_code == 403

        # 2. Manager route: Admin, Owner, Manager -> 200; Staff, Customer -> 403
        assert client.get("/api/v1/test-rbac/manager-only", headers={"Authorization": f"Bearer {manager_token}"}).status_code == 200
        assert client.get("/api/v1/test-rbac/manager-only", headers={"Authorization": f"Bearer {staff_token}"}).status_code == 403

        # 3. Staff route: Admin, Owner, Manager, Staff -> 200; Customer -> 403
        assert client.get("/api/v1/test-rbac/staff-only", headers={"Authorization": f"Bearer {staff_token}"}).status_code == 200
        assert client.get("/api/v1/test-rbac/staff-only", headers={"Authorization": f"Bearer {customer_token}"}).status_code == 403


# ==============================================================================
# 6. Email Verification & Password Reset Flows
# ==============================================================================
class TestAuthFlows:
    """Verifies end-to-end registration, email verification, and password reset flows."""

    def test_registration_and_verification_flow(self, db):
        """Registering user creates inactive account and token; verification activates it."""
        user, raw_token = AuthService.register(
            name="New Employee",
            email="employee@bizflow.com",
            password="SecurePassword123!",
        )
        assert user.is_active is False
        assert user.email_verified is False
        assert user.role_name == "staff"

        # Verify email with token
        verified_user = AuthService.verify_email(raw_token)
        assert verified_user.is_active is True
        assert verified_user.email_verified is True

        # Reusing the token must fail
        with pytest.raises(Exception):
            AuthService.verify_email(raw_token)

    def test_password_reset_flow(self, db, users):
        """Request reset creates token, resetting updates password and invalidates token."""
        user = users["staff"]
        result = AuthService.request_password_reset("staff@bizflow.com")
        assert result is not None
        req_user, raw_token = result

        # Reset password
        updated_user = AuthService.reset_password(raw_token, "NewStaffPassword123!")
        assert updated_user.check_password("NewStaffPassword123!") is True
        assert updated_user.check_password("StaffPassword123!") is False

        # Reusing token must fail
        with pytest.raises(Exception):
            AuthService.reset_password(raw_token, "AnotherPassword123!")
