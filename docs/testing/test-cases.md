# Automated Test Cases Catalog

> **BizFlow Test Case Matrix**  
> *Catalog of 138+ automated test cases covering Domain Services, Web UI, FastAPI, and Security.*

---

## 1. Domain Logic & Business Rules (`test_shared_business_logic.py`)
- `TC-DOM-001`: `test_create_sale_decrements_stock` — Asserts stock decrements atomically upon invoice creation.
- `TC-DOM-002`: `test_insufficient_stock_raises_error` — Asserts `InsufficientStockError` is raised when stock is zero or insufficient.
- `TC-DOM-003`: `test_create_purchase_increments_stock` — Asserts vendor bill increments stock count.
- `TC-DOM-004`: `test_calculate_invoice_totals` — Asserts subtotal, tax, and discount math matches specification.
- `TC-DOM-005`: `test_stock_valuation` — Asserts `Product.stock_value` returns $\text{quantity} \times \text{cost}$.

---

## 2. Authentication, RBAC & Tokens (`test_auth_and_permissions.py`)
- `TC-AUTH-001`: `test_user_registration` — Validates email uniqueness and password complexity.
- `TC-AUTH-002`: `test_user_login_success` — Asserts session creation and redirect to dashboard.
- `TC-AUTH-003`: `test_api_jwt_issuance` — Asserts access and refresh token generation.
- `TC-AUTH-004`: `test_token_revocation_on_logout` — Asserts revoked tokens are rejected.
- `TC-AUTH-005`: `test_cashier_restricted_from_admin` — Asserts cashiers receive HTTP 403 when accessing manager/admin routes.

---

## 3. Udhaar / Credit Management (`test_credit_management.py`)
- `TC-CRED-001`: `test_create_credit_given` — Asserts sale with `due_date` creates receivable and decrements stock.
- `TC-CRED-002`: `test_create_credit_taken` — Asserts purchase with `due_date` creates payable and increments stock.
- `TC-CRED-003`: `test_partial_payment_sale` — Asserts payment voucher decreases remaining balance and leaves stock untouched.
- `TC-CRED-004`: `test_prevent_overpayment` — Asserts payment $> \text{remaining\_amount}$ is rejected with validation error.
- `TC-CRED-005`: `test_customer_ledger_running_balance` — Asserts chronological debits, credits, and running balance calculation.
- `TC-CRED-006`: `test_supplier_ledger_running_balance` — Asserts chronological credits, debits, and running balance calculation.
- `TC-CRED-007`: `test_get_customers_dues` — Asserts outstanding dues summary per customer.
- `TC-CRED-008`: `test_overdue_detection` — Asserts unpaid invoices past `due_date` are flagged as Overdue.
- `TC-CRED-009`: `test_credit_summary_kpis` — Asserts aggregate credit given, taken, customer dues, and supplier dues.

---

## 4. Performance, Export & Security (`test_performance_and_security.py`)
- `TC-SEC-001`: `test_response_timing_header` — Asserts `X-Response-Time` header present on HTTP responses.
- `TC-SEC-002`: `test_csv_export_utf8_bom` — Asserts CSV exports begin with UTF-8 BOM `\ufeff`.
- `TC-SEC-003`: `test_excel_export_styling` — Asserts OpenPyXL headers styled with Dark Slate `#1E293B`.
- `TC-SEC-004`: `test_upload_parser_file_size_limit` — Asserts files $> 10\text{MB}$ are rejected immediately.
- `TC-SEC-005`: `test_sensitive_data_logging_filter` — Asserts passwords and tokens are redacted from application logs.
