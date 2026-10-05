"""Tests for Part 8: Django Web Application.

Covers:
- Landing page & Dashboard KPI metrics
- Dual AD/BS Date conversion endpoint
- Notification alerts & mark read
- Companies & Sellers CRUD, active company switching, CSV & Excel exports
- Products & Categories CRUD, search, filter, stock movements, bulk import
- Customers & Suppliers CRUD, profiles, and transaction ledgers
- Sales invoices with stock deduction, print/detail view, and cancellation stock restoration
- Purchase bills with stock addition and cancellation stock reversal
- Expense management CRUD and filtering
- Financial summary reports & Daybook ledger with CSV exports
- User management RBAC
"""
import io
import pytest
from datetime import date
from decimal import Decimal
from django.test import Client

from apps.accounts.models import User, Role
from apps.companies.models import Company, Seller
from apps.inventory.models import Category, Product, StockMovement
from apps.sales.models import Customer, Sale, SaleItem
from apps.purchases.models import Supplier, Purchase, PurchaseItem
from apps.accounting.models import Expense
from apps.audit.models import Notification


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
class TestDashboardAndCoreViews:
    def test_landing_page_unauthenticated(self):
        client = Client()
        response = client.get("/")
        assert response.status_code == 200
        assert b"BizFlow" in response.content

    def test_dashboard_authenticated(self, auth_client):
        client, user, company = auth_client
        response = client.get("/dashboard/")
        assert response.status_code == 200
        assert b"Dashboard" in response.content
        assert b"Net Profit" in response.content

    def test_date_conversion_endpoint(self, auth_client):
        client, user, company = auth_client
        # Convert AD to BS
        res_ad = client.get("/api/convert-date/?direction=ad_to_bs&date=2026-04-14")
        assert res_ad.status_code == 200
        data_ad = res_ad.json()
        assert data_ad["success"] is True
        assert "bs_date" in data_ad

        # Convert BS to AD
        res_bs = client.get("/api/convert-date/?direction=bs_to_ad&date=2083-01-01")
        assert res_bs.status_code == 200
        data_bs = res_bs.json()
        assert data_bs["success"] is True
        assert "ad_date" in data_bs

    def test_notifications_and_mark_read(self, auth_client):
        client, user, company = auth_client
        notif = Notification.objects.create(
            user=user,
            title="Low Stock Warning",
            message="Item X is below threshold.",
            is_read=False
        )
        res = client.get("/dashboard/notifications/")
        assert res.status_code == 200
        assert b"Low Stock Warning" in res.content

        # Mark as read via POST
        mark_res = client.post(f"/dashboard/notifications/{notif.id}/read/")
        assert mark_res.status_code == 200
        notif.refresh_from_db()
        assert notif.is_read is True


@pytest.mark.django_db
class TestCompaniesAndSellers:
    def test_company_crud_and_exports(self, auth_client):
        client, user, company = auth_client

        # List
        res = client.get("/companies/")
        assert res.status_code == 200
        assert b"Acme Corp" in res.content

        # Create
        create_res = client.post("/companies/new/", {
            "company_name": "Beta Industries",
            "vat_pan_number": "987654321",
            "company_phone": "9811111111",
            "address": "Pokhara, Nepal",
            "logo_url": ""
        })
        assert create_res.status_code == 302
        beta = Company.objects.get(company_name="Beta Industries")

        # Switch Active Company
        switch_res = client.get(f"/companies/{beta.id}/set-active/")
        assert switch_res.status_code == 302
        user.refresh_from_db()
        assert user.active_company_id == beta.id

        # CSV Export
        csv_res = client.get("/companies/export/csv/")
        assert csv_res.status_code == 200
        assert "text/csv" in csv_res["Content-Type"]
        assert b"Beta Industries" in csv_res.content

        # Excel Export
        excel_res = client.get("/companies/export/excel/")
        assert excel_res.status_code == 200
        assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in excel_res["Content-Type"]

    def test_sellers_crud_and_exports(self, auth_client):
        client, user, company = auth_client
        # Create seller
        res = client.post("/sellers/new/", {
            "company": company.id,
            "seller_name": "Downtown Branch",
            "seller_phone": "9844444444"
        })
        assert res.status_code == 302
        seller = Seller.objects.get(seller_name="Downtown Branch")

        # List
        list_res = client.get("/sellers/")
        assert list_res.status_code == 200
        assert b"Downtown Branch" in list_res.content

        # Export CSV
        csv_res = client.get("/sellers/export/csv/")
        assert csv_res.status_code == 200
        assert b"Downtown Branch" in csv_res.content


