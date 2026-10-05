"""
Shared application exceptions.

These are framework-agnostic exceptions raised by domain services and repositories,
and handled uniformly by Django views and FastAPI exception handlers.
"""


class AppError(Exception):
    """Base class for all BizFlow application-level errors."""

    def __init__(self, message: str, code: str = "error"):
        self.message = message
        self.code = code
        super().__init__(message)


BizFlowError = AppError  # Alias for domain semantics


class NotFoundError(AppError):
    """Raised when a requested resource does not exist."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, code="not_found")


class PermissionDeniedError(AppError):
    """Raised when the current user lacks permission for an action."""

    def __init__(self, message: str = "Permission denied"):
        super().__init__(message, code="permission_denied")


PermissionDenied = PermissionDeniedError  # Alias


class ValidationError(AppError):
    """Raised when input data fails business-rule validation."""

    def __init__(self, message: str, field: str | None = None):
        self.field = field
        super().__init__(message, code="validation_error")


class AuthenticationError(AppError):
    """Raised when authentication credentials are invalid or missing."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, code="authentication_error")


class ConflictError(AppError):
    """Raised when an operation conflicts with current state (e.g. duplicate)."""

    def __init__(self, message: str = "Resource conflict"):
        super().__init__(message, code="conflict")


class InsufficientStockError(AppError):
    """Raised when a sale requests more stock than is available."""

    def __init__(self, product_name: str, available: int, requested: int):
        message = (
            f"Insufficient stock for '{product_name}'. "
            f"Available: {available}, Requested: {requested}."
        )
        super().__init__(message, code="insufficient_stock")
        self.product_name = product_name
        self.available = available
        self.requested = requested


class DuplicateSKUError(ConflictError):
    """Raised when a product SKU is already in use."""

    def __init__(self, sku: str):
        super().__init__(f"Product with SKU '{sku}' already exists.")
        self.sku = sku


class DuplicateEmailError(ConflictError):
    """Raised when an email address is already registered."""

    def __init__(self, email: str):
        super().__init__(f"Email address '{email}' is already registered.")
        self.email = email


class TokenExpiredError(ValidationError):
    """Raised when an email verification or reset token has expired."""

    def __init__(self, message: str = "Token has expired"):
        super().__init__(message)


class TokenInvalidError(ValidationError):
    """Raised when a verification or reset token is invalid or already used."""

    def __init__(self, message: str = "Token is invalid or already used"):
        super().__init__(message)