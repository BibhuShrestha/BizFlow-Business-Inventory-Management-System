"""
Pydantic schemas for Notifications and Business Alerts REST API.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class NotificationResponse(BaseModel):
    id: int
    notification_type: str
    title: str
    message: str
    priority: str
    module: str
    record_id: Optional[int] = None
    is_read: bool
    created_at: datetime
    action_url: str = ""


class BusinessAlertsSummaryResponse(BaseModel):
    out_of_stock: int
    low_stock: int
    stock_received: int
    payments_due: int
    cheques_due: int
    receivables_overdue: int
    payables_overdue: int
    total_alerts: int


class NotificationPreferenceUpdate(BaseModel):
    stock_low: Optional[bool] = None
    stock_critical: Optional[bool] = None
    stock_out: Optional[bool] = None
    stock_received: Optional[bool] = None
    stock_restored: Optional[bool] = None
    payment_due: Optional[bool] = None
    payment_overdue: Optional[bool] = None
    cheque_due: Optional[bool] = None
    receivable_overdue: Optional[bool] = None
    payable_overdue: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    sms_phone: Optional[str] = None
    in_app_popups_enabled: Optional[bool] = None


class NotificationPreferenceResponse(BaseModel):
    stock_low: bool
    stock_critical: bool
    stock_out: bool
    stock_received: bool
    stock_restored: bool
    payment_due: bool
    payment_overdue: bool
    cheque_due: bool
    receivable_overdue: bool
    payable_overdue: bool
    sms_enabled: bool
    sms_phone: str
    in_app_popups_enabled: bool


class TestSMSRequest(BaseModel):
    phone: Optional[str] = Field(None, description="Optional target phone number for test dispatch")
