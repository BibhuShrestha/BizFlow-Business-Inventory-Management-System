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
        if record.args:
            if isinstance(record.args, dict):
                sanitized_args = {}
                for k, v in record.args.items():
                    if any(sens in str(k).lower() for sens in ["password", "token", "secret", "auth", "credential"]):
                        sanitized_args[k] = "[REDACTED]"
                    elif isinstance(v, str):
                        val_str = v
                        for pattern, repl in SENSITIVE_PATTERNS:
                            val_str = pattern.sub(repl, val_str)
                        sanitized_args[k] = val_str
                    else:
                        sanitized_args[k] = v
                record.args = sanitized_args
            elif isinstance(record.args, (list, tuple)):
                sanitized_list = []
                for item in record.args:
                    if isinstance(item, str):
                        item_str = item
                        for pattern, repl in SENSITIVE_PATTERNS:
                            item_str = pattern.sub(repl, item_str)
                        sanitized_list.append(item_str)
                    elif isinstance(item, dict):
                        sub_dict = {}
                        for k, v in item.items():
                            if any(sens in str(k).lower() for sens in ["password", "token", "secret", "auth", "credential"]):
                                sub_dict[k] = "[REDACTED]"
                            else:
                                sub_dict[k] = v
                        sanitized_list.append(sub_dict)
                    else:
                        sanitized_list.append(item)
                record.args = tuple(sanitized_list) if isinstance(record.args, tuple) else sanitized_list
        return True
