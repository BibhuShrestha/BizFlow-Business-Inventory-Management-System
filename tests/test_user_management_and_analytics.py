"""
Test Suite: Admin User Management, Online/Offline Activity Visibility, and Business Analytics Accuracy.

Verifies:
- Root cause fix for admin user creation and immediate visibility in /users/ list.
- Field validation error handling and duplicate prevention.
- Online presence calculation and lightweight middleware activity touch.
- Exact financial definitions: Revenue vs Cash Collected vs Receivables vs COGS vs Net Profit vs Cash Flow.
- Intelligent inventory reorder suggestions.
- Period and date range filtering.
- RBAC protection (non-admin blocked from user management).
- Comprehensive analytics CSV export.
"""
from datetime import timedelta
from decimal import Decimal
import pytest
from django.test import Client, RequestFactory
from django.utils import timezone

from apps.accounts.models import User, Role
from apps.accounts.middleware import UserActivityMiddleware
from apps.companies.models import Company
from apps.inventory.models import Category, Product
from apps.sales.models import Sale, SaleItem, Payment, Customer
from apps.purchases.models import Purchase, PurchaseItem, Supplier
from apps.accounting.models import Expense
from domain.services.analytics_service import AnalyticsService


@pytest.fixture
def enterprise_setup(db):
    """Setup multi-tenant company, admin, staff, catalog, and customers."""
    admin_role, _ = Role.objects.get_or_create(name="admin", defaults={"description": "Administrator"})
    manager_role, _ = Role.objects.get_or_create(name="manager", defaults={"description": "Manager"})
    staff_role, _ = Role.objects.get_or_create(name="staff", defaults={"description": "Staff"})

    company = Company.objects.create(
        company_name="Apex Global Ltd",
        company_phone="9801122334",
        vat_pan_number="998877665",
    )

    admin = User.objects.create_user(
        email="admin@apex.com",
        name="Apex Admin",
        password="SuperPassword123!",
        role=admin_role,
        is_staff=True,
        is_superuser=True,
        active_company=company,
    )

    staff = User.objects.create_user(
        email="cashier@apex.com",
        name="Cashier User",
        password="SuperPassword123!",
        role=staff_role,
        is_staff=False,
        active_company=company,
    )

    cat = Category.objects.create(name="Electronics")

    # Product A: High stock, sold in period
    p_gadget = Product.objects.create(
        name="Wireless Router",
        sku="ROUTER-01",
        current_stock=25,
        minimum_stock=10,
        purchase_price=Decimal("1500.00"),
        selling_price=Decimal("2500.00"),
        category=cat,
        company=company,
    )

    # Product B: Low stock, below threshold -> should trigger reorder suggestion
    p_cable = Product.objects.create(
        name="Cat6 Ethernet Cable",
        sku="CABLE-02",
        current_stock=4,
        minimum_stock=15,
        purchase_price=Decimal("200.00"),
        selling_price=Decimal("450.00"),
        category=cat,
        company=company,
    )

    customer = Customer.objects.create(name="Skyline Corp", phone="9851000000", company=company)
    supplier = Supplier.objects.create(name="Tech Distributors", phone="9852000000", company=company)

    return {
        "company": company,
        "admin": admin,
        "staff": staff,
        "admin_role": admin_role,
        "manager_role": manager_role,
        "staff_role": staff_role,
        "p_gadget": p_gadget,
        "p_cable": p_cable,
        "customer": customer,
        "supplier": supplier,
    }


