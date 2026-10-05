"""Re-export role-based access decorators for backward compatibility."""
from apps.accounts.permissions import (
    login_required_custom,
    roles_required,
    admin_required,
    manager_required,
    staff_required,
)

__all__ = [
    "login_required_custom",
    "roles_required",
    "admin_required",
    "manager_required",
    "staff_required",
]
