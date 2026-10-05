"""
SMSService -- Domain service for SMS notification dispatch, deduplication,
safety checks, cost control, and audit logging.
"""
from datetime import datetime
import logging
import re
from typing import Any, Dict

from django.conf import settings
from django.utils import timezone

from apps.audit.models import AuditLog, SMSLog, NotificationPreference
from integrations.sms import get_sms_gateway

logger = logging.getLogger(__name__)


class SMSService:
    """Handles dispatch of transactional SMS with strict cost-control and deduplication."""

    @staticmethod
    def sanitize_phone(phone: str) -> str:
        """Strip spaces, dashes, and ensure clean phone digits or international format."""
        if not phone:
            return ""
        cleaned = re.sub(r"[^\d+]", "", phone.strip())
        return cleaned

    @classmethod
    def can_send_sms_to_user(cls, user: Any, notification_type: str) -> tuple[bool, str]:
        """
        Check if user has SMS enabled, a valid phone number, and preferences permitting this type.
        Returns: (can_send: bool, phone_number: str)
        """
        if not user or not getattr(user, "is_authenticated", False):
            return False, ""

        pref, _ = NotificationPreference.objects.get_or_create(user=user)
        if not pref.sms_enabled:
            return False, ""

        phone = cls.sanitize_phone(pref.sms_phone_number)
        if not phone or len(phone) < 7:
            # Fallback to user phone if available
            phone = cls.sanitize_phone(getattr(user, "phone", ""))
        if not phone or len(phone) < 7:
            return False, ""

        # Check type-specific preference
        type_field_map = {
            "low_stock": "notify_low_stock",
            "critical_stock": "notify_critical_stock",
            "out_of_stock": "notify_out_of_stock",
            "stock_received": "notify_stock_received",
            "stock_restored": "notify_stock_restored",
            "payment_due": "notify_payment_due",
            "payment_overdue": "notify_payment_overdue",
            "cheque_due_soon": "notify_cheque_due_soon",
            "cheque_due_today": "notify_cheque_due_today",
            "cheque_overdue": "notify_cheque_overdue",
            "receivable_due": "notify_receivable_due",
            "receivable_overdue": "notify_receivable_overdue",
            "payable_due": "notify_payable_due",
            "payable_overdue": "notify_payable_overdue",
        }
        field_name = type_field_map.get(notification_type)
        if field_name and not getattr(pref, field_name, True):
            return False, ""

        return True, phone

    @classmethod
    def send_alert_sms(
        cls,
        user: Any,
        notification_type: str,
        message: str,
        dedup_key: str = "",
        force_phone: str = "",
    ) -> Dict[str, Any]:
        """
        Dispatch an SMS alert if enabled and not previously sent under the same dedup_key.
        """
        # Determine phone number
        phone = force_phone
        if not phone:
            can_send, user_phone = cls.can_send_sms_to_user(user, notification_type)
            if not can_send:
                return {"sent": False, "reason": "SMS disabled or phone not configured", "log_id": None}
            phone = user_phone

        # Deduplication check: Do not re-send identical dedup_key within the cycle
        if dedup_key:
            already_sent = SMSLog.objects.filter(
                dedup_key=dedup_key,
                recipient=phone,
                status="Sent",
            ).exists()
            if already_sent:
                logger.info("SMS deduplicated for key '%s' to %s", dedup_key, phone)
                return {"sent": False, "reason": "Deduplicated: already sent", "log_id": None}

        # Dispatch via configured gateway
        gateway = get_sms_gateway()
        result = gateway.send_sms(to_phone=phone, message=message)
        is_success = result.get("success", False)
        status_text = "Sent" if is_success else "Failed"
        error_msg = result.get("error") or ""

        # Create SMS log
        sms_log = SMSLog.objects.create(
            user=user if getattr(user, "is_authenticated", False) else None,
            recipient=phone,
            message=message,
            notification_type=notification_type,
            status=status_text,
            provider=result.get("provider", "mock"),
            dedup_key=dedup_key,
            error_message=error_msg,
        )

        # Audit log
        try:
            AuditLog.objects.create(
                user=user if getattr(user, "is_authenticated", False) else None,
                module="SMS",
                action="SMS Sent" if is_success else "SMS Failed",
                record_type="SMSLog",
                record_id=sms_log.id,
                description=f"SMS ({notification_type}) to {phone}: {message[:50]}...",
                success=is_success,
            )
        except Exception:
            pass

        return {
            "sent": is_success,
            "status": status_text,
            "log_id": sms_log.id,
            "error": error_msg,
        }
