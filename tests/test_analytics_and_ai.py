"""
Test Suite for Part 22: Business Analytics & AI Decision Support Suite.

Verifies:
- AnalyticsService calculation of gross/net profit, margins, inventory velocity, health scores.
- Multi-tenancy isolation across distinct companies.
- LocalDeterministicAdvisor structured decision rules (zero latency, zero tokens).
- AIAnalyticsService bounded caching, rate limits, and fallback behavior.
- Django Web UI analytics dashboard and on-demand refresh views.
- FastAPI REST API /api/v1/analytics/summary and refresh endpoints.
"""
from datetime import timedelta
from decimal import Decimal
import pytest
from django.test import Client
from django.utils import timezone
from fastapi.testclient import TestClient

from apps.accounts.models import User, Role
from apps.companies.models import Company
from apps.inventory.models import Category, Product
from apps.sales.models import Sale, SaleItem, Customer
from apps.purchases.models import Purchase, PurchaseItem, Supplier
from apps.accounting.models import Expense
from apps.credit.models import Cheque
from domain.services.analytics_service import AnalyticsService
from integrations.ai_analytics import LocalDeterministicAdvisor, AIAnalyticsService
from api.main import app
from core.security import create_access_token


@pytest.fixture
def analytics_setup(db):
    """Setup multi-tenant companies, users, catalog, and transactions."""
    manager_role = Role.objects.get_or_create(name="manager", defaults={"description": "Manager"})[0]
    staff_role = Role.objects.get_or_create(name="staff", defaults={"description": "Staff"})[0]

    company1 = Company.objects.create(
        company_name="Alpha Enterprises",
        company_phone="9800000001",
        vat_pan_number="111222333",
    )
    company2 = Company.objects.create(
        company_name="Beta Logistics",
        company_phone="9800000002",
        vat_pan_number="444555666",
    )

    manager = User.objects.create_user(
        email="manager@alpha.com",
        name="Alpha Manager",
        password="SecurePassword123!",
        role=manager_role,
        active_company=company1,
    )

    staff = User.objects.create_user(
        email="staff@alpha.com",
        name="Alpha Staff",
        password="SecurePassword123!",
        role=staff_role,
        active_company=company1,
    )

    cat = Category.objects.create(name="Beverages")

    # Products for Company 1
    p_fast = Product.objects.create(
        name="Fast Juice",
        sku="JUICE-001",
        current_stock=50,
        purchase_price=Decimal("40.00"),
        selling_price=Decimal("60.00"),
        category=cat,
        company=company1,
    )

    p_slow = Product.objects.create(
        name="Slow Syrup",
        sku="SYRUP-002",
        current_stock=20,
        purchase_price=Decimal("100.00"),
        selling_price=Decimal("150.00"),
        category=cat,
        company=company1,
    )

    p_out = Product.objects.create(
        name="Out Item",
        sku="OUT-003",
        current_stock=0,
        purchase_price=Decimal("20.00"),
        selling_price=Decimal("30.00"),
        category=cat,
        company=company1,
    )

    # Customer and Supplier
    cust = Customer.objects.create(name="Retail Customer", phone="9841000000", company=company1)
    supp = Supplier.objects.create(name="Prime Vendor", phone="9842000000", company=company1)

    # Sale transaction (Revenue = 600.00)
    sale = Sale.objects.create(
        invoice_number="INV-2026-001",
        customer=cust,
        total=Decimal("600.00"),
        payment_method="CASH",
        payment_status=Sale.STATUS_PAID,
        sale_date=timezone.now(),
        company=company1,
    )
    SaleItem.objects.create(
        sale=sale,
        product=p_fast,
        quantity=10,
        unit_price=Decimal("60.00"),
        total=Decimal("600.00"),
    )

    # Purchase transaction (Cost = 400.00)
    purch = Purchase.objects.create(
        purchase_number="BILL-2026-001",
        supplier=supp,
        total=Decimal("400.00"),
        payment_method="CASH",
        payment_status=Purchase.STATUS_PAID,
        purchase_date=timezone.now(),
        company=company1,
    )
    PurchaseItem.objects.create(
        purchase=purch,
        product=p_fast,
        quantity=10,
        unit_price=Decimal("40.00"),
        total=Decimal("400.00"),
    )

    # Expense (Overhead = 50.00)
    Expense.objects.create(
        category="Utilities",
        description="Store Utilities",
        amount=Decimal("50.00"),
        expense_date=timezone.now(),
        company=company1,
        user=manager,
    )

    # Company 2 isolated data
    cat2 = Category.objects.create(name="Hardware")
    p_comp2 = Product.objects.create(
        name="Steel Wire",
        sku="WIRE-999",
        current_stock=100,
        purchase_price=Decimal("10.00"),
        selling_price=Decimal("15.00"),
        category=cat2,
        company=company2,
    )
    cust2 = Customer.objects.create(name="Beta Client", phone="9843000000", company=company2)
    sale2 = Sale.objects.create(
        invoice_number="INV-BETA-001",
        customer=cust2,
        total=Decimal("5000.00"),
        payment_method="CASH",
        payment_status=Sale.STATUS_PAID,
        sale_date=timezone.now(),
        company=company2,
    )
    SaleItem.objects.create(
        sale=sale2,
        product=p_comp2,
        quantity=50,
        unit_price=Decimal("100.00"),
        total=Decimal("5000.00"),
    )

    return {
        "company1": company1,
        "company2": company2,
        "manager": manager,
        "staff": staff,
        "p_fast": p_fast,
        "p_slow": p_slow,
        "p_out": p_out,
    }


