"""
Centralized Role-Based Access Control (RBAC) and Permission System for BizFlow.
Provides framework-agnostic permission definitions, role mappings, and checker utilities.
"""
from enum import StrEnum
from typing import Any, Iterable


class Permission(StrEnum):
    """Canonical permission identifiers across the BizFlow system."""

    # Dashboard & General
    DASHBOARD_VIEW = "dashboard.view"
    NOTIFICATIONS_VIEW = "notifications.view"

    # User & Account Management
    USERS_VIEW = "users.view"
    USERS_MANAGE = "users.manage"

    # Company & Seller Setup
    COMPANIES_VIEW = "companies.view"
    COMPANIES_MANAGE = "companies.manage"
    COMPANIES_DELETE = "companies.delete"
    SELLERS_VIEW = "sellers.view"
    SELLERS_MANAGE = "sellers.manage"

    # Product & Inventory Master
    INVENTORY_VIEW = "inventory.view"
    INVENTORY_MANAGE = "inventory.manage"
    INVENTORY_ADJUST = "inventory.adjust"
    INVENTORY_DELETE = "inventory.delete"
    STOCK_MOVEMENTS_VIEW = "stock_movements.view"

    # Sales & Invoicing (POS)
    SALES_VIEW = "sales.view"
    SALES_CREATE = "sales.create"
    SALES_DELETE = "sales.delete"
    CUSTOMERS_VIEW = "customers.view"
    CUSTOMERS_MANAGE = "customers.manage"

    # Purchases & Procurement
    PURCHASES_VIEW = "purchases.view"
    PURCHASES_CREATE = "purchases.create"
    PURCHASES_DELETE = "purchases.delete"
    SUPPLIERS_VIEW = "suppliers.view"
    SUPPLIERS_MANAGE = "suppliers.manage"

    # Expenses & Accounting
    EXPENSES_VIEW = "expenses.view"
    EXPENSES_MANAGE = "expenses.manage"
    EXPENSES_DELETE = "expenses.delete"

    # Receivables & Payables (Credit Management)
    CREDIT_RECEIVABLES_VIEW = "credit.receivables_view"
    CREDIT_RECEIVABLES_MANAGE = "credit.receivables_manage"
    CREDIT_PAYABLES_VIEW = "credit.payables_view"
    CREDIT_PAYABLES_MANAGE = "credit.payables_manage"
    CREDIT_CHEQUES_VIEW = "credit.cheques_view"
    CREDIT_CHEQUES_MANAGE = "credit.cheques_manage"
    CREDIT_PAYMENTS_VIEW = "credit.payments_view"
    CREDIT_PAYMENTS_MANAGE = "credit.payments_manage"
    CREDIT_PAYMENTS_DELETE = "credit.payments_delete"

    # Reports, Financial Daybook & AI Analytics
    REPORTS_VIEW = "reports.view"
    ANALYTICS_VIEW = "analytics.view"

    # Central Import & Export Hub
    IMPORT_EXPORT_VIEW = "import_export.view"
    IMPORT_EXPORT_MANAGE = "import_export.manage"


# ---------------------------------------------------------------------------
# Role Permissions Mapping Matrix
# ---------------------------------------------------------------------------

# Operational cashier permissions (Counter sales, customer records, receiving customer credit)
CASHIER_PERMISSIONS: frozenset[str] = frozenset({
    Permission.DASHBOARD_VIEW,
    Permission.NOTIFICATIONS_VIEW,
    Permission.INVENTORY_VIEW,
    Permission.SALES_VIEW,
    Permission.SALES_CREATE,
    Permission.CUSTOMERS_VIEW,
    Permission.CUSTOMERS_MANAGE,
    Permission.CREDIT_RECEIVABLES_VIEW,
    Permission.CREDIT_RECEIVABLES_MANAGE,
    Permission.CREDIT_PAYMENTS_VIEW,
})

