# Testing Strategy

## Overview

Tests are written at three levels: unit, integration, and API. The goal is high confidence in business-critical workflows without redundant test coverage.

---

## Test Stack

| Tool | Purpose |
|------|---------|
| pytest | Test runner |
| pytest-django | Django integration |
| factory_boy | Test data factories |
| httpx | API client for FastAPI tests |
| coverage | Coverage reporting |

---

## Test Directory Structure

```
tests/
├── conftest.py           # Shared fixtures
├── factories.py          # Test data factories
├── unit/
│   ├── test_auth_service.py
│   ├── test_sale_service.py
│   ├── test_stock_service.py
│   ├── test_purchase_service.py
│   ├── test_report_service.py
│   └── test_nepali_date.py
├── integration/
│   ├── test_auth_flow.py
│   ├── test_sale_flow.py
│   ├── test_purchase_flow.py
│   └── test_inventory_flow.py
└── api/
    ├── test_auth_api.py
    ├── test_products_api.py
    ├── test_sales_api.py
    └── test_permissions_api.py
```

---

## Unit Tests

Test individual service methods in isolation.

### AuthService Tests

```python
def test_authenticate_valid_credentials(db, user_factory):
    user = user_factory(is_active=True)
    result = AuthService.authenticate(email=user.email, password="testpass123!")
    assert result == user

def test_authenticate_inactive_user_rejected(db, user_factory):
    user = user_factory(is_active=False)
    result = AuthService.authenticate(email=user.email, password="testpass123!")
    assert result is None

def test_register_creates_user_with_staff_role(db, role_factory):
    staff_role = role_factory(name="staff")
    user = AuthService.register(name="Test User", email="test@test.com", password="Pass1234!")
    assert user.role.name == "staff"
    assert user.is_active is False
    assert user.email_verified is False
```

### SaleService Tests

```python
def test_create_sale_deducts_stock(db, product_factory, customer_factory):
    product = product_factory(current_stock=10)
    sale = SaleService.create({
        "product_id": product.id,
        "quantity": 3,
        ...
    }, user=...)
    product.refresh_from_db()
    assert product.current_stock == 7

def test_create_sale_fails_if_insufficient_stock(db, product_factory):
    product = product_factory(current_stock=2)
    with pytest.raises(InsufficientStockError):
        SaleService.create({"quantity": 5, ...}, user=...)

def test_delete_sale_restores_stock(db, sale_factory):
    sale = sale_factory()
    original_stock = sale.items.first().product.current_stock
    SaleService.delete(sale.id, user=...)
    sale.items.first().product.refresh_from_db()
    assert sale.items.first().product.current_stock == original_stock + sale.items.first().quantity
```

### StockService Tests

```python
def test_adjust_stock_in(db, product_factory):
    product = product_factory(current_stock=5)
    StockService.adjust(product.id, qty=3, movement_type="IN", description="Test")
    product.refresh_from_db()
    assert product.current_stock == 8

def test_adjust_stock_out_fails_if_insufficient(db, product_factory):
    product = product_factory(current_stock=2)
    with pytest.raises(InsufficientStockError):
        StockService.adjust(product.id, qty=5, movement_type="OUT", description="Test")
```

---

## Integration Tests

Test complete workflows end-to-end through Django views.

### Auth Flow

```python
def test_login_redirects_to_dashboard(client, active_user):
    response = client.post("/auth/login/", {
        "email": active_user.email,
        "password": "testpass123!",
    })
    assert response.status_code == 302
    assert response["Location"] == "/dashboard/"

def test_login_inactive_user_shows_error(client, inactive_user):
    response = client.post("/auth/login/", {
        "email": inactive_user.email,
        "password": "testpass123!",
    })
    assert response.status_code == 200
    assert "Invalid email or password" in response.content.decode()
```

### Sale Flow

```python
def test_create_sale_redirects_to_detail(staff_client, product, customer):
    response = staff_client.post("/sales/new/", {...})
    assert response.status_code == 302

def test_manager_required_for_delete(staff_client, sale):
    response = staff_client.post(f"/sales/{sale.id}/delete/")
    assert response.status_code == 403
```

---

## API Tests

Test FastAPI endpoints with httpx.

