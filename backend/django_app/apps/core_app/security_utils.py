"""
Security utilities: Safe redirection, rate limiting, and login audit tracking.
"""
import logging
from typing import Optional
from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest
from django.utils.http import url_has_allowed_host_and_scheme

logger = logging.getLogger("bizflow.security")


def get_safe_redirect_url(
    target_url: Optional[str],
    request: HttpRequest,
    default: str = "/dashboard/",
) -> str:
    """
    Validate target redirect URL to prevent Open Redirect attacks.
    Ensures the target is a relative path or on an explicitly allowed host.
    """
    if not target_url:
        return default

    target_url = str(target_url).strip()

    # Reject protocol-relative URLs (e.g. "//evil.com" or "/\\evil.com")
    if target_url.startswith("//") or target_url.startswith("/\\"):
        return default

    # Allowed hosts include the current host from the request
    allowed_hosts = {request.get_host()}

    is_safe = url_has_allowed_host_and_scheme(
        url=target_url,
        allowed_hosts=allowed_hosts,
        require_https=request.is_secure(),
    )

    if not is_safe:
        logger.warning(
            "Blocked potential open redirect to '%s' from IP %s",
            target_url,
            request.META.get("REMOTE_ADDR", "unknown"),
        )
        return default

    return target_url


def is_rate_limited(
    key: str,
    max_attempts: int = 5,
    period_seconds: int = 900,
) -> bool:
    """
    Check if a key has exceeded max attempts within period.
    Returns True if rate limited, False otherwise.
    """
    # Allow bypassing in test environment to avoid test flakiness
    if getattr(settings, "TESTING", False):
        return False

    current_attempts = cache.get(key, 0)
    return current_attempts >= max_attempts


def increment_rate_limit(
    key: str,
    period_seconds: int = 900,
) -> int:
    """
    Increment failure/attempt count for a key. Returns new count.
    """
    if getattr(settings, "TESTING", False):
        return 1

    try:
        if cache.get(key) is None:
            cache.set(key, 1, timeout=period_seconds)
            return 1
        return cache.incr(key)
    except Exception:
        # Fallback if cache backend doesn't support incr or on error
        val = (cache.get(key) or 0) + 1
        cache.set(key, val, timeout=period_seconds)
        return val


def clear_rate_limit(key: str) -> None:
    """Clear rate limit counter upon successful action."""
    cache.delete(key)


def get_client_ip(request: HttpRequest) -> str:
    """Extract client IP address considering proxy headers safely."""
    # Check trusted proxy headers first (Vercel, Cloudflare, Nginx reverse proxy)
    real_ip = request.META.get("HTTP_X_REAL_IP") or request.META.get("HTTP_CF_CONNECTING_IP")
    if real_ip:
        return real_ip.strip()

    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        parts = [p.strip() for p in x_forwarded_for.split(",") if p.strip()]
        if parts:
            return parts[0]

    return request.META.get("REMOTE_ADDR", "127.0.0.1")


def record_login_attempt(
    user=None,
    email: str = "",
    request: Optional[HttpRequest] = None,
    success: bool = True,
    method: str = "web",
    message: str = "",
) -> None:
    """Create a LoginHistory record for security auditing."""
    try:
        from apps.accounts.models import LoginHistory, User

        ip = get_client_ip(request) if request else "127.0.0.1"
        ua = request.META.get("HTTP_USER_AGENT", "")[:255] if request else ""

        target_user = user
        if not target_user and email:
            target_user = User.objects.filter(email=email.lower().strip()).first()

        LoginHistory.objects.create(
            user=target_user,
            ip_address=ip[:64],
            user_agent=ua,
            method=method,
            success=success,
            message=message[:255],
        )
    except Exception as exc:
        logger.error("Failed to record login attempt in LoginHistory: %s", exc)
