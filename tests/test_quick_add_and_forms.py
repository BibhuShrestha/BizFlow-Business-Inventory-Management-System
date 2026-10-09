"""Tests for Quick-Add Modals, Inline Entity Creation, and Form State Persistence.

Verifies:
- AJAX quick-create for Company, Supplier, Customer, Product, Category, Seller
- `return_to` / `next` query parameter redirection preserving entity IDs
- Sale and Purchase invoice creation with optional Company selection
- Rendering of redesigned Sale, Purchase, and Product forms with quick-add modals
"""
import json
import pytest
from decimal import Decimal
from django.test import Client

from apps.accounts.models import User, Role
from apps.companies.models import Company, Seller
from apps.inventory.models import Category, Product
from apps.sales.models import Customer, Sale
from apps.purchases.models import Supplier, Purchase


@pytest.fixture
def auth_client(db):
    """Returns a test client authenticated as an Admin with an active company."""
    admin_role, _ = Role.objects.get_or_create(
        name="admin",
        defaults={"description": "Administrator"}
    )
    company = Company.objects.create(
        company_name="Acme Corp",
        vat_pan_number="123456789",
        company_phone="9800000000",
        address="Kathmandu, Nepal"
    )
    user = User.objects.create_user(
        email="admin@test.com",
        password="ValidPassword123!",
        name="Admin Test",
        role=admin_role,
        active_company=company
    )
    client = Client()
    client.force_login(user)
    return client, user, company


