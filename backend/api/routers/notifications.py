"""
FastAPI REST router for Notifications, Business Alerts, and SMS preferences.
Prefix: /api/v1/notifications
"""
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.deps import get_current_user
from api.schemas.notification import (
    BusinessAlertsSummaryResponse,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
    NotificationResponse,
    TestSMSRequest,
)
from apps.audit.models import Notification, NotificationPreference
from domain.services.notification_service import NotificationService
from domain.services.sms_service import SMSService

router = APIRouter(prefix="/notifications", tags=["Notifications & Alerts"])


def _serialize_notification(n: Notification) -> dict:
    return {
        "id": n.id,
        "notification_type": n.notification_type,
        "title": n.title,
        "message": n.message,
        "priority": n.priority,
        "module": n.module,
        "record_id": n.record_id,
        "is_read": n.is_read,
        "created_at": n.created_at,
        "action_url": n.action_url or "",
    }


@router.get("/alerts-summary", response_model=BusinessAlertsSummaryResponse, summary="Get Central Business Alerts Counters")
def get_alerts_summary(current_user: Any = Depends(get_current_user)):
    """Return counts for Section 18 Business Alerts dashboard widget."""
    company_id = getattr(current_user.active_company, "id", None)
    NotificationService.run_all_monitors(company_id=company_id, user=current_user)
    alerts = NotificationService.get_dashboard_business_alerts(company_id=company_id)
    total = sum(alerts.values())
    return {
        "out_of_stock": alerts["out_of_stock"],
        "low_stock": alerts["low_stock"],
        "stock_received": alerts["stock_received"],
        "payments_due": alerts["payments_due"],
        "cheques_due": alerts["cheques_due"],
        "receivables_overdue": alerts["receivables_overdue"],
        "payables_overdue": alerts["payables_overdue"],
        "total_alerts": total,
    }


@router.get("/unread-count", summary="Get Unread Notifications Count")
def get_unread_count(current_user: Any = Depends(get_current_user)):
    """Return total unread notifications count for bell badge."""
    count = NotificationService.get_unread_count(user=current_user)
    return {"unread_count": count}


@router.get("/popups", summary="Get Active Popups")
def get_popups(current_user: Any = Depends(get_current_user)):
    """Return active dismissible in-app popup notifications."""
    popups = NotificationService.get_active_popups(user=current_user)
    return [_serialize_notification(p) for p in popups]


@router.get("/", summary="List Notifications")
def list_notifications(
    unread_only: bool = Query(False, description="Filter unread only"),
    priority: Optional[str] = Query(None, description="critical, high, normal, info"),
    module: Optional[str] = Query(None, description="inventory, sales, purchases, credit, cheque"),
    current_user: Any = Depends(get_current_user),
):
    """Retrieve notifications for the current user and active company."""
    company_id = getattr(current_user.active_company, "id", None)
    qs = Notification.objects.filter(is_active=True)
    if company_id:
        from django.db.models import Q
        qs = qs.filter(Q(company_id=company_id) | Q(company__isnull=True))
    if current_user:
        from django.db.models import Q
        qs = qs.filter(Q(user_id=current_user.id) | Q(user__isnull=True))

    if unread_only:
        qs = qs.filter(is_read=False)
    if priority:
        qs = qs.filter(priority=priority.lower())
    if module:
        qs = qs.filter(module=module.lower())

    return [_serialize_notification(n) for n in qs.order_by("-created_at")[:100]]


@router.post("/{notification_id}/read", summary="Mark Notification as Read")
def mark_notification_read(notification_id: int, current_user: Any = Depends(get_current_user)):
    """Mark a specific notification as read."""
    company_id = getattr(current_user.active_company, "id", None)
    qs = Notification.objects.filter(id=notification_id)
    if company_id:
        from django.db.models import Q
        qs = qs.filter(Q(company_id=company_id) | Q(company__isnull=True))
    notif = qs.first()
    if not notif:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
    notif.is_read = True
    notif.save(update_fields=["is_read"])
    return {"status": "success", "id": notif.id, "is_read": True}


@router.post("/mark-all-read", summary="Mark All Notifications as Read")
def mark_all_read(current_user: Any = Depends(get_current_user)):
    """Mark all active notifications as read."""
    company_id = getattr(current_user.active_company, "id", None)
    qs = Notification.objects.filter(is_active=True, is_read=False)
    if company_id:
        from django.db.models import Q
        qs = qs.filter(Q(company_id=company_id) | Q(company__isnull=True))
    if current_user:
        from django.db.models import Q
        qs = qs.filter(Q(user_id=current_user.id) | Q(user__isnull=True))
    updated = qs.update(is_read=True)
    return {"status": "success", "marked_read_count": updated}