class TestAdminUserManagement:
    """Verifies user creation, immediate visibility, validation errors, and permissions."""

    def test_admin_created_user_immediately_appears_in_user_list(self, enterprise_setup):
        """Root cause test: Newly created user must be persisted and rendered in the admin user table."""
        client = Client()
        client.force_login(enterprise_setup["admin"])

        # 1. Create a new staff user via POST
        create_payload = {
            "name": "Binod Sharma",
            "email": "binod@apex.com",
            "phone": "9812345678",
            "role": enterprise_setup["staff_role"].id,
            "active_company": enterprise_setup["company"].id,
            "password": "StrongPassword999!",
            "is_active": "on",
        }
        res_post = client.post("/users/create/", create_payload, follow=True)
        assert res_post.status_code == 200

        # 2. Verify database record exists
        new_user = User.objects.filter(email="binod@apex.com").first()
        assert new_user is not None
        assert new_user.name == "Binod Sharma"
        assert new_user.is_active is True
        assert new_user.check_password("StrongPassword999!") is True

        # 3. Verify user immediately renders in /users/ list without empty table
        res_list = client.get("/users/")
        assert res_list.status_code == 200
        assert b"Binod Sharma" in res_list.content
        assert b"binod@apex.com" in res_list.content
        assert b"No users found" not in res_list.content

    def test_duplicate_email_rejected_with_field_error(self, enterprise_setup):
        """Duplicate emails must be rejected with informative validation feedback."""
        client = Client()
        client.force_login(enterprise_setup["admin"])

        payload = {
            "name": "Imposter Admin",
            "email": "admin@apex.com",  # Already exists
            "phone": "9800000000",
            "role": enterprise_setup["staff_role"].id,
            "password": "StrongPassword999!",
            "is_active": "on",
        }
        res = client.post("/users/create/", payload)
        assert res.status_code == 200  # Re-renders form
        assert b"already exists" in res.content

    def test_weak_password_rejected(self, enterprise_setup):
        """Passwords not meeting complexity standards must be rejected."""
        client = Client()
        client.force_login(enterprise_setup["admin"])

        payload = {
            "name": "Weak User",
            "email": "weak@apex.com",
            "role": enterprise_setup["staff_role"].id,
            "password": "weak",
            "is_active": "on",
        }
        res = client.post("/users/create/", payload)
        assert res.status_code == 200
        assert b"Password" in res.content

    def test_non_admin_cannot_access_user_management(self, enterprise_setup):
        """Staff and non-admin users must be rejected from user management."""
        client = Client()
        client.force_login(enterprise_setup["staff"])

        res_list = client.get("/users/")
        assert res_list.status_code in (302, 403)

        res_create = client.get("/users/create/")
        assert res_create.status_code in (302, 403)

    def test_toggle_user_account_status(self, enterprise_setup):
        """Admin can deactivate and reactivate an account."""
        client = Client()
        client.force_login(enterprise_setup["admin"])
        staff = enterprise_setup["staff"]

        # Deactivate
        res_deact = client.post(f"/users/{staff.id}/delete/", {"action": "deactivate"}, follow=True)
        assert res_deact.status_code == 200
        staff.refresh_from_db()
        assert staff.is_active is False

        # Reactivate
        res_act = client.post(f"/users/{staff.id}/delete/", {"action": "activate"}, follow=True)
        assert res_act.status_code == 200
        staff.refresh_from_db()
        assert staff.is_active is True


class TestUserActivityAndOnlinePresence:
    """Verifies online vs offline presence logic and middleware touch."""

    def test_online_vs_offline_property_calculation(self, enterprise_setup):
        user = enterprise_setup["staff"]

        # 1. No last_activity -> Offline
        user.last_activity = None
        user.save()
        assert user.is_online is False
        assert user.online_status_label == "Offline"

        # 2. Activity within 10 minutes -> Online
        user.last_activity = timezone.now() - timedelta(minutes=10)
        user.save()
        assert user.is_online is True
        assert user.online_status_label == "Online"

        # 3. Activity 45 minutes ago (> 15m timeout) -> Offline
        user.last_activity = timezone.now() - timedelta(minutes=45)
        user.save()
        assert user.is_online is False
        assert user.online_status_label == "Offline"

    def test_user_activity_middleware_throttled_touch(self, enterprise_setup):
        """Middleware updates last_activity with in-session throttling."""
        rf = RequestFactory()
        request = rf.get("/")
        request.user = enterprise_setup["staff"]
        request.session = {}

        middleware = UserActivityMiddleware(lambda req: req)
        middleware(request)

        # Session ping and DB should be updated
        assert "last_activity_ping" in request.session
        enterprise_setup["staff"].refresh_from_db()
        assert enterprise_setup["staff"].last_activity is not None

    def test_user_list_online_filter(self, enterprise_setup):
        """Filtering by online and offline returns correct subsets."""
        admin = enterprise_setup["admin"]
        staff = enterprise_setup["staff"]

        admin.last_activity = timezone.now()
        admin.save()
        staff.last_activity = timezone.now() - timedelta(hours=2)
        staff.save()

        client = Client()
        client.force_login(admin)

        # Filter online
        res_online = client.get("/users/?online=online")
        assert res_online.status_code == 200
        assert admin.name.encode() in res_online.content

        # Filter offline
        res_offline = client.get("/users/?online=offline")
        assert res_offline.status_code == 200
        assert staff.name.encode() in res_offline.content


