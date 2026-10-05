"""
Pydantic schemas for Receivables & Payables Management REST API.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class CreditItemInput(BaseModel):
    product_id: int = Field(..., description="ID of catalog Product")
    quantity: int = Field(1, ge=1, description="Quantity")
    unit_price: Optional[Decimal] = Field(None, ge=0, description="Override unit price (defaults to catalog price)")
    tax_rate: Optional[Decimal] = Field(Decimal("0.00"), ge=0, description="Tax rate percentage")
    discount: Optional[Decimal] = Field(Decimal("0.00"), ge=0, description="Line discount in Rs.")


class CreditGivenCreateRequest(BaseModel):
    customer_id: int = Field(..., description="Customer ID")
    items: list[CreditItemInput] = Field(..., min_length=1, description="Product line items")
    due_date: Optional[date] = Field(None, description="Due date for credit settlement")
    sale_date: Optional[date] = Field(None, description="Transaction date (defaults to today)")
    bill_number: Optional[str] = Field("", max_length=64, description="Optional invoice or bill number")
    discount: Optional[Decimal] = Field(Decimal("0.00"), ge=0, description="Overall invoice discount in Rs.")
    initial_paid_amount: Optional[Decimal] = Field(Decimal("0.00"), ge=0, description="Initial down payment in Rs.")
    payment_method: Optional[str] = Field("Cash", description="Payment method for down payment")
    notes: Optional[str] = Field("", description="Remarks / terms")


class CreditTakenCreateRequest(BaseModel):
    supplier_id: int = Field(..., description="Supplier ID")
    items: list[CreditItemInput] = Field(..., min_length=1, description="Product line items")
    due_date: Optional[date] = Field(None, description="Due date for credit payable settlement")
    purchase_date: Optional[date] = Field(None, description="Transaction date (defaults to today)")
    bill_number: Optional[str] = Field("", max_length=64, description="Supplier bill reference number")
    discount: Optional[Decimal] = Field(Decimal("0.00"), ge=0, description="Overall bill discount in Rs.")
    initial_paid_amount: Optional[Decimal] = Field(Decimal("0.00"), ge=0, description="Initial down payment in Rs.")
    payment_method: Optional[str] = Field("Cash", description="Payment method for down payment")
    notes: Optional[str] = Field("", description="Remarks / terms")


class PaymentAddRequest(BaseModel):
    credit_type: str = Field(..., description="'given' (customer sale) or 'taken' (supplier purchase)")
    transaction_id: int = Field(..., description="ID of Sale or Purchase")
    amount: Decimal = Field(..., gt=0, description="Payment voucher amount in Rs.")
    payment_date: Optional[date] = Field(None, description="Date of payment")
    payment_method: Optional[str] = Field("Cash", description="Cash, QR, Bank, Cheque")
    reference: Optional[str] = Field("", description="Receipt, cheque, or transaction reference")
    notes: Optional[str] = Field("", description="Notes / remarks")


class CreditSummaryResponse(BaseModel):
    credit_given_total: Decimal
    credit_given_received: Decimal
    customer_due: Decimal
    credit_taken_total: Decimal
    credit_taken_paid: Decimal
    supplier_due: Decimal
    overdue_given_count: int
    overdue_given_amount: Decimal
    overdue_taken_count: int
    overdue_taken_amount: Decimal
    total_overdue_amount: Decimal
