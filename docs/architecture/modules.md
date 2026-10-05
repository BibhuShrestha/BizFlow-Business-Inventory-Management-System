# Architectural Modules & Subsystem Catalog

> **BizFlow Module Registry**  
> *Catalog of all 13 Django apps, FastAPI routers, domain services, and core utilities.*

---

## 1. Django Applications (`backend/django_app/apps/`)

| App Name | Primary Responsibilities | Key Models | Key Views / Routes |
|---|---|---|---|
| **`accounts`** | User registration, authentication, RBAC, profiles, token revocation. | `User`, `RevokedToken` | `/accounts/login/`, `/accounts/register/`, `/accounts/profile/` |
| **`companies`** | Multi-tenant company configuration, sellers, store branches. | `Company`, `Seller` | `/companies/`, `/sellers/` |
| **`inventory`** | Product catalog, categories, barcodes, stock movements. | `Category`, `Product`, `StockMovement` | `/inventory/products/`, `/inventory/categories/`, `/inventory/movements/` |
| **`sales`** | POS checkout, customer invoices, payment vouchers, thermal receipt. | `Customer`, `Sale`, `SaleItem`, `Payment` | `/sales/`, `/sales/create/`, `/sales/<id>/`, `/sales/customers/` |
| **`purchases`** | Supplier master, vendor bills, procurement receiving. | `Supplier`, `Purchase`, `PurchaseItem` | `/purchases/`, `/purchases/create/`, `/purchases/suppliers/` |
| **`credit`** | Udhaar receivables, payables, customer/supplier dues, overdue debt. | Relational queries via `CreditService` | `/credit/`, `/credit/give/`, `/credit/take/`, `/credit/ledger/`, `/credit/overdue/` |
| **`accounting`** | Chart of accounts, journal entries, general ledger, operational expenses. | `ExpenseCategory`, `Expense`, `Account`, `JournalEntry` | `/accounting/expenses/`, `/accounting/accounts/` |
| **`dashboard`** | Main KPI overview, quick actions, analytics widgets, notifications bell. | N/A | `/dashboard/`, `/dashboard/notifications/` |
| **`reports`** | Financial daybook, gross profit, sales summary, CSV export hub. | N/A | `/reports/`, `/reports/daybook/`, `/reports/summary/export/csv/` |
| **`audit`** | Security audit trail, user activity log, email history, export logs. | `AuditLog`, `Notification`, `EmailLog`, `ExportLog` | Admin models, notification center |
| **`core_app`** | Middleware (performance timing, multi-tenancy), CSV/Excel export helpers. | N/A | Shared templates, context processors |
| **`parties`** | Legacy bridge for customer/supplier party compatibility. | Reference bridge | Unified in sales and purchases |
| **`transactions`**| Internal cash/bank transfer records and cheque entries. | `Transaction` | `/transactions/` |

---

## 2. FastAPI Routers (`backend/api/routers/`)

| Router | Prefix | Description |
|---|---|---|
| **`health`** | `/api/v1/health` | System health check (database connection, uptime, API status). |
| **`auth`** | `/api/v1/auth` | JWT issuance (`/login`), refresh token rotation (`/refresh`), logout (`/logout`), current user (`/me`). |
| **`credit`** | `/api/v1/credit` | Credit summary, given, taken, payment vouchers, party dues, overdue age analysis, and customer/supplier ledgers. |

---

## 3. Pure Domain Services (`backend/domain/services/`)

| Service | Primary Functions |
|---|---|
| **`CreditService`** | `create_credit_given`, `create_credit_taken`, `add_payment`, `get_credit_summary`, `get_customer_ledger`, `get_supplier_ledger`, `get_customers_dues`, `get_suppliers_dues`. |
| **`SaleService`** | `create_sale`, `calculate_totals`, `validate_stock`, `void_sale`. |
| **`PurchaseService`** | `create_purchase`, `receive_goods`, `calculate_purchase_totals`. |
| **`StockService`** | `record_movement`, `adjust_stock`, `get_low_stock`, `get_stock_valuation`. |
| **`AuthService`** | `authenticate_user`, `issue_tokens`, `refresh_token`, `revoke_token`. |
| **`ReportService`** | `get_dashboard_metrics`, `get_daybook_summary`. |
