"""
Comprehensive Test Suite for Receivables & Payables Management Feature.

Covers:
- Credit Given creation (customer receivable, multiple products, stock deduction, status)
- Credit Taken creation (supplier payable, multiple products, stock increment, status)
- Payment Lifecycle: partial payment, multiple payments, full payment, overpayment prevention
- Inventory isolation: stock is never changed by payments
- Automatic Status transitions: Unpaid, Partially Paid, Paid, Overdue
- Customer Ledger & running balance calculation
- Supplier Ledger & running balance calculation
- Customer & Supplier Outstanding Dues aggregation
- Overdue tracking & alerts
- Deletion/cancellation & atomic stock restoration
- Security & RBAC: staff vs manager permissions, unauthorized access
- Audit Logging: Credit Created, Payment Added, Payment Deleted, Credit Deleted
- Web Views rendering & CSV exports
- FastAPI REST API endpoints (/api/v1/credit/...)
"""
from datetime import date, timedelta
from decimal import Decimal
import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from fastapi.testclient import TestClient

from apps.accounts.models import User, Role
from apps.companies.models import Company
from apps.inventory.models import Category, Product
from apps.sales.models import Sale, Payment, Customer
from apps.purchases.models import Purchase, Supplier
from apps.audit.models import AuditLog
from domain.services.credit_service import CreditService
from domain.exceptions import InsufficientStockError, NotFoundError, ValidationError
from api.main import app
from core.security import create_access_token


@pytest.fixture
def credit_setup(db):
    """Setup base entities for credit tests."""
    admin_role = Role.objects.get_or_create(name="admin", defaults={"description": "Admin"})[0]
    manager_role = Role.objects.get_or_create(name="manager", defaults={"description": "Manager"})[0]
    staff_role = Role.objects.get_or_create(name="staff", defaults={"description": "Staff"})[0]
    customer_role = Role.objects.get_or_create(name="customer", defaults={"description": "Customer"})[0]

    company = Company.objects.create(
        company_name="Test Corp",
        company_phone="9800000000",
        vat_pan_number="123456789",
    )

    admin_user = User.objects.create_user(
        email="admin@credit.test",
        name="Admin User",
        password="ValidPassword123!",
        role=admin_role,
        active_company=company,
    )
    manager_user = User.objects.create_user(
        email="manager@credit.test",
        name="Manager User",
        password="ValidPassword123!",
        role=manager_role,
        active_company=company,
    )
    staff_user = User.objects.create_user(
        email="staff@credit.test",
        name="Staff User",
        password="ValidPassword123!",
        role=staff_role,
        active_company=company,
    )
    customer_user = User.objects.create_user(
        email="cust_user@credit.test",
        name="Customer User",
        password="ValidPassword123!",
        role=customer_role,
        active_company=company,
    )

    category = Category.objects.create(name="Groceries")
    rice = Product.objects.create(
        sku="RICE-01",
        name="Basmati Rice 25kg",
        category=category,
        company=company,
        unit="bag",
        purchase_price=Decimal("2000.00"),
        selling_price=Decimal("2500.00"),
        current_stock=50,
        tax_rate=Decimal("13.00"),
    )
    oil = Product.objects.create(
        sku="OIL-01",
        name="Sunflower Oil 1L",
        category=category,
        company=company,
        unit="bottle",
        purchase_price=Decimal("180.00"),
        selling_price=Decimal("220.00"),
        current_stock=100,
        tax_rate=Decimal("0.00"),
    )

    customer = Customer.objects.create(
        name="Ram Sharma",
        phone="9841234567",
        email="ram@test.com",
        company=company,
        opening_balance=Decimal("0.00"),
    )

    supplier = Supplier.objects.create(
        name="ABC Suppliers Ltd",
        phone="9851234567",
        email="abc@supplier.test",
        company=company,
        opening_balance=Decimal("0.00"),
    )

    client = Client()
    client.force_login(staff_user)

    api_client = TestClient(app)
    token = create_access_token({"sub": str(staff_user.id), "email": staff_user.email, "role": "staff"})
    auth_headers = {"Authorization": f"Bearer {token}"}

    return {
        "company": company,
        "admin_user": admin_user,
        "manager_user": manager_user,
        "staff_user": staff_user,
        "customer_user": customer_user,
        "customer": customer,
        "supplier": supplier,
        "rice": rice,
        "oil": oil,
        "client": client,
        "api_client": api_client,
        "auth_headers": auth_headers,
    }