@pytest.mark.django_db
class TestInventoryManagement:
    def test_category_and_product_crud(self, auth_client):
        client, user, company = auth_client

        # Create Category
        cat_res = client.post("/products/categories/new/", {
            "name": "Electronics",
            "description": "Gadgets & Hardware",
            "is_active": True
        })
        assert cat_res.status_code == 302
        category = Category.objects.get(name="Electronics")

        # Create Product
        prod_res = client.post("/products/new/", {
            "company": company.id,
            "category": category.id,
            "name": "Laptop Stand",
            "sku": "LS-001",
            "purchase_price": "1200.00",
            "selling_price": "1800.00",
            "current_stock": "25",
            "minimum_stock": "5",
            "unit": "pcs",
            "tax_rate": "13.00",
            "description": "Ergonomic aluminum stand"
        })
        assert prod_res.status_code == 302
        product = Product.objects.get(sku="LS-001")
        assert product.selling_price == Decimal("1800.00")

        # Search and Filter
        search_res = client.get(f"/products/?search=Laptop&category_id={category.id}")
        assert search_res.status_code == 200
        assert b"Laptop Stand" in search_res.content

        # CSV & Excel Export
        csv_res = client.get("/products/export/csv/")
        assert csv_res.status_code == 200
        assert b"Laptop Stand" in csv_res.content

        excel_res = client.get("/products/export/excel/")
        assert excel_res.status_code == 200

    def test_stock_adjustments_and_ledger(self, auth_client):
        client, user, company = auth_client
        category = Category.objects.create(name="Office Supplies")
        product = Product.objects.create(
            company=company,
            category=category,
            name="Keyboard",
            sku="KB-001",
            purchase_price=Decimal("800.00"),
            selling_price=Decimal("1200.00"),
            current_stock=10,
            is_active=True
        )

        # Manual Adjustment (ADD)
        adjust_res = client.post("/inventory/adjust/", {
            "product": product.id,
            "adjustment_type": "IN",
            "quantity": 5,
            "reason": "Stock Count Discovery"
        })
        assert adjust_res.status_code == 302
        product.refresh_from_db()
        assert product.current_stock == 15

        # Check Movement Ledger
        mov_res = client.get("/inventory/")
        assert mov_res.status_code == 200
        assert b"Keyboard" in mov_res.content

    def test_sample_template_and_bulk_import(self, auth_client):
        client, user, company = auth_client

        # Sample Template
        tpl_res = client.get("/products/sample-template/")
        assert tpl_res.status_code == 200
        assert b"SKU" in tpl_res.content

        # Bulk Import CSV
        csv_data = "sku,name,purchase_price,selling_price,current_stock,unit\nUSB-001,USB Cable,150,250,50,pcs\n"
        csv_file = io.BytesIO(csv_data.encode("utf-8"))
        csv_file.name = "products.csv"

        import_res = client.post("/products/import/", {"file": csv_file})
        assert import_res.status_code == 302
        assert Product.objects.filter(sku="USB-001").exists()


@pytest.mark.django_db
class TestSalesAndCustomers:
    def test_customer_crud_and_ledger(self, auth_client):
        client, user, company = auth_client

        # Create Customer
        res = client.post("/customers/new/", {
            "name": "Bikash Shrestha",
            "phone": "9812345678",
            "email": "bikash@example.com",
            "address": "Kathmandu, Nepal",
            "opening_balance": "0.00",
            "credit_limit": "50000.00",
            "company": company.id,
            "is_active": True
        })
        assert res.status_code == 302
        customer = Customer.objects.get(name="Bikash Shrestha")

        # Detail Ledger View
        detail_res = client.get(f"/customers/{customer.id}/")
        assert detail_res.status_code == 200
        assert b"Bikash Shrestha" in detail_res.content

    def test_sale_creation_stock_deduction_and_cancellation(self, auth_client):
        client, user, company = auth_client
        category = Category.objects.create(name="Computers")
        product = Product.objects.create(
            company=company,
            category=category,
            name="Mouse",
            sku="MS-101",
            purchase_price=Decimal("300.00"),
            selling_price=Decimal("500.00"),
            current_stock=20,
            is_active=True
        )
        customer = Customer.objects.create(
            company=company,
            name="Anoop Sharma",
            phone="9851000000"
        )

        # Create Sale via Form
        sale_res = client.post("/sales/new/", {
            "customer": customer.id,
            "product": product.id,
            "quantity": 2,
            "unit_price": "500.00",
            "discount": "0.00",
            "payment_status": "Paid",
            "payment_method": "Cash",
            "bill_number": "BILL-1001",
            "notes": "Direct Sale"
        })
        assert sale_res.status_code == 302
        sale = Sale.objects.filter(customer=customer).first()
        assert sale is not None

        # Verify stock was deducted automatically by StockService
        product.refresh_from_db()
        assert product.current_stock == 18

        # View Printable Invoice Detail
        detail_res = client.get(f"/sales/{sale.id}/")
        assert detail_res.status_code == 200
        assert b"TAX INVOICE" in detail_res.content
        assert b"window.print()" in detail_res.content

        # Cancel Sale (restores stock via StockService)
        cancel_res = client.post(f"/sales/{sale.id}/delete/")
        assert cancel_res.status_code == 302
        product.refresh_from_db()
        assert product.current_stock == 20


