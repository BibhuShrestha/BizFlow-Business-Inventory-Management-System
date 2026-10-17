"""
Performance and Security Middlewares for BizFlow.
Adds request timing headers, security audit logging, and safe error boundary.
"""
import time
import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger("bizflow.performance")


class PerformanceTimingMiddleware(MiddlewareMixin):
    """Adds X-Response-Time header to track request latency and logs slow requests (> 500ms)."""

    def process_request(self, request):
        request._start_time = time.perf_counter()

    def process_response(self, request, response):
        if hasattr(request, "_start_time"):
            duration_ms = (time.perf_counter() - request._start_time) * 1000
            response["X-Response-Time"] = f"{duration_ms:.2f}ms"
            if duration_ms > 500:
                logger.warning(
                    "Slow request: %s %s took %.2fms (status %s)",
                    request.method,
                    request.path,
                    duration_ms,
                    response.status_code,
                )
        return response


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Enforces robust HTTP security headers across all web responses:
    - Content-Security-Policy (CSP)
    - Permissions-Policy
    - Referrer-Policy
    - X-Content-Type-Options
    - X-Frame-Options
    """

    CSP_POLICY = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com data:; "
        "img-src 'self' data: https:; "
        "connect-src 'self' https://*.supabase.co https://accounts.google.com; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "frame-ancestors 'none';"
    )

    def process_response(self, request, response):
        # Only attach CSP if not already present
        if "Content-Security-Policy" not in response:
            response["Content-Security-Policy"] = self.CSP_POLICY

        if "Permissions-Policy" not in response:
            response["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=()"

        if "Referrer-Policy" not in response:
            response["Referrer-Policy"] = "strict-origin-when-cross-origin"

        if "X-Content-Type-Options" not in response:
            response["X-Content-Type-Options"] = "nosniff"

        if "X-Frame-Options" not in response:
            response["X-Frame-Options"] = "DENY"

        return response


import traceback

class ExceptionCaptureMiddleware(MiddlewareMixin):
    """Captures unhandled exceptions and attaches tracebacks to request for diagnostic 500 handler."""

    def process_exception(self, request, exception):
        request._last_exception = exception
        request._last_traceback = traceback.format_exc()
        logger.error(
            "Unhandled exception at %s %s: %s\n%s",
            getattr(request, "method", "GET"),
            getattr(request, "path", "/"),
            exception,
            request._last_traceback,
        )
        return None


