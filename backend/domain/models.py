"""
Domain models and DTOs (Data Transfer Objects).

Framework-agnostic data structures passed into and returned from application services.
These contain pure business representations without binding to HTTP request/response objects.
"""
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal


@dataclass
class LineItemInput:
    """Represents a product item line on a sale or purchase."""

    product_id: int
    quantity: int
    unit_price: Decimal | None = None
    discount: Decimal = Decimal("0.00")
    tax_rate: Decimal = Decimal("0.00")


@dataclass
class CalculationResult:
    """Summary of financial computations for an order/invoice."""

    subtotal: Decimal
    total_discount: Decimal
    total_tax: Decimal
    grand_total: Decimal


@dataclass
class SaleInput:
    """Input payload required to record a sales invoice."""

    items: list[LineItemInput]
    company_id: int | None = None
    customer_id: int | None = None
    discount: Decimal = Decimal("0.00")
    payment_status: str = "Due"
    payment_method: str = "Cash"
    bill_number: str | None = None
    cheque_number: str | None = None
    cheque_date: date | None = None
    notes: str = ""
    sale_date: datetime | None = None


@dataclass
class PurchaseInput:
    """Input payload required to record a purchase bill."""

    items: list[LineItemInput]
    supplier_id: int | None = None
    company_id: int | None = None
    discount: Decimal = Decimal("0.00")
    payment_status: str = "Due"
    payment_method: str = "Cash"
    bill_number: str | None = None
    cheque_number: str | None = None
    cheque_date: date | None = None
    notes: str = ""
    purchase_date: datetime | None = None


@dataclass
class DashboardMetrics:
    """Aggregated business KPIs for dashboard presentation."""

    total_sales: Decimal
    total_purchases: Decimal
    total_expenses: Decimal
    gross_profit: Decimal
    total_customers: int
    total_products: int
    low_stock_count: int