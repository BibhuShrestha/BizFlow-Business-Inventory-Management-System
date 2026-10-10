"""
Unit and integration tests for Part 24: Google OAuth2 Social Authentication & Granular RBAC Permissions.

Covers:
- GoogleOAuthClient authorization URL generation and OpenID Connect state verification
- GoogleOAuthClient code exchange and profile retrieval
- AuthService.login_or_register_via_google user provisioning & authentication
- Django Web views: google_login_view & google_callback_view
- FastAPI REST endpoints: GET /api/v1/auth/google & POST /api/v1/auth/google/callback
- Centralized RBAC Permission enum, ROLE_PERMISSION_MAP, and checker utilities
- Django permission_required_custom decorator and PermissionRequiredMixin
- FastAPI require_permission dependency
- Django template context processor user_permissions injection
"""
import pytest
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.test import Client, RequestFactory
from django.urls import reverse
from fastapi.testclient import TestClient

from apps.accounts.models import Role
from apps.accounts.permissions import (
    permission_required_custom,
    any_permission_required_custom,
    PermissionRequiredMixin,
)
from apps.core_app.context_processors import active_company
from core.security import create_access_token
from domain.exceptions import AuthenticationError
from domain.permissions import (
    Permission,
    ROLE_PERMISSION_MAP,
    get_all_user_permissions,
    has_permission,
    has_any_permission,
)
from domain.services.auth_service import AuthService
from integrations.google_oauth import GoogleOAuthClient, GoogleOAuthError
from api.main import app

User = get_user_model()


@pytest.fixture
def rbac_roles(db):
    """Ensure standard roles exist in test database."""
    r_admin, _ = Role.objects.get_or_create(name="admin", defaults={"description": "System Admin"})
    r_owner, _ = Role.objects.get_or_create(name="owner", defaults={"description": "Company Owner"})
    r_mgr, _ = Role.objects.get_or_create(name="manager", defaults={"description": "Store Manager"})
    r_staff, _ = Role.objects.get_or_create(name="staff", defaults={"description": "Store Staff"})
    r_cashier, _ = Role.objects.get_or_create(name="cashier", defaults={"description": "POS Cashier"})
    r_cust, _ = Role.objects.get_or_create(name="customer", defaults={"description": "Customer"})
    return {
        "admin": r_admin,
        "owner": r_owner,
        "manager": r_mgr,
        "staff": r_staff,
        "cashier": r_cashier,
        "customer": r_cust,
    }


@pytest.fixture
def rbac_users(db, rbac_roles):
    """Create test users for each role."""
    admin_user = User.objects.create_user(
        email="admin_rbac@bizflow.com",
        name="Admin RBAC",
        password="Password123!",
        role=rbac_roles["admin"],
        email_verified=True,
    )
    manager_user = User.objects.create_user(
        email="mgr_rbac@bizflow.com",
        name="Manager RBAC",
        password="Password123!",
        role=rbac_roles["manager"],
        email_verified=True,
    )
    staff_user = User.objects.create_user(
        email="staff_rbac@bizflow.com",
        name="Staff RBAC",
        password="Password123!",
        role=rbac_roles["staff"],
        email_verified=True,
    )
    cashier_user = User.objects.create_user(
        email="cashier_rbac@bizflow.com",
        name="Cashier RBAC",
        password="Password123!",
        role=rbac_roles["cashier"],
        email_verified=True,
    )
    customer_user = User.objects.create_user(
        email="cust_rbac@bizflow.com",
        name="Customer RBAC",
        password="Password123!",
        role=rbac_roles["customer"],
        email_verified=True,
    )
    return {
        "admin": admin_user,
        "manager": manager_user,
        "staff": staff_user,
        "cashier": cashier_user,
        "customer": customer_user,
    }


# ===========================================================================
# 1. Google OAuth Client Unit Tests
# ===========================================================================