class TestAnalyticsService:
    """Tests for AnalyticsService business intelligence and calculations."""

    def test_get_business_analytics_metrics(self, analytics_setup):
        company1 = analytics_setup["company1"]
        data = AnalyticsService.get_business_analytics(company_id=company1.id, days=30)

        # Revenue = 600, Purchases = 400, Expenses = 50
        assert data["revenue"] == Decimal("600.00")
        assert data["purchases"] == Decimal("400.00")
        assert data["expenses"] == Decimal("50.00")

        # Gross profit = 600 - 400 = 200
        assert data["gross_profit"] == Decimal("200.00")
        # Net profit = 200 - 50 = 150
        assert data["net_profit"] == Decimal("150.00")
        assert data["net_margin_pct"] == 25.0

        # Health score
        assert 10 <= data["health_score"] <= 100
        assert data["health_grade"] in ["Excellent", "Healthy", "Attention Needed", "Critical Risk"]

        # Fast moving product check
        fast_items = data["fast_moving_products"]
        assert len(fast_items) == 1
        assert fast_items[0]["sku"] == "JUICE-001"
        assert fast_items[0]["sold_units"] == 10

        # Slow moving product check (p_slow has 20 stock and 0 sales)
        slow_items = data["slow_moving_products"]
        slow_skus = [p["sku"] for p in slow_items]
        assert "SYRUP-002" in slow_skus

        # Top expense categories
        top_exp = data["top_expense_categories"]
        assert len(top_exp) == 1
        assert top_exp[0]["category"] == "Utilities"
        assert top_exp[0]["amount"] == Decimal("50.00")

    def test_multi_tenancy_isolation(self, analytics_setup):
        company1 = analytics_setup["company1"]
        company2 = analytics_setup["company2"]

        data1 = AnalyticsService.get_business_analytics(company_id=company1.id, days=30)
        data2 = AnalyticsService.get_business_analytics(company_id=company2.id, days=30)

        # Company 1 revenue must be 600, not including Company 2's 5000
        assert data1["revenue"] == Decimal("600.00")
        assert data2["revenue"] == Decimal("5000.00")

    def test_deterministic_advisor_rules(self):
        # Test out of stock trigger
        mock_data = {
            "revenue": 10000.0,
            "net_profit": 2500.0,
            "net_margin_pct": 25.0,
            "receivables_overdue": 500.0,
            "receivables_total": 2000.0,
            "payables_total": 1000.0,
            "low_stock_count": 0,
            "out_of_stock_count": 2,
            "health_score": 85,
        }
        insights = LocalDeterministicAdvisor.generate_insights(mock_data)
        assert insights["source"] == "local_rules"
        assert "out-of-stock" in str(insights["action_plan"]).lower() or "restock" in str(insights["action_plan"]).lower()

        # Test zero revenue phase
        zero_data = {
            "revenue": 0.0,
            "net_profit": 0.0,
            "net_margin_pct": 0.0,
            "receivables_overdue": 0.0,
            "receivables_total": 0.0,
            "payables_total": 0.0,
            "low_stock_count": 0,
            "out_of_stock_count": 0,
            "health_score": 70,
        }
        zero_insights = LocalDeterministicAdvisor.generate_insights(zero_data)
        assert "setup or low-volume" in zero_insights["executive_summary"].lower()


