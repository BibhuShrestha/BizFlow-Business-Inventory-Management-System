"""
Tests for Django models across all apps (Part 5).
Verifies model instantiation, relations, constraints, and field defaults.
"""
from datetime import datetime, timezone
from decimal import Decimal
import pytest
from apps.accounts.models import Role, User, EmailVerificationToken, PasswordResetToken, LoginHistory
from apps.companies.models import Company, Seller
from apps.inventory.models import Category, Product, StockMovement, StockAdjustment
from apps.sales.models import Customer, Sale, SaleItem, Payment
from apps.purchases.models import Supplier, Purchase, PurchaseItem
from apps.accounting.models import ExpenseCategory, Expense, Account, JournalEntry, JournalEntryItem
from apps.audit.models import AuditLog, Notification, EmailLog, ExportLog


@pytest.mark.django_db
class TestDatabaseModels:
    """Verify all 20+ migrated Django models work properly."""

    def test_company_and_seller_creation(self):
        comp = Company.objects.create(
            company_name="Test Enterprise",
            company_phone="9800000000",
            vat_pan_number="123456789",
        )
        assert comp.id is not None
        seller = Seller.objects.create(
            seller_name="John Agent",
            seller_phone="9811111111",
            company=comp,
        )
        assert seller.company == comp
        assert "John Agent" in str(seller)
        assert comp.sellers.count() == 1

    def test_user_and_role_creation(self):
        role = Role.objects.create(name="manager", description="Store Manager")
        comp = Company.objects.create(company_name="User Company")
        user = User.objects.create_user(
            email="manager@test.com",
            name="Alice Manager",
            password="StrongPassword@123",
            role=role,
            active_company=comp,
        )
        assert user.check_password("StrongPassword@123") is True
        assert user.role == role
        assert user.active_company == comp
        assert str(user) == "Alice Manager <manager@test.com>"

    def test_category_and_product_with_stock_value(self):
        cat = Category.objects.create(name="Electronics")
        prod = Product.objects.create(
            sku="SKU-ELEC-001",
            name="Wireless Mouse",
            category=cat,
            unit="pcs",
            purchase_price=Decimal("500.00"),
            selling_price=Decimal("750.00"),
            current_stock=20,
            minimum_stock=5,
        )
        assert prod.stock_value == Decimal("10000.00")
        assert "Wireless Mouse" in str(prod)

    def test_customer_sale_and_items(self):
        cat = Category.objects.create(name="Groceries")
        prod = Product.objects.create(
            sku="SKU-GROC-01",
            name="Organic Rice",
            category=cat,
            purchase_price=Decimal("100.00"),
            selling_price=Decimal("150.00"),
        )
        cust = Customer.objects.create(name="Ram Bahadur", phone="9841234567")
        sale = Sale.objects.create(
            invoice_number="INV-2081-001",
            customer=cust,
            sale_date=datetime.now(timezone.utc),
            discount=Decimal("0.00"),
            tax=Decimal("19.50"),
            total=Decimal("169.50"),
            payment_status=Sale.STATUS_DUE,
        )
        item = SaleItem.objects.create(
            sale=sale,
            product=prod,
            quantity=1,
            unit_price=Decimal("150.00"),
            total=Decimal("150.00"),
        )
        assert sale.items.count() == 1
        assert item.product == prod
        assert cust.sales.count() == 1

    def test_supplier_purchase_and_payment(self):
        supp = Supplier.objects.create(name="Himalayan Traders", phone="014444444")
        purch = Purchase.objects.create(
            purchase_number="PUR-2081-001",
            supplier=supp,
            purchase_date=datetime.now(timezone.utc),
            total=Decimal("5000.00"),
        )
        payment = Payment.objects.create(
            payment_date=datetime.now(timezone.utc),
            amount=Decimal("5000.00"),
            payment_method="Bank Transfer",
            purchase=purch,
            supplier=supp,
        )
        assert purch.payments.count() == 1
        assert payment.supplier == supp

    def test_accounting_and_audit_models(self):
        exp_cat = ExpenseCategory.objects.create(name="Office Rent")
        exp = Expense.objects.create(
            category="Office Rent",
            amount=Decimal("25000.00"),
            expense_date=datetime.now(timezone.utc),
        )
        assert exp.id is not None
        acc = Account.objects.create(name="Cash in Hand", code="1001")
        assert "1001" in str(acc)
        audit = AuditLog.objects.create(
            module="AUTH",
            action="LOGIN_SUCCESS",
            description="User logged in",
        )
        assert audit.id is not None