# Operational staff permissions (Cashier duties + inventory catalog, inward purchases, basic expenses)
STAFF_PERMISSIONS: frozenset[str] = frozenset(
    set(CASHIER_PERMISSIONS) | {
        Permission.INVENTORY_MANAGE,
        Permission.STOCK_MOVEMENTS_VIEW,
        Permission.PURCHASES_VIEW,
        Permission.PURCHASES_CREATE,
        Permission.SUPPLIERS_VIEW,
        Permission.EXPENSES_VIEW,
        Permission.EXPENSES_MANAGE,
    }
)

# Manager permissions (Full operational control except user administration and company deletion)
MANAGER_PERMISSIONS: frozenset[str] = frozenset(
    set(STAFF_PERMISSIONS) | {
        Permission.COMPANIES_VIEW,
        Permission.SELLERS_VIEW,
        Permission.SELLERS_MANAGE,
        Permission.INVENTORY_ADJUST,
        Permission.INVENTORY_DELETE,
        Permission.SALES_DELETE,
        Permission.PURCHASES_DELETE,
        Permission.SUPPLIERS_MANAGE,
        Permission.EXPENSES_DELETE,
        Permission.CREDIT_PAYABLES_VIEW,
        Permission.CREDIT_PAYABLES_MANAGE,
        Permission.CREDIT_CHEQUES_VIEW,
        Permission.CREDIT_CHEQUES_MANAGE,
        Permission.CREDIT_PAYMENTS_MANAGE,
        Permission.CREDIT_PAYMENTS_DELETE,
        Permission.REPORTS_VIEW,
        Permission.ANALYTICS_VIEW,
        Permission.IMPORT_EXPORT_VIEW,
        Permission.IMPORT_EXPORT_MANAGE,
    }
)

# Customer permissions (Public catalog & personal account)
CUSTOMER_PERMISSIONS: frozenset[str] = frozenset({
    Permission.INVENTORY_VIEW,
})

ROLE_PERMISSION_MAP: dict[str, frozenset[str]] = {
    "cashier": CASHIER_PERMISSIONS,
    "staff": STAFF_PERMISSIONS,
    "manager": MANAGER_PERMISSIONS,
    "customer": CUSTOMER_PERMISSIONS,
}


def get_user_role_name(user: Any) -> str:
    """Safely resolve normalized lower-case role name from a user object."""
    if not user or not getattr(user, "is_authenticated", False):
        return "anonymous"
    if getattr(user, "is_superuser", False):
        return "admin"
    if hasattr(user, "role_name"):
        return str(user.role_name).lower()
    role_obj = getattr(user, "role", None)
    if role_obj and hasattr(role_obj, "name"):
        return str(role_obj.name).lower()
    return "customer"


def has_permission(user: Any, permission: str | Permission) -> bool:
    """
    Check if the user has a specific granular permission.
    Admin/Owner always possesses all permissions.
    """
    if not user or not getattr(user, "is_authenticated", False):
        return False

    # Owner / Superuser / Admin has unrestricted permission
    if getattr(user, "is_admin", False) or getattr(user, "is_superuser", False):
        return True

    role_name = get_user_role_name(user)
    if role_name in ("admin", "owner"):
        return True

    allowed_perms = ROLE_PERMISSION_MAP.get(role_name, frozenset())
    perm_val = str(permission.value if isinstance(permission, Permission) else permission)
    return perm_val in allowed_perms


def has_any_permission(user: Any, *permissions: str | Permission) -> bool:
    """Return True if user possesses at least one of the given permissions."""
    return any(has_permission(user, p) for p in permissions)


def get_all_user_permissions(user: Any) -> frozenset[str]:
    """Retrieve all permission string keys granted to the specified user."""
    if not user or not getattr(user, "is_authenticated", False):
        return frozenset()
    if getattr(user, "is_admin", False) or getattr(user, "is_superuser", False):
        return frozenset({p.value for p in Permission})
    role_name = get_user_role_name(user)
    if role_name in ("admin", "owner"):
        return frozenset({p.value for p in Permission})
    return ROLE_PERMISSION_MAP.get(role_name, frozenset())