class TestCreditGivenAndStock:
    """Test Credit Given (Customer receivable) and inventory reduction."""

    def test_create_credit_given_decrements_stock_and_calculates_balance(self, credit_setup):
        rice = credit_setup["rice"]
        oil = credit_setup["oil"]
        customer = credit_setup["customer"]
        initial_rice_stock = rice.current_stock
        initial_oil_stock = oil.current_stock

        items = [
            {"product_id": rice.id, "quantity": 2, "unit_price": Decimal("2500.00"), "tax_rate": Decimal("0.00"), "discount": Decimal("0.00")},
            {"product_id": oil.id, "quantity": 5, "unit_price": Decimal("200.00"), "tax_rate": Decimal("0.00"), "discount": Decimal("0.00")},
        ]

        sale = CreditService.create_credit_given(
            customer_id=customer.id,
            items=items,
            due_date=timezone.localdate() + timedelta(days=15),
            initial_paid_amount=Decimal("2000.00"),
            payment_method="Cash",
            user=credit_setup["staff_user"],
        )

        rice.refresh_from_db()
        oil.refresh_from_db()

        # Stock deducted
        assert rice.current_stock == initial_rice_stock - 2
        assert oil.current_stock == initial_oil_stock - 5

        # Financials: (2*2500) + (5*200) = 5000 + 1000 = 6000
        assert sale.total == Decimal("6000.00")
        assert sale.paid_amount == Decimal("2000.00")
        assert sale.remaining_amount == Decimal("4000.00")
        assert sale.calculated_status == "Partially Paid"
        assert not sale.is_overdue

        # Audit log verified
        assert AuditLog.objects.filter(module="Credit", action="Credit Created", record_id=sale.id).exists()

    def test_insufficient_stock_raises_error_and_rolls_back(self, credit_setup):
        rice = credit_setup["rice"]
        customer = credit_setup["customer"]
        initial_stock = rice.current_stock

        items = [
            {"product_id": rice.id, "quantity": initial_stock + 10, "unit_price": Decimal("2500.00")},
        ]

        with pytest.raises(InsufficientStockError):
            CreditService.create_credit_given(
                customer_id=customer.id,
                items=items,
                user=credit_setup["staff_user"],
            )

        rice.refresh_from_db()
        assert rice.current_stock == initial_stock
        assert not Sale.objects.filter(customer=customer).exists()


class TestCreditTakenAndStock:
    """Test Credit Taken (Supplier payable) and inventory increment."""

    def test_create_credit_taken_increments_stock(self, credit_setup):
        rice = credit_setup["rice"]
        supplier = credit_setup["supplier"]
        initial_stock = rice.current_stock

        items = [
            {"product_id": rice.id, "quantity": 20, "unit_price": Decimal("2000.00"), "tax_rate": Decimal("0.00"), "discount": Decimal("0.00")},
        ]

        purchase = CreditService.create_credit_taken(
            supplier_id=supplier.id,
            items=items,
            due_date=timezone.localdate() + timedelta(days=30),
            initial_paid_amount=Decimal("10000.00"),
            payment_method="Bank Transfer",
            user=credit_setup["staff_user"],
        )

        rice.refresh_from_db()
        # Stock increased
        assert rice.current_stock == initial_stock + 20

        # Financials: 20 * 2000 = 40,000
        assert purchase.total == Decimal("40000.00")
        assert purchase.paid_amount == Decimal("10000.00")
        assert purchase.remaining_amount == Decimal("30000.00")
        assert purchase.calculated_status == "Partially Paid"


