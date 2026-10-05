"""
Pydantic schemas for Cheque Management REST API.
"""
from datetime import date
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class ChequeCreateRequest(BaseModel):
    cheque_type: str = Field(..., description="GIVEN or RECEIVED")
    cheque_number: str = Field(..., max_length=64, description="Cheque serial/leaf number")
    bank_name: str = Field(..., max_length=128, description="Drawee Bank name")
    amount: Decimal = Field(..., gt=0, description="Cheque face value in Rs.")
    cheque_date: date = Field(..., description="Maturity/presentation date")
    customer_id: Optional[int] = Field(None, description="Customer ID for received cheque")
    supplier_id: Optional[int] = Field(None, description="Supplier ID for given cheque")
    sale_id: Optional[int] = Field(None, description="Linked Sale invoice ID")
    purchase_id: Optional[int] = Field(None, description="Linked Purchase bill ID")
    notes: Optional[str] = Field("", description="Remarks / branch details")


class ChequeStatusUpdateRequest(BaseModel):
    status: str = Field(..., description="PENDING, CLEARED, BOUNCED, or CANCELLED")
    notes: Optional[str] = Field(None, description="Optional clearance/dishonor note")


class ChequeResponse(BaseModel):
    id: int
    cheque_type: str
    cheque_number: str
    bank_name: str
    amount: Decimal
    cheque_date: date
    status: str
    party_name: str
    sale_invoice: Optional[str] = None
    purchase_bill: Optional[str] = None
    days_until_due: int
    is_due_today: bool
    is_overdue: bool
    is_due_soon: bool
    notes: str = ""


class ChequeSummaryResponse(BaseModel):
    total_given: Decimal
    total_received: Decimal
    pending_count: int
    cleared_count: int
    bounced_count: int
    due_today_count: int
    due_soon_count: int
    overdue_count: int
