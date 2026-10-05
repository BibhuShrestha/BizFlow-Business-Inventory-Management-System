"""
SMS Gateway Integration Layer.
Provides pluggable, configurable SMS gateways (Console, Mock, Sparrow SMS, Twilio)
with safety controls and error handling.
"""
from abc import ABC, abstractmethod
import logging
import os
from typing import Any, Dict, List

from django.conf import settings

logger = logging.getLogger(__name__)


class BaseSMSGateway(ABC):
    """Abstract SMS Gateway Interface."""

    @abstractmethod
    def send_sms(self, to_phone: str, message: str) -> Dict[str, Any]:
        """
        Dispatch an SMS to the designated recipient.

        Args:
            to_phone: E.164 or local phone number format.
            message: Text message content.

        Returns:
            dict with keys: {"success": bool, "provider": str, "message_id": str, "error": str | None}
        """
        pass


class ConsoleSMSGateway(BaseSMSGateway):
    """Logs SMS to console/logger for development and testing."""

    def send_sms(self, to_phone: str, message: str) -> Dict[str, Any]:
        logger.info("[SMS-CONSOLE] Dispatch to %s: %s", to_phone, message)
        return {
            "success": True,
            "provider": "console",
            "message_id": f"console-{os.urandom(4).hex()}",
            "error": None,
        }


class MockSMSGateway(BaseSMSGateway):
    """In-memory gateway for unit tests."""

    def __init__(self):
        self.sent_messages: List[Dict[str, str]] = []

    def send_sms(self, to_phone: str, message: str) -> Dict[str, Any]:
        record = {"to_phone": to_phone, "message": message}
        self.sent_messages.append(record)
        return {
            "success": True,
            "provider": "mock",
            "message_id": f"mock-{len(self.sent_messages)}",
            "error": None,
        }

    def clear(self):
        self.sent_messages.clear()


class SparrowSMSGateway(BaseSMSGateway):
    """Gateway for Sparrow SMS (Nepal)."""

    def __init__(self, token: str | None = None, sender: str | None = None):
        self.token = token or getattr(settings, "SPARROW_SMS_TOKEN", "") or os.getenv("SPARROW_SMS_TOKEN", "")
        self.sender = sender or getattr(settings, "SPARROW_SMS_FROM", "") or os.getenv("SPARROW_SMS_FROM", "BizFlow")
        self.api_url = "http://api.sparrowsms.com/v2/sms/"

    def send_sms(self, to_phone: str, message: str) -> Dict[str, Any]:
        if not self.token:
            return {"success": False, "provider": "sparrow", "message_id": "", "error": "Sparrow SMS token not configured."}
        try:
            import requests
            params = {
                "token": self.token,
                "from": self.sender,
                "to": to_phone,
                "text": message,
            }
            res = requests.post(self.api_url, data=params, timeout=5)
            if res.status_code == 200:
                return {"success": True, "provider": "sparrow", "message_id": res.text.strip(), "error": None}
            return {"success": False, "provider": "sparrow", "message_id": "", "error": f"HTTP {res.status_code}: {res.text}"}
        except Exception as exc:
            logger.error("Sparrow SMS error: %s", exc)
            return {"success": False, "provider": "sparrow", "message_id": "", "error": str(exc)}


class TwilioSMSGateway(BaseSMSGateway):
    """Gateway for Twilio SMS."""

    def __init__(self, account_sid: str | None = None, auth_token: str | None = None, from_number: str | None = None):
        self.account_sid = account_sid or getattr(settings, "TWILIO_ACCOUNT_SID", "") or os.getenv("TWILIO_ACCOUNT_SID", "")
        self.auth_token = auth_token or getattr(settings, "TWILIO_AUTH_TOKEN", "") or os.getenv("TWILIO_AUTH_TOKEN", "")
        self.from_number = from_number or getattr(settings, "TWILIO_FROM_NUMBER", "") or os.getenv("TWILIO_FROM_NUMBER", "")

    def send_sms(self, to_phone: str, message: str) -> Dict[str, Any]:
        if not (self.account_sid and self.auth_token and self.from_number):
            return {"success": False, "provider": "twilio", "message_id": "", "error": "Twilio credentials not configured."}
        try:
            import requests
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
            res = requests.post(
                url,
                data={"From": self.from_number, "To": to_phone, "Body": message},
                auth=(self.account_sid, self.auth_token),
                timeout=5,
            )
            data = res.json()
            if res.status_code in (200, 201):
                return {"success": True, "provider": "twilio", "message_id": data.get("sid", ""), "error": None}
            return {"success": False, "provider": "twilio", "message_id": "", "error": data.get("message", res.text)}
        except Exception as exc:
            logger.error("Twilio SMS error: %s", exc)
            return {"success": False, "provider": "twilio", "message_id": "", "error": str(exc)}


_mock_instance: MockSMSGateway | None = None


def get_sms_gateway(gateway_type: str | None = None) -> BaseSMSGateway:
    """
    Factory to retrieve configured SMS Gateway.
    Default determined by settings.SMS_GATEWAY or env SMS_GATEWAY.
    """
    global _mock_instance
    gw = gateway_type or getattr(settings, "SMS_GATEWAY", "") or os.getenv("SMS_GATEWAY", "console")
    gw = gw.lower().strip()

    if gw == "mock":
        if _mock_instance is None:
            _mock_instance = MockSMSGateway()
        return _mock_instance
    elif gw == "sparrow":
        return SparrowSMSGateway()
    elif gw == "twilio":
        return TwilioSMSGateway()
    return ConsoleSMSGateway()