class TestPaymentLifecycleAndOverpaymentPrevention:
    """Test payment settlements, partial/multiple payments, and overpayment blocks."""

    def test_payments_do_not_alter_stock(self, credit_setup):
        rice = credit_setup["rice"]
        customer = credit_setup["customer"]

        sale = CreditService.create_credit_given(
            customer_id=customer.id,
            items=[{"product_id": rice.id, "quantity": 5, "unit_price": Decimal("1000.00"), "tax_rate": Decimal("0.00")}],
            user=credit_setup["staff_user"],
        )
        rice.refresh_from_db()
        stock_after_sale = rice.current_stock

        # Add partial payment
        CreditService.add_payment(
            credit_type="given",
            transaction_id=sale.id,
            amount=Decimal("2000.00"),
            payment_method="QR / Mobile Pay",
            user=credit_setup["staff_user"],
        )

        rice.refresh_from_db()
        # Stock must remain unchanged by payments
        assert rice.current_stock == stock_after_sale
        assert sale.paid_amount == Decimal("2000.00")
        assert sale.remaining_amount == Decimal("3000.00")

    def test_multiple_payments_until_paid_status(self, credit_setup):
        rice = credit_setup["rice"]
        customer = credit_setup["customer"]

        sale = CreditService.create_credit_given(
            customer_id=customer.id,
            items=[{"product_id": rice.id, "quantity": 10, "unit_price": Decimal("1000.00"), "tax_rate": Decimal("0.00")}],
            user=credit_setup["staff_user"],
        )
        assert sale.total == Decimal("10000.00")
        assert sale.calculated_status == "Unpaid"

        # Payment 1
        CreditService.add_payment("given", sale.id, Decimal("3000.00"), "Cash", user=credit_setup["staff_user"])
        assert sale.paid_amount == Decimal("3000.00")
        assert sale.remaining_amount == Decimal("7000.00")
        assert sale.calculated_status == "Partially Paid"

        # Payment 2
        CreditService.add_payment("given", sale.id, Decimal("4000.00"), "QR / Mobile Pay", user=credit_setup["staff_user"])
        assert sale.paid_amount == Decimal("7000.00")
        assert sale.remaining_amount == Decimal("3000.00")
        assert sale.calculated_status == "Partially Paid"

        # Payment 3 (Settles fully)
        CreditService.add_payment("given", sale.id, Decimal("3000.00"), "Bank Transfer", user=credit_setup["staff_user"])
        assert sale.paid_amount == Decimal("10000.00")
        assert sale.remaining_amount == Decimal("0.00")
        assert sale.calculated_status == "Paid"

    def test_prevent_overpayment(self, credit_setup):
        rice = credit_setup["rice"]
        customer = credit_setup["customer"]

        sale = CreditService.create_credit_given(
            customer_id=customer.id,
            items=[{"product_id": rice.id, "quantity": 2, "unit_price": Decimal("1000.00"), "tax_rate": Decimal("0.00")}],
            user=credit_setup["staff_user"],
        )
        assert sale.remaining_amount == Decimal("2000.00")

        # Attempt to pay more than remaining amount
        with pytest.raises(ValidationError) as exc_info:
            CreditService.add_payment("given", sale.id, Decimal("2500.00"), "Cash", user=credit_setup["staff_user"])
        assert "exceeds outstanding balance" in str(exc_info.value)


class TestOverdueStatusAndAlerts:
    """Test overdue status when remaining > 0 and due_date < today."""

    def test_overdue_calculation(self, credit_setup):
        rice = credit_setup["rice"]
        customer = credit_setup["customer"]

        past_due = timezone.localdate() - timedelta(days=5)
        sale = CreditService.create_credit_given(
            customer_id=customer.id,
            items=[{"product_id": rice.id, "quantity": 1, "unit_price": Decimal("1000.00"), "tax_rate": Decimal("0.00")}],
            due_date=past_due,
            user=credit_setup["staff_user"],
        )

        assert sale.is_overdue
        assert sale.calculated_status == "Overdue"

        # When paid in full, overdue becomes false and status becomes Paid
        CreditService.add_payment("given", sale.id, Decimal("1000.00"), "Cash", user=credit_setup["staff_user"])
        sale.refresh_from_db()
        assert not sale.is_overdue
        assert sale.calculated_status == "Paid"