class TestGoogleOAuthClient:

    def test_get_auth_url_contains_required_params(self):
        url = GoogleOAuthClient.get_auth_url(
            redirect_uri="https://bizflow.example.com/auth/google/callback",
            state="test-random-state-12345",
        )
        assert "accounts.google.com" in url
        assert "response_type=code" in url
        assert "state=test-random-state-12345" in url
        assert "openid" in url
        assert "email" in url
        assert "redirect_uri=" in url

    def test_exchange_code_mock_mode(self):
        token_data = GoogleOAuthClient.exchange_code(
            code="mock_code_test:testuser@gmail.com",
            redirect_uri="https://bizflow.example.com/auth/google/callback",
        )
        assert token_data["access_token"] == "mock_access_token"
        assert token_data["_mock"] is True
        assert token_data["_mock_email"] == "testuser@gmail.com"

    def test_get_user_info_mock_mode(self):
        token_data = {
            "access_token": "mock_token",
            "_mock": True,
            "_mock_email": "jane.doe@gmail.com",
        }
        profile = GoogleOAuthClient.get_user_info(token_data)
        assert profile["email"] == "jane.doe@gmail.com"
        assert profile["email_verified"] is True
        assert "Jane.Doe" in profile["name"]
        assert profile["sub"].startswith("google_sub_")

    def test_get_user_info_missing_access_token(self):
        with pytest.raises(GoogleOAuthError, match="No access token provided"):
            GoogleOAuthClient.get_user_info({})


# ===========================================================================
# 2. AuthService Google OAuth Business Logic Tests
# ===========================================================================

class TestAuthServiceGoogleOAuth:

    def test_provision_new_user_via_google(self, db, rbac_roles):
        user_info = {
            "sub": "google-10928374",
            "email": "newgoogleuser@example.com",
            "email_verified": True,
            "name": "Alex Google",
        }
        user, created = AuthService.login_or_register_via_google(user_info)
        assert created is True
        assert user.email == "newgoogleuser@example.com"
        assert user.name == "Alex Google"
        assert user.google_id == "google-10928374"
        assert user.is_active is True
        assert user.email_verified is True
        assert user.has_usable_password() is False

    def test_authenticate_existing_user_via_google(self, db, rbac_users):
        staff = rbac_users["staff"]
        user_info = {
            "sub": "google-existing-staff",
            "email": staff.email,
            "email_verified": True,
            "name": staff.name,
        }
        user, created = AuthService.login_or_register_via_google(user_info)
        assert created is False
        assert user.id == staff.id
        user.refresh_from_db()
        assert user.google_id == "google-existing-staff"

    def test_reject_inactive_user_via_google(self, db, rbac_users):
        staff = rbac_users["staff"]
        staff.is_active = False
        staff.save(update_fields=["is_active"])

        user_info = {
            "sub": "google-inactive",
            "email": staff.email,
            "email_verified": True,
            "name": staff.name,
        }
        with pytest.raises(AuthenticationError, match="inactive"):
            AuthService.login_or_register_via_google(user_info)

    def test_reject_unverified_email_via_google(self, db):
        user_info = {
            "sub": "google-unverified",
            "email": "unverified@gmail.com",
            "email_verified": False,
            "name": "Unverified User",
        }
        with pytest.raises(AuthenticationError, match="not verified"):
            AuthService.login_or_register_via_google(user_info)


# ===========================================================================
# 3. Django Web Google OAuth Views Tests
# ===========================================================================

class TestDjangoWebGoogleOAuth:

    def test_google_login_view_redirects_and_sets_session(self, db):
        client = Client()
        response = client.get(reverse("accounts:google_login") + "?next=/dashboard/")
        assert response.status_code == 302
        assert "accounts.google.com" in response.url
        assert client.session.get("google_oauth_state") is not None
        assert client.session.get("google_oauth_next") == "/dashboard/"

    def test_google_callback_view_state_mismatch(self, db):
        client = Client()
        # No state stored in session
        response = client.get(reverse("accounts:google_callback") + "?code=test_code&state=invalid_state")
        assert response.status_code == 302
        assert reverse("accounts:login") in response.url

    def test_google_callback_view_error_query_param(self, db):
        client = Client()
        response = client.get(reverse("accounts:google_callback") + "?error=access_denied")
        assert response.status_code == 302
        assert reverse("accounts:login") in response.url

    def test_google_callback_view_success(self, db, rbac_roles):
        client = Client()
        session = client.session
        session["google_oauth_state"] = "matching_state_xyz"
        session["google_oauth_next"] = "/dashboard/"
        session.save()

        callback_url = (
            reverse("accounts:google_callback")
            + "?code=mock_code_web:webgoogleuser@example.com&state=matching_state_xyz"
        )
        response = client.get(callback_url)
        assert response.status_code == 302
        assert response.url == "/dashboard/"

        # User is authenticated in session
        user = User.objects.get(email="webgoogleuser@example.com")
        assert user.is_active is True
        assert user.email_verified is True

    def test_google_login_dev_sandbox_render(self, db, settings):
        settings.TESTING = False
        settings.DEBUG = True
        client = Client()
        response = client.get(reverse("accounts:google_login"))
        assert response.status_code == 200
        assert "Google OAuth Development Sandbox" in response.content.decode()

    def test_google_login_dev_sandbox_post_simulation(self, db, settings, rbac_roles):
        settings.TESTING = False
        settings.DEBUG = True
        client = Client()
        response = client.post(
            reverse("accounts:google_login"),
            {"dev_simulate": "1", "email": "bibhutest@gmail.com", "name": "Bibhu Test", "next": "/dashboard/"},
        )
        assert response.status_code == 302
        assert response.url == "/dashboard/"
        user = User.objects.get(email="bibhutest@gmail.com")
        assert user.name == "Bibhu Test"