class TestBusinessAnalyticsAccuracyAndAccounting:
    """Verifies accurate financial calculations, COGS, cash flow, and reorder alerts."""

    def test_revenue_vs_cash_received_distinction(self, enterprise_setup):
        """Crucial requirement: Unpaid credit sales must NOT be counted as Cash Received."""
        company = enterprise_setup["company"]
        customer = enterprise_setup["customer"]
        p_gadget = enterprise_setup["p_gadget"]

        # Create an unpaid credit sale of Rs. 5,000
        sale = Sale.objects.create(
            invoice_number="INV-TEST-CREDIT",
            customer=customer,
            total=Decimal("5000.00"),
            payment_status=Sale.STATUS_DUE,
            sale_date=timezone.now(),
            company=company,
        )
        SaleItem.objects.create(
            sale=sale,
            product=p_gadget,
            quantity=2,
            unit_price=Decimal("2500.00"),
            total=Decimal("5000.00"),
        )

        # Fetch analytics
        analytics = AnalyticsService.get_business_analytics(company_id=company.id, days=30)

        # Revenue is Rs. 5000, but Cash Received must be Rs. 0!
        assert analytics["revenue"] == Decimal("5000.00")
        assert analytics["cash_received"] == Decimal("0.00")
        assert analytics["receivables_total"] == Decimal("5000.00")
        assert analytics["collection_rate_pct"] == 0.0

        # Now record a partial settlement payment of Rs. 2,000
        Payment.objects.create(
            sale=sale,
            customer=customer,
            amount=Decimal("2000.00"),
            payment_date=timezone.now(),
            payment_method="Cash",
            status="Completed",
        )

        analytics_after = AnalyticsService.get_business_analytics(company_id=company.id, days=30)
        assert analytics_after["revenue"] == Decimal("5000.00")
        assert analytics_after["cash_received"] == Decimal("2000.00")
        assert analytics_after["collection_rate_pct"] == 40.0
        assert analytics_after["receivables_total"] == Decimal("3000.00")

    def test_cogs_gross_profit_net_profit_and_cash_flow(self, enterprise_setup):
        """Verifies COGS, Gross Profit = Rev - COGS, Net Profit = GP - Exp, Net Cash Flow."""
        company = enterprise_setup["company"]
        customer = enterprise_setup["customer"]
        supplier = enterprise_setup["supplier"]
        p_gadget = enterprise_setup["p_gadget"]

        # 1. Sale: 2 units at Rs. 2,500 = Rs. 5,000. Purchase price is Rs. 1,500/unit -> COGS = Rs. 3,000
        sale = Sale.objects.create(
            invoice_number="INV-TEST-PROFIT",
            customer=customer,
            total=Decimal("5000.00"),
            payment_status=Sale.STATUS_PAID,
            sale_date=timezone.now(),
            company=company,
        )
        SaleItem.objects.create(
            sale=sale,
            product=p_gadget,
            quantity=2,
            unit_price=Decimal("2500.00"),
            total=Decimal("5000.00"),
        )

        # Customer paid Rs. 5,000 cash
        Payment.objects.create(
            sale=sale,
            customer=customer,
            amount=Decimal("5000.00"),
            payment_date=timezone.now(),
            payment_method="Cash",
            status="Completed",
        )

        # 2. Operating Expense: Rent Rs. 800
        Expense.objects.create(
            amount=Decimal("800.00"),
            category="Rent",
            expense_date=timezone.now(),
            company=company,
        )

        # 3. Supplier payment: Paid Rs. 1,200 for vendor bill
        Payment.objects.create(
            supplier=supplier,
            amount=Decimal("1200.00"),
            payment_date=timezone.now(),
            payment_method="Bank",
            status="Completed",
        )

        analytics = AnalyticsService.get_business_analytics(company_id=company.id, days=30)

        # Revenue = 5000
        assert analytics["revenue"] == Decimal("5000.00")
        # COGS = 2 * 1500 = 3000
        assert analytics["cogs"] == Decimal("3000.00")
        # Gross Profit = 5000 - 3000 = 2000
        assert analytics["gross_profit"] == Decimal("2000.00")
        assert analytics["gross_margin_pct"] == 40.0
        # Expenses = 800
        assert analytics["expenses"] == Decimal("800.00")
        # Net Profit = 2000 - 800 = 1200
        assert analytics["net_profit"] == Decimal("1200.00")
        assert analytics["net_margin_pct"] == 24.0

        # Cash Flow:
        # Cash In = 5000
        assert analytics["cash_received"] == Decimal("5000.00")
        # Cash Out = 1200 (supplier) + 800 (expense) = 2000
        assert analytics["total_cash_out"] == Decimal("2000.00")
        # Net Cash Flow = 5000 - 2000 = 3000
        assert analytics["net_cash_flow"] == Decimal("3000.00")

    def test_reorder_suggestions_detects_low_stock(self, enterprise_setup):
        """Product below minimum threshold must produce intelligent reorder suggestion."""
        company = enterprise_setup["company"]
        p_cable = enterprise_setup["p_cable"]  # current_stock = 4, minimum_stock = 15

        analytics = AnalyticsService.get_business_analytics(company_id=company.id, days=30)
        reorders = analytics["reorder_suggestions"]
        assert len(reorders) >= 1

        target = next((r for r in reorders if r["sku"] == "CABLE-02"), None)
        assert target is not None
        assert target["current_stock"] == 4
        assert target["minimum_stock"] == 15
        assert target["suggested_order_qty"] >= 20  # (15 * 2) - 4 = 26
        assert target["estimated_cost"] > Decimal("0.00")

    def test_analytics_csv_export_endpoint(self, enterprise_setup):
        """CSV export returns downloadable file with all sections."""
        client = Client()
        client.force_login(enterprise_setup["admin"])

        res = client.get("/reports/analytics/export/csv/?period=30d")
        assert res.status_code == 200
        assert res["Content-Type"].startswith("text/csv")
        assert b"Business Health Score" in res.content
        assert b"Total Billed Revenue" in res.content
        assert b"Cost of Goods Sold (COGS)" in res.content
        assert b"Cash Actually Received" in res.content
        assert b"Net Cash Flow" in res.content