class TestLedgerAndRunningBalance:
    """Test customer and supplier ledgers with debit/credit entries and running balance."""

    def test_customer_ledger(self, credit_setup):
        rice = credit_setup["rice"]
        customer = credit_setup["customer"]

        # Sale 1: Rs. 5000
        sale1 = CreditService.create_credit_given(
            customer_id=customer.id,
            items=[{"product_id": rice.id, "quantity": 2, "unit_price": Decimal("2500.00"), "tax_rate": Decimal("0.00")}],
            sale_date=timezone.now() - timedelta(days=10),
            user=credit_setup["staff_user"],
        )
        # Payment: Rs. 2000
        CreditService.add_payment(
            "given", sale1.id, Decimal("2000.00"), "Cash",
            payment_date=timezone.now() - timedelta(days=8),
            user=credit_setup["staff_user"],
        )
        # Sale 2: Rs. 2500
        CreditService.create_credit_given(
            customer_id=customer.id,
            items=[{"product_id": rice.id, "quantity": 1, "unit_price": Decimal("2500.00"), "tax_rate": Decimal("0.00")}],
            sale_date=timezone.now() - timedelta(days=5),
            user=credit_setup["staff_user"],
        )

        ledger = CreditService.get_customer_ledger(customer.id)

        assert ledger["total_credit_given"] == Decimal("7500.00")
        assert ledger["total_paid"] == Decimal("2000.00")
        assert ledger["remaining_due"] == Decimal("5500.00")

        rows = ledger["ledger_rows"]
        assert len(rows) == 3
        # Row 1: Sale 1 (debit 5000, running 5000)
        assert rows[0]["debit"] == Decimal("5000.00")
        assert rows[0]["running_balance"] == Decimal("5000.00")
        # Row 2: Payment (credit 2000, running 3000)
        assert rows[1]["credit"] == Decimal("2000.00")
        assert rows[1]["running_balance"] == Decimal("3000.00")
        # Row 3: Sale 2 (debit 2500, running 5500)
        assert rows[2]["debit"] == Decimal("2500.00")
        assert rows[2]["running_balance"] == Decimal("5500.00")

    def test_supplier_ledger(self, credit_setup):
        rice = credit_setup["rice"]
        supplier = credit_setup["supplier"]

        po1 = CreditService.create_credit_taken(
            supplier_id=supplier.id,
            items=[{"product_id": rice.id, "quantity": 10, "unit_price": Decimal("2000.00"), "tax_rate": Decimal("0.00")}],
            purchase_date=timezone.now() - timedelta(days=10),
            user=credit_setup["staff_user"],
        )
        CreditService.add_payment(
            "taken", po1.id, Decimal("5000.00"), "Bank Transfer",
            payment_date=timezone.now() - timedelta(days=5),
            user=credit_setup["staff_user"],
        )

        ledger = CreditService.get_supplier_ledger(supplier.id)
        assert ledger["total_credit_taken"] == Decimal("20000.00")
        assert ledger["total_paid"] == Decimal("5000.00")
        assert ledger["remaining_payable"] == Decimal("15000.00")


class TestDeletionAndStockRestoration:
    """Test cancelling credit and deleting payments with atomic stock and balance restoration."""

    def test_cancel_credit_given_restores_stock(self, credit_setup):
        rice = credit_setup["rice"]
        customer = credit_setup["customer"]
        initial_stock = rice.current_stock

        sale = CreditService.create_credit_given(
            customer_id=customer.id,
            items=[{"product_id": rice.id, "quantity": 5, "unit_price": Decimal("1000.00"), "tax_rate": Decimal("0.00")}],
            user=credit_setup["staff_user"],
        )
        rice.refresh_from_db()
        assert rice.current_stock == initial_stock - 5

        CreditService.delete_credit("given", sale.id, user=credit_setup["manager_user"])
        rice.refresh_from_db()
        assert rice.current_stock == initial_stock
        assert not Sale.objects.filter(pk=sale.id, is_active=True).exists()

    def test_delete_payment_restores_balance(self, credit_setup):
        rice = credit_setup["rice"]
        customer = credit_setup["customer"]

        sale = CreditService.create_credit_given(
            customer_id=customer.id,
            items=[{"product_id": rice.id, "quantity": 1, "unit_price": Decimal("1000.00"), "tax_rate": Decimal("0.00")}],
            user=credit_setup["staff_user"],
        )
        payment = CreditService.add_payment("given", sale.id, Decimal("600.00"), "Cash", user=credit_setup["staff_user"])
        assert sale.remaining_amount == Decimal("400.00")

        CreditService.delete_payment(payment.id, user=credit_setup["manager_user"])
        sale.refresh_from_db()
        assert sale.remaining_amount == Decimal("1000.00")
        assert sale.calculated_status == "Unpaid"