@router.post("/{notification_id}/dismiss-popup", summary="Dismiss In-App Popup")
def dismiss_popup(notification_id: int, current_user: Any = Depends(get_current_user)):
    """Dismiss an in-app popup alert."""
    dismissed = NotificationService.dismiss_popup(user=current_user, notification_id=notification_id)
    if not dismissed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification popup not found.")
    return {"status": "success", "dismissed": True}


@router.get("/settings", response_model=NotificationPreferenceResponse, summary="Get Notification Preferences")
def get_notification_settings(current_user: Any = Depends(get_current_user)):
    """Retrieve notification and SMS preferences for the authenticated user."""
    pref, _ = NotificationPreference.objects.get_or_create(
        user=current_user,
        defaults={"sms_phone_number": getattr(current_user, "phone", "") or ""},
    )
    return {
        "stock_low": pref.notify_low_stock,
        "stock_critical": pref.notify_critical_stock,
        "stock_out": pref.notify_out_of_stock,
        "stock_received": pref.notify_stock_received,
        "stock_restored": pref.notify_stock_restored,
        "payment_due": pref.notify_payment_due,
        "payment_overdue": pref.notify_payment_overdue,
        "cheque_due": pref.notify_cheque_due_soon,
        "receivable_overdue": pref.notify_receivable_overdue,
        "payable_overdue": pref.notify_payable_overdue,
        "sms_enabled": pref.sms_enabled,
        "sms_phone": pref.sms_phone_number,
        "in_app_popups_enabled": pref.popup_enabled,
    }


@router.patch("/settings", response_model=NotificationPreferenceResponse, summary="Update Notification Preferences")
def update_notification_settings(
    payload: NotificationPreferenceUpdate,
    current_user: Any = Depends(get_current_user),
):
    """Update notification and SMS delivery preferences."""
    pref, _ = NotificationPreference.objects.get_or_create(
        user=current_user,
        defaults={"sms_phone_number": getattr(current_user, "phone", "") or ""},
    )

    mapping = {
        "stock_low": "notify_low_stock",
        "stock_critical": "notify_critical_stock",
        "stock_out": "notify_out_of_stock",
        "stock_received": "notify_stock_received",
        "stock_restored": "notify_stock_restored",
        "payment_due": "notify_payment_due",
        "payment_overdue": "notify_payment_overdue",
        "cheque_due": "notify_cheque_due_soon",
        "receivable_overdue": "notify_receivable_overdue",
        "payable_overdue": "notify_payable_overdue",
        "sms_enabled": "sms_enabled",
        "sms_phone": "sms_phone_number",
        "in_app_popups_enabled": "popup_enabled",
    }
    update_data = payload.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        if k in mapping and v is not None:
            setattr(pref, mapping[k], v)
    pref.save()

    return {
        "stock_low": pref.notify_low_stock,
        "stock_critical": pref.notify_critical_stock,
        "stock_out": pref.notify_out_of_stock,
        "stock_received": pref.notify_stock_received,
        "stock_restored": pref.notify_stock_restored,
        "payment_due": pref.notify_payment_due,
        "payment_overdue": pref.notify_payment_overdue,
        "cheque_due": pref.notify_cheque_due_soon,
        "receivable_overdue": pref.notify_receivable_overdue,
        "payable_overdue": pref.notify_payable_overdue,
        "sms_enabled": pref.sms_enabled,
        "sms_phone": pref.sms_phone_number,
        "in_app_popups_enabled": pref.popup_enabled,
    }


@router.post("/test-sms", summary="Send Test SMS")
def send_test_sms(payload: TestSMSRequest, current_user: Any = Depends(get_current_user)):
    """Dispatch a test SMS message using the configured SMS gateway."""
    pref = NotificationPreference.objects.filter(user=current_user).first()
    target_phone = payload.phone or (pref.sms_phone_number if pref else "") or getattr(current_user, "phone", "")
    if not target_phone:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No phone number configured for SMS dispatch.")

    result = SMSService.send_alert_sms(
        user=current_user,
        notification_type="test",
        message="BizFlow TEST: Your business notification SMS gateway is operational.",
        force_phone=target_phone,
    )
    if result.get("sent"):
        return {"status": "success", "message": f"Test SMS sent to {target_phone}"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error") or "Failed to dispatch test SMS.",
        )
