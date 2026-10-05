# Testing Strategy & Quality Assurance

> **BizFlow Verification Framework**  
> *Test Pyramid, In-Memory SQLite Isolation, Pytest Configuration, and CI Execution.*

---

## 1. Testing Philosophy

1. **Zero External Test Dependencies**: Tests run completely standalone in-memory via SQLite (`config.settings.testing`) without needing live PostgreSQL or Redis servers.
2. **100% Green Mandate**: No change request or milestone is considered complete unless all automated tests pass (`python -m pytest`).
3. **Preservation of Legacy Integrity**: The original Flask reference repository (`e:/project/business/tests`) must remain 100% untouched.

---

## 2. Test Pyramid & Directory Structure

```text
tests/
├── conftest.py                       # Global fixtures (test users, companies, products, client)
├── unit/                             # Fast isolated unit tests for domain services
├── django/                           # Django SSR views, forms, context processors
├── api/                              # FastAPI endpoints, Pydantic schemas, HTTP status codes
├── integration/                      # Cross-service transactional workflows
├── test_shared_business_logic.py     # Pure Python domain logic tests
├── test_auth_and_permissions.py      # RBAC, login, token refresh and revocation tests
├── test_django_web_application.py    # Complete Django web application tests
├── test_credit_management.py         # Udhaar, receivables, payables, party ledgers tests
└── test_performance_and_security.py # Timing middleware, export engine, sensitive data filter
```

---

## 3. Test Execution Commands

```powershell
# Run the entire test suite
python -m pytest

# Run with verbose output
python -m pytest -v

# Run a specific test module
python -m pytest tests/test_credit_management.py

# Run with test coverage report
python -m pytest --cov=backend tests/
```
