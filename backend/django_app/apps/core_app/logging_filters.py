"""Logging filters for security and data privacy."""
import re
import logging

SENSITIVE_PATTERNS = [
    (re.compile(r"(password\s*[:=]\s*['\"]?)([^\'\"\s&]+)", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"(token\s*[:=]\s*['\"]?)([^\'\"\s&]+)", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"(secret\s*[:=]\s*['\"]?)([^\'\"\s&]+)", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"(Bearer\s+)[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"(Authorization\s*[:=]\s*['\"]?)([^\'\"\s]+)", re.IGNORECASE), r"\1[REDACTED]"),
]

class SensitiveDataFilter(logging.Filter):
    """Filter that sanitizes log records by redacting sensitive data patterns."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            for pattern, repl in SENSITIVE_PATTERNS:
                record.msg = pattern.sub(repl, record.msg)
        if record.args and isinstance(record.args, dict):
            sanitized_args = {}
            for k, v in record.args.items():
                if any(sens in str(k).lower() for sens in ["password", "token", "secret", "auth", "credential"]):
                    sanitized_args[k] = "[REDACTED]"
                else:
                    sanitized_args[k] = v
            record.args = sanitized_args
        return True