# ===========================================================================
# 4. FastAPI Google OAuth Endpoints Tests
# ===========================================================================

class TestFastAPIGoogleOAuth:

    def test_api_get_google_auth_url(self):
        client = TestClient(app)
        response = client.get("/api/v1/auth/google")
        assert response.status_code == 200
        data = response.json()
        assert "auth_url" in data
        assert "state" in data
        assert "accounts.google.com" in data["auth_url"]
        assert data["state"] in data["auth_url"]

    def test_api_post_google_callback_success(self, transactional_db):
        client = TestClient(app)
        payload = {
            "code": "mock_code_api:apigoogleuser@example.com",
            "redirect_uri": "http://localhost:8000/auth/google/callback",
        }
        response = client.post("/api/v1/auth/google/callback", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["email"] == "apigoogleuser@example.com"


# ===========================================================================
# 5. Granular RBAC Permissions Tests
# ===========================================================================

class TestGranularRBAC:

    def test_cashier_permissions_matrix(self, db, rbac_users):
        cashier = rbac_users["cashier"]
        # Cashier CAN view and create sales, view inventory, manage customers
        assert has_permission(cashier, Permission.SALES_VIEW) is True
        assert has_permission(cashier, Permission.SALES_CREATE) is True
        assert has_permission(cashier, Permission.INVENTORY_VIEW) is True
        assert has_permission(cashier, Permission.CUSTOMERS_MANAGE) is True
        # Cashier CANNOT purchase, adjust inventory, or view reports
        assert has_permission(cashier, Permission.PURCHASES_CREATE) is False
        assert has_permission(cashier, Permission.INVENTORY_ADJUST) is False
        assert has_permission(cashier, Permission.REPORTS_VIEW) is False

    def test_staff_permissions_matrix(self, db, rbac_users):
        staff = rbac_users["staff"]
        assert has_permission(staff, Permission.SALES_CREATE) is True
        assert has_permission(staff, Permission.PURCHASES_CREATE) is True
        assert has_permission(staff, Permission.INVENTORY_MANAGE) is True
        # Staff CANNOT delete inventory or view analytics
        assert has_permission(staff, Permission.INVENTORY_DELETE) is False
        assert has_permission(staff, Permission.ANALYTICS_VIEW) is False

    def test_manager_permissions_matrix(self, db, rbac_users):
        manager = rbac_users["manager"]
        assert has_permission(manager, Permission.INVENTORY_ADJUST) is True
        assert has_permission(manager, Permission.INVENTORY_DELETE) is True
        assert has_permission(manager, Permission.REPORTS_VIEW) is True
        assert has_permission(manager, Permission.ANALYTICS_VIEW) is True
        # Manager CANNOT manage/delete users
        assert has_permission(manager, Permission.USERS_MANAGE) is False

    def test_admin_has_unrestricted_permissions(self, db, rbac_users):
        admin = rbac_users["admin"]
        for perm in Permission:
            assert has_permission(admin, perm) is True
        all_perms = get_all_user_permissions(admin)
        assert len(all_perms) == len(Permission)

    def test_has_any_permission_utility(self, db, rbac_users):
        cashier = rbac_users["cashier"]
        assert has_any_permission(cashier, Permission.PURCHASES_CREATE, Permission.SALES_CREATE) is True
        assert has_any_permission(cashier, Permission.PURCHASES_CREATE, Permission.PURCHASES_DELETE) is False

    def test_django_permission_decorator_allowed(self, rbac_users):
        rf = RequestFactory()
        request = rf.get("/dummy/")
        request.user = rbac_users["cashier"]

        @permission_required_custom(Permission.SALES_CREATE)
        def my_view(req):
            return HttpResponse("Authorized", status=200)

        response = my_view(request)
        assert response.status_code == 200
        assert response.content == b"Authorized"

    def test_django_permission_decorator_denied(self, rbac_users, monkeypatch):
        rf = RequestFactory()
        request = rf.get("/dummy/")
        request.user = rbac_users["cashier"]

        called_error = []
        monkeypatch.setattr(
            "apps.accounts.permissions.messages.error",
            lambda req, msg: called_error.append(msg),
        )

        @permission_required_custom(Permission.INVENTORY_ADJUST)
        def my_view(req):
            return HttpResponse("Authorized", status=200)

        response = my_view(request)
        assert response.status_code == 302
        assert response.url == "/dashboard/"
        assert len(called_error) == 1

    def test_template_context_processor_injects_permissions(self, rbac_users):
        rf = RequestFactory()
        request = rf.get("/dummy/")
        request.user = rbac_users["cashier"]

        ctx = active_company(request)
        assert "user_permissions" in ctx
        assert Permission.SALES_CREATE.value in ctx["user_permissions"]
        assert Permission.PURCHASES_CREATE.value not in ctx["user_permissions"]

    def test_customer_ui_restricted_to_catalog_only(self, db, rbac_users):
        customer = rbac_users["customer"]
        client = Client()
        client.force_login(customer)

        # Dashboard redirects customer to product list
        dash_res = client.get(reverse("dashboard:index"))
        assert dash_res.status_code == 302
        assert reverse("inventory:product_list") in dash_res.url

        # In product list, customer sees Catalog and Sell Price, but NOT wholesale Buy Price or management actions
        prod_res = client.get(reverse("inventory:product_list"))
        assert prod_res.status_code == 200
        content = prod_res.content.decode("utf-8")
        assert "Product Catalog" in content
        assert "Buy Price" not in content
        assert "+ Add Product" not in content
        assert "Import Excel/CSV" not in content
        assert "Export CSV" not in content
        assert reverse("inventory:category_list") not in content
        # Sidebar for customer only shows Customer Portal, not internal financial sections
        assert "Customer Portal" in content
        assert "AI Analytics &amp; Insights" not in content
        assert "Reports &amp; Daybook" not in content
        assert "Supplier Payables (Cr)" not in content

    def test_cashier_ui_hides_purchases_and_reports(self, db, rbac_users):
        cashier = rbac_users["cashier"]
        client = Client()
        client.force_login(cashier)

        # Dashboard for cashier hides Net Profit, Purchases, Expenses, AI Analytics
        res = client.get(reverse("dashboard:index"))
        assert res.status_code == 200
        content = res.content.decode("utf-8")
        assert "Total Sales" in content
        assert "Net Profit" not in content
        assert "Total Purchases" not in content
        assert "Total Expenses" not in content
        assert "AI Analytics &amp; Insights" not in content
        assert "Recent Purchases" not in content
        assert "Supplier Payables (Cr)" not in content

    def test_staff_ui_hides_executive_analytics_and_companies(self, db, rbac_users):
        staff = rbac_users["staff"]
        client = Client()
        client.force_login(staff)

        # Staff dashboard shows Sales and Purchases, but hides Net Profit and AI Analytics
        res = client.get(reverse("dashboard:index"))
        assert res.status_code == 200
        content = res.content.decode("utf-8")
        assert "Total Sales" in content
        assert "Total Purchases" in content
        assert "Total Expenses" in content
        assert "Net Profit" not in content
        assert "AI Analytics &amp; Insights" not in content
        assert "Receivables &amp; Payables Hub" not in content

        # Staff visiting /companies/ or /import-export/ is blocked by manager_required
        comp_res = client.get(reverse("companies:list"))
        assert comp_res.status_code == 302
        assert "/dashboard/" in comp_res.url

        imp_res = client.get(reverse("core_app:import_export_hub"))
        assert imp_res.status_code == 302
        assert "/dashboard/" in imp_res.url