```python
def test_login_returns_tokens(api_client):
    response = api_client.post("/api/v1/auth/login", json={
        "email": "test@test.com",
        "password": "Pass1234!",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]

def test_list_products_requires_auth(api_client):
    response = api_client.get("/api/v1/products/")
    assert response.status_code == 401

def test_list_products_with_valid_token(authenticated_api_client):
    response = authenticated_api_client.get("/api/v1/products/")
    assert response.status_code == 200
    assert response.json()["success"] is True
```

---

## Critical Workflows to Test

| Workflow | Priority |
|----------|----------|
| Registration + Email Verification | High |
| Login + Logout | High |
| Password Reset | High |
| Create Sale + Stock Deduction | High |
| Delete Sale + Stock Restore | High |
| Create Purchase + Stock Increase | High |
| Delete Purchase + Stock Decrease | High |
| Manual Stock Adjustment | Medium |
| Product Import (CSV) | Medium |
| CSV/Excel Export | Medium |
| Role Permission Enforcement | High |
| API Auth (JWT) | High |
| API Validation (400 errors) | Medium |
| Create Credit Given + Stock Decrement | High |
| Create Credit Taken + Stock Increment | High |
| Multi-Product Line Calculations & Taxes | High |
| Partial / Multiple Payment Settlement | High |
| Overpayment Prevention Validation | High |
| Dynamic Status (Unpaid/Partial/Paid/Overdue) | High |
| Running Balance Party Ledgers (Customer/Supplier) | High |
| Credit Dashboard KPIs & Dues Reports | Medium |
| REST API Credit Endpoints (/api/v1/credit) | High |

---

## Udhaar / Credit Automated Test Suite (`tests/test_credit_management.py`)

A comprehensive suite of 19 automated tests validates the entire Udhaar / Credit feature lifecycle:
1. `test_credit_given_decrements_stock_and_creates_sale`: Validates customer credit, due date, items, and inventory decrement.
2. `test_credit_taken_increments_stock_and_creates_purchase`: Validates supplier credit, due date, items, and inventory intake.
3. `test_credit_payment_flow_and_overpayment_prevention`: Verifies partial payments, balance reduction, status transitions, and rejection of overpayment.
4. `test_payment_does_not_affect_inventory`: Invariant check that payments never mutate product stock.
5. `test_customer_ledger_running_balance`: Verifies chronological debits, credits, and running balance math.
6. `test_supplier_ledger_running_balance`: Verifies vendor credit bill and payment debit running balance.
7. `test_credit_summary_calculations`: Verifies aggregate KPIs across given, received, taken, paid, and dues.
8. `test_credit_dashboard_view`: Tests Django web UI dashboard HTTP 200 response and KPI context.
9. `test_credit_given_and_taken_list_views`: Tests filtering, search, and list views.
10. `test_credit_create_views_post`: Tests Django web UI form submissions for credit given and taken.
11. `test_add_payment_web_view`: Tests payment addition modal/form processing.
12. `test_dues_and_overdue_views`: Tests customer dues, supplier dues, and overdue list views.
13. `test_ledger_views`: Tests customer and supplier ledger statement views.
14. `test_reports_views`: Tests reports hub and CSV export responses.
15. `test_customer_and_supplier_detail_integration`: Tests credit summaries and "View Ledger" button on profile views.
16. `test_fastapi_credit_summary`: Tests `/api/v1/credit/summary` REST API endpoint.
17. `test_fastapi_credit_given_and_taken`: Tests `/api/v1/credit/given` and `/credit/taken` endpoints.
18. `test_fastapi_payment_settlement`: Tests `/api/v1/credit/payments` settlement endpoint.
19. `test_fastapi_ledgers`: Tests `/api/v1/credit/ledger/customer/{id}` and `/credit/ledger/supplier/{id}` endpoints.

---

## Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=backend --cov-report=html

# Only unit tests
pytest tests/unit/

# Only API tests
pytest tests/api/

# Specific test file
pytest tests/unit/test_sale_service.py -v

# Specific test
pytest tests/unit/test_sale_service.py::test_create_sale_deducts_stock -v
```

---

## Test Configuration

```ini
# pytest.ini or pyproject.toml [tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = config.settings.testing
addopts = -v --tb=short
testpaths = tests
```

---

## Fixtures (conftest.py)

```python
@pytest.fixture
def staff_client(client, staff_user):
    client.force_login(staff_user)
    return client

@pytest.fixture
def authenticated_api_client(api_client, staff_user):
    token = AuthService.create_access_token(staff_user)
    api_client.headers["Authorization"] = f"Bearer {token}"
    return api_client
```
