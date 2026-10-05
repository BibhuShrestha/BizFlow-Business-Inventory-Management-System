# Code Style and Standards Guide

> **Coding Standards for BizFlow (Django + FastAPI Migration)**  
> Adherence to these standards ensures consistency, maintainability, and clean architecture across the entire codebase.

---

## 1. Python Standards & Tooling

1. **Language Version**: Python 3.12+
2. **Formatting & Linting**:
   - **Black**: Default code formatter (line length: 100 characters).
   - **Flake8**: Style guide enforcement (`flake8 --max-line-length=100 --extend-ignore=E203,W503`).
   - **isort**: Import ordering (Black compatible profile).
3. **Encoding & Line Endings**:
   - All text files must use **UTF-8 without BOM**.
   - LF line endings are preferred; Windows CRLF will be normalized by Git.

---

## 2. Naming Conventions

| Entity | Convention | Example |
|---|---|---|
| Modules / Files | `snake_case.py` | `sale_service.py`, `password_validator.py` |
| Packages / Folders | `snake_case` | `django_app`, `domain_services` |
| Classes | `PascalCase` | `SalesInvoice`, `StockService`, `UserResponse` |
| Functions & Methods | `snake_case()` | `calculate_invoice_total()`, `verify_token()` |
| Variables | `snake_case` | `unit_price`, `active_company_id` |
| Constants | `UPPER_SNAKE_CASE` | `DEFAULT_PAGE_SIZE = 25`, `JWT_ALGORITHM = "HS256"` |
| Boolean Flags | `is_`, `has_`, `can_` | `is_active`, `has_stock`, `can_delete` |
| Pydantic Schemas | `PascalCase` + Suffix | `ProductCreate`, `ProductResponse`, `InvoiceFilter` |
| Django Models | `PascalCase` (singular) | `Product`, `Customer`, `SaleInvoice` |

---

## 3. Type Annotations

1. Use modern Python 3.10+ union and generic syntax:
   - Use `str | None` instead of `Optional[str]`.
   - Use `list[str]`, `dict[str, Any]` instead of `List[str]`, `Dict[str, Any]`.
2. All domain service methods and API endpoints must include parameter and return type hints:
   ```python
   def deduct_stock(
       company_id: int,
       product_id: int,
       quantity: Decimal,
       reference: str | None = None
   ) -> StockAdjustmentResult:
       ...
   ```

---

## 4. Import Ordering

Organize imports into four distinct blocks separated by single blank lines:

```python
# 1. Standard library imports
import os
import sys
from decimal import Decimal
from pathlib import Path

# 2. Third-party library imports
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

# 3. Django framework imports
from django.db import transaction
from django.shortcuts import get_object_or_404

# 4. Local application imports
from core.exceptions import InsufficientStockError
from domain.services.stock_service import StockService
from apps.inventory.models import Product
```

---

## 5. Django Coding Standards

### 5.1 Model Design
1. Every model must define an explicit string representation (`__str__`).
2. Order model attributes consistently:
   - Foreign keys & OneToOne relationships
   - Database fields (char, text, integer, decimal)
   - Boolean flags
   - Date & timestamp tracking (`created_at`, `updated_at`)
   - `objects = Manager()` (custom managers)
   - Inner `class Meta:`
   - Public methods and properties
3. Multi-tenant models must always reference the Company model:
   ```python
   class Product(models.Model):
       company = models.ForeignKey(
           "companies.Company",
           on_delete=models.CASCADE,
           related_name="products",
           db_index=True,
       )
       name = models.CharField(max_length=200)
       sku = models.CharField(max_length=100, blank=True)
       selling_price = models.DecimalField(max_digits=12, decimal_places=2)
       created_at = models.DateTimeField(auto_now_add=True)
       updated_at = models.DateTimeField(auto_now=True)

       class Meta:
           ordering = ["name"]
           unique_together = ("company", "sku")

       def __str__(self) -> str:
           return self.name
   ```

### 5.2 Views and URL Routing
1. Keep views thin: extract calculations and transaction orchestration to domain services.
2. View function naming should clearly reflect action: `sale_list`, `sale_create`, `sale_detail`.
3. Protect views with `@login_required` and company verification middleware.

---

## 6. FastAPI Coding Standards

1. Use routers organized by resource in `backend/api/routers/`.
2. Request validation must be performed exclusively with Pydantic schemas.
3. Use dependency injection for authentication and database sessions:
   ```python
   @router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
   def create_product(
       payload: ProductCreate,
       current_user: User = Depends(get_current_active_user),
   ):
       """Create a new inventory product for the user's active company."""
       ...
   ```
4. Map domain exceptions to standard HTTP error responses:
   - `NotFoundError` -> `404 Not Found`
   - `ValidationError` -> `422 Unprocessable Entity`
   - `InsufficientStockError` -> `409 Conflict`
   - `PermissionDeniedError` -> `403 Forbidden`

---

## 7. Domain Services Standards

1. Framework-agnostic: Never import `HttpRequest` or `FastAPI` inside domain services.
2. Decimal Precision: Always use Python's `Decimal` type for monetary amounts and stock quantities to prevent floating-point inaccuracies.
3. Transactions: Encapsulate compound state changes in `transaction.atomic()` blocks.

---

## 8. Template & Frontend Standards

1. **HTML Structure**:
   - Use valid HTML5 with semantic landmarks (`<header>`, `<nav>`, `<main>`, `<footer>`, `<section>`).
   - Indent templates using 2 spaces.
2. **Template Tags**:
   - Always load static assets with `{% static 'path/to/asset' %}`.
   - Use descriptive block names in base templates (`{% block title %}`, `{% block content %}`).
3. **CSS Class Naming**:
   - Use meaningful utility classes and design tokens (`biz-card`, `biz-table`, `btn-primary-biz`).
   - Do not write inline CSS styles (`style="..."`).

---

## 9. Error Handling & Logging

1. Use standard Python `logging`:
   ```python
   import logging
   logger = logging.getLogger(__name__)

   logger.info("Invoice created: %s for company: %s", invoice.invoice_number, company_id)
   logger.warning("Low stock threshold breached for product ID: %s", product_id)
   logger.error("Failed to process payment for invoice: %s", invoice_id, exc_info=True)
   ```
2. Never print debug logs to stdout using `print()` in production code.