@pytest.mark.django_db
class TestPurchasesAndSuppliers:
    def test_supplier_crud(self, auth_client):
        client, user, company = auth_client
        res = client.post("/suppliers/new/", {
            "name": "Global Traders Pvt Ltd",
            "phone": "9841223344",
            "email": "global@traders.com",
            "address": "Birgunj, Nepal",
            "opening_balance": "0.00",
            "company": company.id,
            "is_active": True
        })
        assert res.status_code == 302
        supplier = Supplier.objects.get(name="Global Traders Pvt Ltd")

        detail_res = client.get(f"/suppliers/{supplier.id}/")
        assert detail_res.status_code == 200
        assert b"Global Traders" in detail_res.content

    def test_purchase_creation_and_cancellation(self, auth_client):
        client, user, company = auth_client
        supplier = Supplier.objects.create(company=company, name="ABC Wholesalers")
        category = Category.objects.create(name="Hardware")
        product = Product.objects.create(
            company=company,
            category=category,
            name="Power Supply",
            sku="PS-500",
            purchase_price=Decimal("2000.00"),
            selling_price=Decimal("2800.00"),
            current_stock=5,
            is_active=True
        )

        # Create Purchase
        res = client.post("/purchases/new/", {
            "supplier": supplier.id,
            "product": product.id,
            "quantity": 5,
            "unit_price": "2000.00",
            "discount": "0.00",
            "payment_status": "Paid",
            "payment_method": "Cash",
            "bill_number": "PO-1001",
            "notes": "Direct vendor purchase"
        })
        assert res.status_code == 302
        purchase = Purchase.objects.filter(supplier=supplier).first()
        assert purchase is not None

        # Verify stock replenishment by StockService
        product.refresh_from_db()
        assert product.current_stock == 10

        # Detail View
        detail_res = client.get(f"/purchases/{purchase.id}/")
        assert detail_res.status_code == 200

        # Cancel purchase (deducts stock via StockService)
        cancel_res = client.post(f"/purchases/{purchase.id}/delete/")
        assert cancel_res.status_code == 302
        product.refresh_from_db()
        assert product.current_stock == 5


@pytest.mark.django_db
class TestAccountingAndReports:
    def test_expense_crud(self, auth_client):
        client, user, company = auth_client
        res = client.post("/expenses/new/", {
            "category": "Utilities",
            "amount": "3500.00",
            "expense_date": "2026-04-14",
            "payment_method": "Cash",
            "reference": "VOUCHER-01",
            "description": "Office High-Speed Internet"
        })
        assert res.status_code == 302
        expense = Expense.objects.get(description="Office High-Speed Internet")
        assert expense.amount == Decimal("3500.00")

        list_res = client.get("/expenses/?category=Utilities")
        assert list_res.status_code == 200
        assert b"Office High-Speed Internet" in list_res.content

    def test_reports_and_daybook(self, auth_client):
        client, user, company = auth_client

        # Reports index
        res = client.get("/reports/")
        assert res.status_code == 200
        assert b"Financial Summary" in res.content

        # Daybook view
        daybook_res = client.get("/reports/daybook/?date=2026-04-14")
        assert daybook_res.status_code == 200
        assert b"Day Inflow" in daybook_res.content

        # CSV exports
        summary_csv = client.get("/reports/export/summary-csv/")
        assert summary_csv.status_code == 200
        assert b"Financial Summary Report" in summary_csv.content

        daybook_csv = client.get("/reports/export/daybook-csv/?date=2026-04-14")
        assert daybook_csv.status_code == 200
        assert b"Type,Reference" in daybook_csv.content


@pytest.mark.django_db
class TestUserManagementRBAC:
    def test_admin_can_manage_users(self, auth_client):
        client, user, company = auth_client
        res = client.get("/users/")
        assert res.status_code == 200
        assert b"User Accounts" in res.content

        # Create new staff user
        staff_role, _ = Role.objects.get_or_create(
            name="staff",
            defaults={"description": "Staff Member"}
        )
        create_res = client.post("/users/new/", {
            "email": "staff@bizflow.com",
            "name": "Staff Member 1",
            "phone": "9812345678",
            "password": "Password123!",
            "role": staff_role.id,
            "active_company": company.id,
            "is_active": True,
        })
        assert create_res.status_code == 302
        assert User.objects.filter(email="staff@bizflow.com").exists()

    def test_staff_cannot_access_user_management(self, auth_client):
        client, user, company = auth_client
        staff_role, _ = Role.objects.get_or_create(name="staff", defaults={"description": "Staff Member"})
        staff_user = User.objects.create_user(
            email="staffonly@test.com",
            password="Password123!",
            name="Staff Only",
            role=staff_role,
            active_company=company
        )
        client.force_login(staff_user)

        res = client.get("/users/")
        # Should be forbidden / redirect
        assert res.status_code in [302, 403]
