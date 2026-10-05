"""
Unit and integration tests for Shared Business Logic (Part 6).
Tests domain services, validators, repositories, and calculation invariants.
"""
from decimal import Decimal
import pytest
from apps.accounts.models import Role, User
from apps.companies.models import Company
from apps.inventory.models import Category, Product, StockMovement
from apps.sales.models import Customer, Sale
from apps.purchases.models import Supplier, Purchase
from apps.accounting.models import Expense
from core.exceptions import InsufficientStockError, ValidationError, NotFoundError
from domain.models import SaleInput, PurchaseInput, LineItemInput
from services import StockService, SaleService, PurchaseService, ReportService, NepaliDateService
from repositories import ProductRepository, SaleRepository
from validators import validate_pan_vat, calculate_tax, validate_positive_amount


@pytest.mark.django_db
class TestSharedBusinessLogic:
    """Verifies all shared application services execute business rules correctly."""

    @pytest.fixture
    def setup_data(self):
        comp = Company.objects.create(company_name="Apex Corp", vat_pan_number="123456789")
        cat = Category.objects.create(name="Hardware")
        prod = Product.objects.create(
            sku="HW-DRILL-01",
            name="Power Drill",
            category=cat,
            company=comp,
            purchase_price=Decimal("2000.00"),
            selling_price=Decimal("3000.00"),
            current_stock=10,
            minimum_stock=2,
            tax_rate=Decimal("13.00"),
        )
        cust = Customer.objects.create(name="Biraj Shrestha", company=comp)
        supp = Supplier.objects.create(name="Bosch Tools Nepal", company=comp)
        return {"company": comp, "category": cat, "product": prod, "customer": cust, "supplier": supp}

    def test_stock_deduction_and_insufficient_stock(self, setup_data):
        prod = setup_data["product"]
        # Deduct 4 items
        movement = StockService.deduct(prod.id, 4, StockMovement.REFERENCE_SALE)
        prod.refresh_from_db()
        assert prod.current_stock == 6
        assert movement.quantity == 4
        assert movement.movement_type == StockMovement.MOVEMENT_OUT

        # Attempt to deduct 10 items (only 6 available) -> InsufficientStockError
        with pytest.raises(InsufficientStockError) as exc_info:
            StockService.deduct(prod.id, 10, StockMovement.REFERENCE_SALE)
        assert exc_info.value.available == 6
        assert exc_info.value.requested == 10
        prod.refresh_from_db()
        assert prod.current_stock == 6  # Unchanged

    def test_sale_creation_and_stock_management(self, setup_data):
        prod = setup_data["product"]
        cust = setup_data["customer"]
        comp = setup_data["company"]

        sale_input = SaleInput(
            company_id=comp.id,
            customer_id=cust.id,
            items=[LineItemInput(product_id=prod.id, quantity=3, unit_price=Decimal("3000.00"), tax_rate=Decimal("13.00"))],
            discount=Decimal("500.00"),
        )

        sale = SaleService.create(sale_input)
        assert sale.id is not None
        assert sale.invoice_number.startswith("INV-")
        # Subtotal: 3 * 3000 = 9000. Tax: 13% of 9000 = 1170. Total before order discount: 10170. Minus 500 = 9670
        assert sale.total == Decimal("9670.00")

        # Verify stock was decremented from 10 to 7
        prod.refresh_from_db()
        assert prod.current_stock == 7

        # Verify stock movement record was created
        assert StockMovement.objects.filter(reference_type=StockMovement.REFERENCE_SALE, reference_id=sale.id).exists()

        # Cancel sale -> stock restored to 10
        SaleService.cancel(sale.id)
        prod.refresh_from_db()
        assert prod.current_stock == 10
        sale.refresh_from_db()
        assert sale.is_active is False

    def test_purchase_creation_and_cancellation(self, setup_data):
        prod = setup_data["product"]
        supp = setup_data["supplier"]
        comp = setup_data["company"]

        purch_input = PurchaseInput(
            company_id=comp.id,
            supplier_id=supp.id,
            items=[LineItemInput(product_id=prod.id, quantity=5, unit_price=Decimal("2000.00"))],
            discount=Decimal("0.00"),
        )

        purchase = PurchaseService.create(purch_input)
        assert purchase.purchase_number.startswith("PO-")
        assert purchase.total == Decimal("10000.00")

        # Verify stock increased from 10 to 15
        prod.refresh_from_db()
        assert prod.current_stock == 15

        # Cancel purchase -> stock returned to 10
        PurchaseService.cancel(purchase.id)
        prod.refresh_from_db()
        assert prod.current_stock == 10
        purchase.refresh_from_db()
        assert purchase.is_active is False

    def test_report_service_metrics(self, setup_data):
        comp = setup_data["company"]
        prod = setup_data["product"]
        cust = setup_data["customer"]

        # Record a sale
        SaleService.create({
            "company_id": comp.id,
            "customer_id": cust.id,
            "items": [{"product_id": prod.id, "quantity": 1, "unit_price": Decimal("1000.00"), "discount": Decimal("0.00"), "tax_rate": Decimal("0.00")}],
        })

        # Record an expense
        Expense.objects.create(company=comp, category="Rent", amount=Decimal("200.00"), expense_date=prod.created_at)

        metrics = ReportService.get_dashboard_metrics(company_id=comp.id)
        assert metrics.total_sales == Decimal("1130.00")
        assert metrics.total_expenses == Decimal("200.00")
        assert metrics.gross_profit == Decimal("930.00")
        assert metrics.total_products >= 1

    def test_nepali_date_service(self):
        from datetime import date
        bs_date = NepaliDateService.ad_to_bs(date(2024, 4, 13))
        assert bs_date.year == 2081
        assert bs_date.month == 1
        assert bs_date.day == 1

    def test_validators(self):
        # PAN / VAT
        assert validate_pan_vat("123456789") == "123456789"
        with pytest.raises(ValidationError):
            validate_pan_vat("12345")  # Not 9 digits

        # Tax calculation
        assert calculate_tax(Decimal("1000.00"), Decimal("13.00")) == Decimal("130.00")
        assert calculate_tax(Decimal("1000.00"), Decimal("0.00")) == Decimal("0.00")

        # Positive amount
        assert validate_positive_amount(Decimal("50.00")) == Decimal("50.00")
        with pytest.raises(ValidationError):
            validate_positive_amount(Decimal("-10.00"))

    def test_repositories(self, setup_data):
        prod = setup_data["product"]
        comp = setup_data["company"]

        repo = ProductRepository()
        found = repo.get_by_sku(prod.sku, company_id=comp.id)
        assert found is not None
        assert found.id == prod.id

        # Non-existent SKU
        assert repo.get_by_sku("NON-EXISTENT", company_id=comp.id) is None