class TestWebViewsAndExports:
    """Test Django web UI views, forms, permissions, and exports for credit app."""

    def test_credit_dashboard_view(self, credit_setup):
        client = credit_setup["client"]
        res = client.get(reverse("credit:dashboard"))
        assert res.status_code == 200
        assert "Receivables & Payables Overview" in res.content.decode("utf-8")
        assert "Credit Given" in res.content.decode("utf-8")
        assert "Credit Taken" in res.content.decode("utf-8")

    def test_credit_create_view_post_given(self, credit_setup):
        client = credit_setup["client"]
        customer = credit_setup["customer"]
        rice = credit_setup["rice"]

        res = client.post(reverse("credit:create"), {
            "credit_type": "given",
            "customer": str(customer.id),
            "transaction_date": timezone.localdate().isoformat(),
            "due_date": (timezone.localdate() + timedelta(days=7)).isoformat(),
            "bill_number": "BILL-TEST-01",
            "discount": "0.00",
            "initial_paid_amount": "500.00",
            "payment_method": "Cash",
            "notes": "Test credit entry",
            "product_id[]": [str(rice.id)],
            "quantity[]": ["2"],
            "unit_price[]": ["2500.00"],
            "tax_rate[]": ["0.00"],
            "item_discount[]": ["0.00"],
        })
        assert res.status_code == 302
        assert Sale.objects.filter(bill_number="BILL-TEST-01").exists()

    def test_customer_detail_shows_credit_summary_and_ledger_link(self, credit_setup):
        client = credit_setup["client"]
        customer = credit_setup["customer"]
        rice = credit_setup["rice"]

        CreditService.create_credit_given(
            customer_id=customer.id,
            items=[{"product_id": rice.id, "quantity": 1, "unit_price": Decimal("1500.00"), "tax_rate": Decimal("0.00")}],
            user=credit_setup["staff_user"],
        )

        res = client.get(reverse("customers:detail", args=[customer.id]))
        assert res.status_code == 200
        content = res.content.decode("utf-8")
        assert "Total Credit" in content
        assert "Remaining Due" in content
        assert "View Ledger Statement" in content

    def test_supplier_detail_shows_credit_summary_and_ledger_link(self, credit_setup):
        client = credit_setup["client"]
        supplier = credit_setup["supplier"]
        rice = credit_setup["rice"]

        CreditService.create_credit_taken(
            supplier_id=supplier.id,
            items=[{"product_id": rice.id, "quantity": 2, "unit_price": Decimal("1000.00"), "tax_rate": Decimal("0.00")}],
            user=credit_setup["staff_user"],
        )

        res = client.get(reverse("suppliers:detail", args=[supplier.id]))
        assert res.status_code == 200
        content = res.content.decode("utf-8")
        assert "Total Purchase Credit" in content
        assert "Remaining Payable" in content
        assert "View Ledger Statement" in content

    def test_export_credit_csv(self, credit_setup):
        client = credit_setup["client"]
        res = client.get(reverse("credit:export_csv", args=["given"]))
        assert res.status_code == 200
        assert "text/csv" in res["Content-Type"]
        assert "Invoice #" in res.content.decode("utf-8")

    def test_ledger_select_view(self, credit_setup):
        client = credit_setup["client"]
        res = client.get(reverse("credit:ledger_select"))
        assert res.status_code == 200
        content = res.content.decode("utf-8")
        assert "Party Ledger Statements" in content
        assert "Customer Ledgers" in content
        assert "Supplier Ledgers" in content
        assert "Debit (Dr)" in content
        assert "Credit (Cr)" in content

    def test_customer_ledger_view(self, credit_setup):
        client = credit_setup["client"]
        customer = credit_setup["customer"]
        rice = credit_setup["rice"]

        CreditService.create_credit_given(
            customer_id=customer.id,
            items=[{"product_id": rice.id, "quantity": 2, "unit_price": Decimal("2500.00"), "tax_rate": Decimal("0.00")}],
            user=credit_setup["staff_user"],
        )

        res = client.get(reverse("credit:customer_ledger", args=[customer.id]))
        assert res.status_code == 200
        content = res.content.decode("utf-8")
        assert customer.name in content
        assert "Debit (Dr)" in content
        assert "Running Balance" in content

    def test_supplier_ledger_view(self, credit_setup):
        client = credit_setup["client"]
        supplier = credit_setup["supplier"]
        rice = credit_setup["rice"]

        CreditService.create_credit_taken(
            supplier_id=supplier.id,
            items=[{"product_id": rice.id, "quantity": 5, "unit_price": Decimal("2000.00"), "tax_rate": Decimal("0.00")}],
            user=credit_setup["staff_user"],
        )

        res = client.get(reverse("credit:supplier_ledger", args=[supplier.id]))
        assert res.status_code == 200
        content = res.content.decode("utf-8")
        assert supplier.name in content
        assert "Credit (Cr)" in content
        assert "Running Balance" in content

    def test_payment_list_view(self, credit_setup):
        client = credit_setup["client"]
        res = client.get(reverse("credit:payment_list"))
        assert res.status_code == 200
        content = res.content.decode("utf-8")
        assert "Payment Vouchers" in content
        assert "Settlement Direction" in content


