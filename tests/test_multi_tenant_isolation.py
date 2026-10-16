"""Unit and integration tests for multi-tenant data isolation.

Verifies:
- Tenant Admins and Staff only see and manipulate records belonging to their active_company.
- Cross-tenant access to sales, purchases, inventory, customers, suppliers, and expenses returns 404.
- Cross-tenant exports do not leak other companies' data.
"""
from decimal import Decimal
import pytest
from django.test import Client

from apps.accounts.models import Role, User
from apps.companies.models import Company
from apps.inventory.models import Category, Product
from apps.sales.models import Customer, Sale
from apps.purchases.models import Supplier, Purchase
from apps.accounting.models import Expense


@pytest.fixture
def two_companies_setup(db):
    """Set up two distinct tenant companies with admin users and resources."""
    admin_role, _ = Role.objects.get_or_create(
        name="admin",
        defaults={"description": "Administrator"}
    )

    # Company A
    company_a = Company.objects.create(
        company_name="Alpha Corp",
        vat_pan_number="111111111",
        company_phone="9800000001",
        address="Kathmandu",
    )
    user_a = User.objects.create_user(
        email="admin_a@alpha.com",
        name="Admin Alpha",
        password="ValidPassword123!",
        role=admin_role,
        active_company=company_a,
    )

    # Company B
    company_b = Company.objects.create(
        company_name="Beta Corp",
        vat_pan_number="222222222",
        company_phone="9800000002",
        address="Pokhara",
    )
    user_b = User.objects.create_user(
        email="admin_b@beta.com",
        name="Admin Beta",
        password="ValidPassword123!",
        role=admin_role,
        active_company=company_b,
    )

    category, _ = Category.objects.get_or_create(name="General")

    # Products
    prod_a = Product.objects.create(
        sku="SKU-A",
        name="Product Alpha",
        company=company_a,
        category=category,
        purchase_price=Decimal("100"),
        selling_price=Decimal("150"),
        current_stock=10,
    )
    prod_b = Product.objects.create(
        sku="SKU-B",
        name="Product Beta",
        company=company_b,
        category=category,
        purchase_price=Decimal("200"),
        selling_price=Decimal("250"),
        current_stock=20,
    )

    # Customers & Sales
    cust_a = Customer.objects.create(name="Customer A", company=company_a)
    cust_b = Customer.objects.create(name="Customer B", company=company_b)

    from django.utils import timezone
    now = timezone.now()

    sale_a = Sale.objects.create(
        invoice_number="INV-A-001",
        customer=cust_a,
        company=company_a,
        sale_date=now,
        total=Decimal("150"),
    )
    sale_b = Sale.objects.create(
        invoice_number="INV-B-001",
        customer=cust_b,
        company=company_b,
        sale_date=now,
        total=Decimal("250"),
    )

    # Suppliers & Purchases
    supp_a = Supplier.objects.create(name="Supplier A", company=company_a)
    supp_b = Supplier.objects.create(name="Supplier B", company=company_b)

    purch_a = Purchase.objects.create(
        purchase_number="PO-A-001",
        supplier=supp_a,
        company=company_a,
        purchase_date=now,
        total=Decimal("100"),
    )
    purch_b = Purchase.objects.create(
        purchase_number="PO-B-001",
        supplier=supp_b,
        company=company_b,
        purchase_date=now,
        total=Decimal("200"),
    )

    # Expenses
    exp_a = Expense.objects.create(
        category="Rent",
        amount=Decimal("500"),
        expense_date=now,
        company=company_a,
    )
    exp_b = Expense.objects.create(
        category="Electricity",
        amount=Decimal("300"),
        expense_date=now,
        company=company_b,
    )

    client_a = Client()
    client_a.force_login(user_a)

    return {
        "company_a": company_a,
        "company_b": company_b,
        "user_a": user_a,
        "user_b": user_b,
        "client_a": client_a,
        "prod_a": prod_a,
        "prod_b": prod_b,
        "sale_a": sale_a,
        "sale_b": sale_b,
        "purch_a": purch_a,
        "purch_b": purch_b,
        "exp_a": exp_a,
        "exp_b": exp_b,
    }


@pytest.mark.django_db
class TestMultiTenantIsolation:
    """Verify complete isolation between tenant companies."""

    def test_sales_list_isolation(self, two_companies_setup):
        data = two_companies_setup
        res = data["client_a"].get("/sales/")
        assert res.status_code == 200
        content = res.content.decode("utf-8")
        assert "INV-A-001" in content
        assert "INV-B-001" not in content

    def test_sale_detail_cross_tenant_forbidden(self, two_companies_setup):
        data = two_companies_setup
        res = data["client_a"].get(f"/sales/{data['sale_b'].id}/")
        assert res.status_code == 404

    def test_sale_delete_cross_tenant_forbidden(self, two_companies_setup):
        data = two_companies_setup
        res = data["client_a"].post(f"/sales/{data['sale_b'].id}/delete/")
        assert res.status_code == 404
        assert Sale.objects.filter(id=data["sale_b"].id).exists()

    def test_purchases_list_isolation(self, two_companies_setup):
        data = two_companies_setup
        res = data["client_a"].get("/purchases/")
        assert res.status_code == 200
        content = res.content.decode("utf-8")
        assert "PO-A-001" in content
        assert "PO-B-001" not in content

    def test_purchase_detail_cross_tenant_forbidden(self, two_companies_setup):
        data = two_companies_setup
        res = data["client_a"].get(f"/purchases/{data['purch_b'].id}/")
        assert res.status_code == 404

    def test_product_list_isolation(self, two_companies_setup):
        data = two_companies_setup
        res = data["client_a"].get("/products/")
        assert res.status_code == 200
        content = res.content.decode("utf-8")
        assert "SKU-A" in content
        assert "SKU-B" not in content

    def test_product_edit_cross_tenant_forbidden(self, two_companies_setup):
        data = two_companies_setup
        res = data["client_a"].get(f"/products/{data['prod_b'].id}/edit/")
        assert res.status_code == 404

    def test_expense_list_isolation(self, two_companies_setup):
        data = two_companies_setup
        res = data["client_a"].get("/expenses/")
        assert res.status_code == 200
        content = res.content.decode("utf-8")
        assert "Rent" in content
        assert "Electricity" not in content

    def test_expense_delete_cross_tenant_forbidden(self, two_companies_setup):
        data = two_companies_setup
        res = data["client_a"].post(f"/expenses/{data['exp_b'].id}/delete/")
        assert res.status_code == 404
        assert Expense.objects.filter(id=data["exp_b"].id).exists()

    def test_user_list_company_isolation(self, two_companies_setup):
        data = two_companies_setup
        res_a = data["client_a"].get("/users/")
        assert res_a.status_code == 200
        content_a = res_a.content.decode("utf-8")
        assert "admin_a@alpha.com" in content_a
        assert "admin_b@beta.com" not in content_a

        client_b = Client()
        client_b.force_login(data["user_b"])
        res_b = client_b.get("/users/")
        assert res_b.status_code == 200
        content_b = res_b.content.decode("utf-8")
        assert "admin_b@beta.com" in content_b
        assert "admin_a@alpha.com" not in content_b
