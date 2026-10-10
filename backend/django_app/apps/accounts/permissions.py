"""
Role-based access control permissions for Django views.
Provides function decorators and Class-Based View mixins.
Migrated from Flask's app/utils/decorators.py.
"""
from functools import wraps
import logging
from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect

from domain.permissions import (
    Permission,
    has_permission,
    has_any_permission,
    get_all_user_permissions,
)

logger = logging.getLogger(__name__)


def _get_dashboard_url() -> str:
    try:
        from django.urls import reverse
        return reverse("dashboard:index")
    except Exception:
        return "/dashboard/"


def login_required_custom(func):
    """Redirect unauthenticated users to the login page with next parameter."""
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"/auth/login/?next={request.path}")
        return func(request, *args, **kwargs)
    return wrapper


def roles_required(*allowed_roles: str):
    """
    Decorator to enforce role-based access control.
    Owner/Admin always has access to all features.

    Usage:
        @roles_required('admin', 'manager')
        def my_view(request):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(f"/auth/login/?next={request.path}")

            # Admin / Owner has unrestricted access
            if getattr(request.user, "is_admin", False):
                return func(request, *args, **kwargs)

            user_role = getattr(request.user, "role_name", "customer").lower()
            normalized_allowed = [r.lower() for r in allowed_roles]

            if user_role not in normalized_allowed:
                messages.error(request, "Access Restricted: You do not have permission for this action.")
                return redirect(_get_dashboard_url())

            return func(request, *args, **kwargs)
        return wrapper
    return decorator


def admin_required(func):
    """Restricted to Owner / Admin only."""
    return roles_required("admin", "owner")(func)


def manager_required(func):
    """Accessible by Admin, Owner, and Manager."""
    return roles_required("admin", "owner", "manager")(func)


def staff_required(func):
    """Accessible by Admin, Owner, Manager, Staff, and Cashier."""
    return roles_required("admin", "owner", "manager", "staff", "cashier")(func)


def permission_required_custom(permission: str | Permission):
    """
    Decorator enforcing granular permission on Django view functions.
    Admin/Owner always possesses all permissions.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(f"/auth/login/?next={request.path}")

            if not has_permission(request.user, permission):
                messages.error(request, "Access Restricted: Insufficient privileges for this operation.")
                return redirect(_get_dashboard_url())

            return func(request, *args, **kwargs)
        return wrapper
    return decorator


def any_permission_required_custom(*permissions: str | Permission):
    """
    Decorator verifying user possesses at least one of the specified permissions.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(f"/auth/login/?next={request.path}")

            if not has_any_permission(request.user, *permissions):
                messages.error(request, "Access Restricted: Insufficient privileges for this operation.")
                return redirect(_get_dashboard_url())

            return func(request, *args, **kwargs)
        return wrapper
    return decorator


# ---------------------------------------------------------------------------
# Class-Based View Mixins
# ---------------------------------------------------------------------------

class RoleRequiredMixin(AccessMixin):
    """CBV mixin verifying the user has one of the allowed roles."""

    allowed_roles: tuple[str, ...] = ()

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if getattr(request.user, "is_admin", False):
            return super().dispatch(request, *args, **kwargs)

        user_role = getattr(request.user, "role_name", "customer").lower()
        normalized = [r.lower() for r in self.allowed_roles]

        if user_role not in normalized:
            messages.error(request, "Access Restricted: You do not have permission for this action.")
            return redirect(_get_dashboard_url())

        return super().dispatch(request, *args, **kwargs)


class AdminRequiredMixin(RoleRequiredMixin):
    allowed_roles = ("admin", "owner")


class ManagerRequiredMixin(RoleRequiredMixin):
    allowed_roles = ("admin", "owner", "manager")


class StaffRequiredMixin(RoleRequiredMixin):
    allowed_roles = ("admin", "owner", "manager", "staff", "cashier")


class PermissionRequiredMixin(AccessMixin):
    """CBV mixin verifying the user has the required granular permission."""

    permission_required: str | Permission | tuple[str | Permission, ...] | None = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if self.permission_required:
            if isinstance(self.permission_required, (list, tuple, set)):
                has_access = any(has_permission(request.user, p) for p in self.permission_required)
            else:
                has_access = has_permission(request.user, self.permission_required)

            if not has_access:
                messages.error(request, "Access Restricted: Insufficient privileges for this operation.")
                return redirect(_get_dashboard_url())

        return super().dispatch(request, *args, **kwargs)