@pytest.mark.django_db
class TestQuickAddAjaxEndpoints:
    def test_company_quick_add_ajax(self, auth_client):
        client, user, company = auth_client
        res = client.post(
            "/companies/new/",
            {
                "company_name": "New Quick Company Pvt Ltd",
                "vat_pan_number": "999888777",
                "company_phone": "9811223344",
                "address": "Lalitpur",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["name"] == "New Quick Company Pvt Ltd"
        assert Company.objects.filter(company_name="New Quick Company Pvt Ltd").exists()

    def test_company_quick_add_redirect_with_return_to(self, auth_client):
        client, user, company = auth_client
        res = client.post(
            "/companies/new/?return_to=/purchases/new/",
            {
                "company_name": "Redirect Co",
                "vat_pan_number": "111222333",
            }
        )
        assert res.status_code == 302
        new_co = Company.objects.get(company_name="Redirect Co")
        assert f"/purchases/new/?company_id={new_co.id}" in res["Location"]

    def test_supplier_quick_add_ajax(self, auth_client):
        client, user, company = auth_client
        res = client.post(
            "/suppliers/new/",
            {
                "name": "Quick Vendor Alpha",
                "phone": "9851122334",
                "email": "vendor@alpha.com",
                "address": "Pokhara",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["name"] == "Quick Vendor Alpha"
        assert Supplier.objects.filter(name="Quick Vendor Alpha").exists()

    def test_supplier_quick_add_redirect_with_return_to(self, auth_client):
        client, user, company = auth_client
        res = client.post(
            "/suppliers/new/?return_to=/purchases/new/",
            {
                "name": "Supplier Redirect Vendor",
                "phone": "9800000000",
            }
        )
        assert res.status_code == 302
        new_sup = Supplier.objects.get(name="Supplier Redirect Vendor")
        assert f"/purchases/new/?supplier_id={new_sup.id}" in res["Location"]

    def test_customer_quick_add_ajax(self, auth_client):
        client, user, company = auth_client
        res = client.post(
            "/customers/new/",
            {
                "name": "Quick Customer Bravo",
                "phone": "9841998877",
                "email": "bravo@customer.com",
                "address": "Biratnagar",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["name"] == "Quick Customer Bravo"
        assert Customer.objects.filter(name="Quick Customer Bravo").exists()

    def test_product_quick_add_ajax(self, auth_client):
        client, user, company = auth_client
        res = client.post(
            "/products/new/",
            {
                "name": "Quick Add Wireless Mouse",
                "sku": "WM-999",
                "purchase_price": "450.00",
                "selling_price": "750.00",
                "current_stock": "15",
                "unit": "pcs",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert "Quick Add Wireless Mouse" in data["name"]
        assert Product.objects.filter(sku="WM-999").exists()

    def test_category_quick_add_ajax(self, auth_client):
        client, user, company = auth_client
        res = client.post(
            "/products/categories/new/",
            {
                "name": "Peripherals & Accessories",
                "description": "Computer peripherals",
                "is_active": True,
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["name"] == "Peripherals & Accessories"
        assert Category.objects.filter(name="Peripherals & Accessories").exists()

    def test_seller_quick_add_ajax(self, auth_client):
        client, user, company = auth_client
        res = client.post(
            "/sellers/new/",
            {
                "seller_name": "Quick Seller John",
                "seller_phone": "9841112233",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert "Quick Seller John" in data["name"]
        assert Seller.objects.filter(seller_name="Quick Seller John").exists()


@pytest.mark.django_db
class TestRedesignedFormsRendering:
    def test_sale_form_get_renders_modals_and_fields(self, auth_client):
        client, user, company = auth_client
        res = client.get("/sales/new/")
        assert res.status_code == 200
        # Check required fields exist in HTML
        assert b'name="customer"' in res.content
        assert b'name="product"' in res.content
        assert b'name="quantity"' in res.content
        assert b'name="unit_price"' in res.content
        assert b'name="discount"' in res.content
        # Check inline modals are embedded
        assert b'id="modal-add-customer"' in res.content
        assert b'id="modal-add-company"' in res.content
        assert b'id="modal-add-product"' in res.content
        assert b'quick_add.js' in res.content

    def test_purchase_form_get_renders_modals_and_fields(self, auth_client):
        client, user, company = auth_client
        res = client.get("/purchases/new/")
        assert res.status_code == 200
        # Check required fields exist in HTML
        assert b'name="supplier"' in res.content
        assert b'name="product"' in res.content
        assert b'name="quantity"' in res.content
        assert b'name="unit_price"' in res.content
        assert b'name="discount"' in res.content
        # Check inline modals are embedded
        assert b'id="modal-add-supplier"' in res.content
        assert b'id="modal-add-company"' in res.content
        assert b'id="modal-add-product"' in res.content
        assert b'quick_add.js' in res.content

    def test_product_form_get_renders_modals_and_fields(self, auth_client):
        client, user, company = auth_client
        res = client.get("/products/new/")
        assert res.status_code == 200
        assert b'name="name"' in res.content
        assert b'name="sku"' in res.content
        assert b'name="selling_price"' in res.content
        assert b'name="purchase_price"' in res.content
        assert b'id="modal-add-company"' in res.content
        assert b'id="modal-add-category"' in res.content
        assert b'id="modal-add-seller"' in res.content

    def test_sale_creation_with_specific_company(self, auth_client):
        client, user, company = auth_client
        cat = Category.objects.create(name="Monitors")
        company2 = Company.objects.create(company_name="Secondary Company")
        customer = Customer.objects.create(name="Customer 1", phone="9800000001")
        product = Product.objects.create(
            category=cat,
            name="Test Monitor",
            sku="MON-01",
            current_stock=10,
            selling_price=Decimal("15000.00"),
            purchase_price=Decimal("10000.00"),
            company=company2
        )

        res = client.post("/sales/new/", {
            "company": company2.id,
            "customer": customer.id,
            "product": product.id,
            "quantity": 1,
            "unit_price": "15000.00",
            "discount": "0.00",
            "payment_status": "Paid",
            "payment_method": "Cash",
            "bill_number": "BILL-2001",
            "notes": "Company specific sale"
        })
        assert res.status_code == 302
        sale = Sale.objects.get(bill_number="BILL-2001")
        assert sale.company == company2

    def test_purchase_creation_with_specific_company(self, auth_client):
        client, user, company = auth_client
        cat = Category.objects.create(name="Components")
        company2 = Company.objects.create(company_name="Secondary Supplier Company")
        supplier = Supplier.objects.create(name="Vendor 1", phone="9800000002")
        product = Product.objects.create(
            category=cat,
            name="Test RAM",
            sku="RAM-01",
            current_stock=5,
            selling_price=Decimal("4000.00"),
            purchase_price=Decimal("2500.00"),
            company=company2
        )

        res = client.post("/purchases/new/", {
            "company": company2.id,
            "supplier": supplier.id,
            "product": product.id,
            "quantity": 4,
            "unit_price": "2500.00",
            "discount": "0.00",
            "payment_status": "Paid",
            "payment_method": "Cash",
            "bill_number": "PO-2001",
            "notes": "Company specific purchase"
        })
        assert res.status_code == 302
        purchase = Purchase.objects.get(bill_number="PO-2001")
        assert purchase.company == company2

    def test_sale_creation_with_custom_date_and_due_date(self, auth_client):
        client, user, company = auth_client
        cat = Category.objects.create(name="Monitors")
        customer = Customer.objects.create(name="Date Test Customer", phone="9800000099")
        product = Product.objects.create(
            category=cat,
            name="27 Inch 4K Display",
            sku="DISP-4K",
            current_stock=10,
            selling_price=Decimal("45000.00"),
            purchase_price=Decimal("38000.00"),
            company=company
        )

        res = client.post("/sales/new/", {
            "company": company.id,
            "customer": customer.id,
            "product": product.id,
            "quantity": 1,
            "unit_price": "45000.00",
            "discount": "500.00",
            "sale_date": "2026-09-15",
            "due_date": "2026-10-15",
            "payment_status": "Due",
            "payment_method": "Credit",
            "bill_number": "INV-DATED-01",
            "notes": "Custom transaction and due date"
        })
        assert res.status_code == 302
        sale = Sale.objects.get(bill_number="INV-DATED-01")
        assert sale.sale_date.date().isoformat() == "2026-09-15"
        assert sale.due_date.isoformat() == "2026-10-15"
        assert sale.payment_status == "Due"

    def test_purchase_creation_with_custom_date_and_due_date(self, auth_client):
        client, user, company = auth_client
        cat = Category.objects.create(name="Monitors")
        supplier = Supplier.objects.create(name="Date Test Vendor", phone="9800000088")
        product = Product.objects.create(
            category=cat,
            name="Keychron Mechanical Keyboard",
            sku="KEY-M1",
            current_stock=2,
            selling_price=Decimal("12000.00"),
            purchase_price=Decimal("8500.00"),
            company=company
        )

        res = client.post("/purchases/new/", {
            "company": company.id,
            "supplier": supplier.id,
            "product": product.id,
            "quantity": 5,
            "unit_price": "8500.00",
            "discount": "0.00",
            "purchase_date": "2026-08-20",
            "due_date": "2026-09-20",
            "payment_status": "Due",
            "payment_method": "Credit",
            "bill_number": "PO-DATED-01",
            "notes": "Custom bill and due date"
        })
        assert res.status_code == 302
        purchase = Purchase.objects.get(bill_number="PO-DATED-01")
        assert purchase.purchase_date.date().isoformat() == "2026-08-20"
        assert purchase.due_date.isoformat() == "2026-09-20"
        assert purchase.payment_status == "Due"

    def test_sales_and_purchases_list_date_range_filtering(self, auth_client):
        client, user, company = auth_client
        # Filter sales by date
        res_sale = client.get("/sales/?date_from=2026-09-01&date_to=2026-09-30")
        assert res_sale.status_code == 200
        assert "From:" in res_sale.content.decode()

        # Filter purchases by date
        res_purch = client.get("/purchases/?date_from=2026-08-01&date_to=2026-08-31")
        assert res_purch.status_code == 200
        assert "From:" in res_purch.content.decode()

    def test_expense_and_credit_list_date_range_filtering(self, auth_client):
        client, user, company = auth_client
        # Filter expenses by date
        res_exp = client.get("/expenses/?date_from=2026-09-01&date_to=2026-09-30")
        assert res_exp.status_code == 200
        assert "From:" in res_exp.content.decode()

        # Filter credit given (receivables) by date
        res_given = client.get("/credit/given/?date_from=2026-09-01&date_to=2026-09-30")
        assert res_given.status_code == 200
        assert "From:" in res_given.content.decode()

        # Filter credit taken (payables) by date
        res_taken = client.get("/credit/taken/?date_from=2026-08-01&date_to=2026-08-31")
        assert res_taken.status_code == 200
        assert "From:" in res_taken.content.decode()