class TestAIAnalyticsService:
    """Tests for hybrid AI service caching and rate limiting."""

    def test_caching_and_fallback(self, analytics_setup):
        company1 = analytics_setup["company1"]
        summary = AnalyticsService.get_business_analytics(company_id=company1.id, days=30)

        # First call without live key falls back to local rules
        first_call = AIAnalyticsService.get_insights(summary, company_id=company1.id, force_refresh=True)
        assert "executive_summary" in first_call

        # Second call returns from cache
        second_call = AIAnalyticsService.get_insights(summary, company_id=company1.id, force_refresh=False)
        assert second_call.get("source") == "cache"

    def test_user_rate_limit(self, analytics_setup):
        company1 = analytics_setup["company1"]
        user = analytics_setup["manager"]
        summary = AnalyticsService.get_business_analytics(company_id=company1.id, days=30)

        # Max out rate limit
        for _ in range(AIAnalyticsService.RATE_LIMIT_PER_HOUR + 1):
            res = AIAnalyticsService.get_insights(
                summary,
                company_id=company1.id,
                force_refresh=True,
                user_id=user.id,
            )
        assert res.get("rate_limited") is True


class TestReportsWebAnalyticsView:
    """Tests for Web UI /reports/analytics/."""

    def test_analytics_view_authenticated(self, analytics_setup):
        client = Client()
        manager = analytics_setup["manager"]
        client.force_login(manager)

        response = client.get("/reports/analytics/?days=30")
        assert response.status_code == 200
        assert b"Executive Analytics &amp; AI Decision Support" in response.content or b"AI Decision Support" in response.content
        assert b"JUICE-001" in response.content

    def test_analytics_ai_refresh_post(self, analytics_setup):
        client = Client()
        manager = analytics_setup["manager"]
        client.force_login(manager)

        response = client.post("/reports/analytics/refresh-ai/", {"days": "30"})
        assert response.status_code == 302
        assert "/reports/analytics/?days=30" in response.url

    def test_analytics_view_unauthenticated(self):
        client = Client()
        response = client.get("/reports/analytics/")
        assert response.status_code == 302
        assert "/login" in response.url


@pytest.mark.django_db(transaction=True)
class TestFastAPIAnalyticsEndpoints:
    """Tests for FastAPI /api/v1/analytics/."""

    def test_api_analytics_summary(self, analytics_setup):
        manager = analytics_setup["manager"]
        token = create_access_token(data={"sub": str(manager.id), "email": manager.email})

        client = TestClient(app)
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.get("/api/v1/analytics/summary?days=30", headers=headers)
        assert resp.status_code == 200

        data = resp.json()
        assert float(data["revenue"]) == 600.0
        assert float(data["gross_profit"]) == 200.0
        assert float(data["net_profit"]) == 150.0
        assert data["health_score"] >= 10
        assert "ai_insights" in data

    def test_api_analytics_refresh(self, analytics_setup):
        manager = analytics_setup["manager"]
        token = create_access_token(data={"sub": str(manager.id), "email": manager.email})

        client = TestClient(app)
        headers = {"Authorization": f"Bearer {token}"}
        payload = {"days": 30, "force_refresh": True}
        resp = client.post("/api/v1/analytics/insights/refresh", json=payload, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "executive_summary" in data
        assert "action_plan" in data