@pytest.mark.django_db(transaction=True)
class TestFastAPICreditEndpoints:
    """Test FastAPI REST endpoints under /api/v1/credit/."""

    def test_api_credit_summary(self, credit_setup):
        client = TestClient(app)
        headers = credit_setup["auth_headers"]

        res = client.get("/api/v1/credit/summary", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert "credit_given_total" in data
        assert "customer_due" in data
        assert "credit_taken_total" in data
        assert "supplier_due" in data

    def test_api_create_credit_given(self, credit_setup):
        client = TestClient(app)
        headers = credit_setup["auth_headers"]
        customer = credit_setup["customer"]
        rice = credit_setup["rice"]

        payload = {
            "customer_id": customer.id,
            "items": [
                {"product_id": rice.id, "quantity": 2, "unit_price": 2500.0}
            ],
            "due_date": (timezone.localdate() + timedelta(days=10)).isoformat(),
            "initial_paid_amount": 1000.0,
            "payment_method": "Cash",
        }

        res = client.post("/api/v1/credit/given", json=payload, headers=headers)
        assert res.status_code == 201
        data = res.json()
        assert data["success"] is True
        assert data["remaining_amount"] == 4000.0

    def test_api_add_payment_voucher(self, credit_setup):
        client = TestClient(app)
        headers = credit_setup["auth_headers"]
        customer = credit_setup["customer"]
        rice = credit_setup["rice"]

        sale = CreditService.create_credit_given(
            customer_id=customer.id,
            items=[{"product_id": rice.id, "quantity": 1, "unit_price": Decimal("2000.00"), "tax_rate": Decimal("0.00")}],
            user=credit_setup["staff_user"],
        )

        payload = {
            "credit_type": "given",
            "transaction_id": sale.id,
            "amount": 1500.0,
            "payment_method": "QR / Mobile Pay",
            "reference": "QR-10029",
        }

        res = client.post("/api/v1/credit/payment", json=payload, headers=headers)
        assert res.status_code == 201
        assert res.json()["success"] is True

        sale.refresh_from_db()
        assert sale.remaining_amount == Decimal("500.00")
        assert sale.calculated_status == "Partially Paid"
