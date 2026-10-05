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
