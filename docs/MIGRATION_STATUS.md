# MIGRATION STATUS — Flask ➔ Django + FastAPI

> **Project:** Business Inventory Management System (BizFlow)  
> **Source:** `e:/project/business` (Flask 2.3.3 — Untouched, Read-Only)  
> **Target:** `e:/project/business_new/` (Django 6.0 + FastAPI REST API)  
> **Last Updated:** Part 22 — Business Analytics & AI Decision Support Suite Completed

---

## Analytics Explorer Enhancement (2026-10-09)

- Added selectable sales, purchases, expenses, profitability, inventory, receivables, and payables views to the analytics dashboard.
- Added numeric summaries alongside charts, with period-aware transaction series and current-state inventory and balance snapshots.
- Extended the analytics API response with transaction counts and daily, weekly, or monthly trend points.

## Status Key

| Symbol | Meaning |
|---|---|
| `[ ]` | Not Started |
| `[~]` | In Progress |
| `[x]` | Complete |
| `[!]` | Needs Review / Decision Required |

---

## Part Progress

| Part | Description | Status |
|---|---|---|
| Part 1 | Inspect & Analyze Flask Project | `[x]` Complete |
| Part 2 | Create the New Project Scaffold (Django + FastAPI) | `[x]` Complete |
| Part 3 | Create Architectural Documentation Suite | `[x]` Complete |
| Part 4 | Architecture & API-First Foundation | `[x]` Complete |
| Part 5 | Database & Migration Foundation (20+ Models) | `[x]` Complete |
| Part 6 | Shared Business Logic (Services, Repositories, Validators) | `[x]` Complete |
| Part 7 | Authentication & Authorization (Web, API, Desktop, Mobile) | `[x]` Complete |
| Part 8 | Django Web Application & Views | `[x]` Complete |
| Part 9 | Companies & Sellers Module | `[x]` Complete |
| Part 10 | UI/UX & Design System (Minimal Blue/White) | `[x]` Complete |
| Part 11 | SEO Engineering & Public Web Optimization | `[x]` Complete |
| Part 12 | Files, Background Tasks, Integrations & AI | `[x]` Complete |
| Part 13 | Testing & Verification Suite | `[x]` Complete (87 passing tests) |
| Part 14 | Performance, Logging, Accessibility & Hardening | `[x]` Complete (100 passing tests) |
| Part 15 | Systemized Documentation & Change Management System | `[x]` Complete (138 passing tests) |
| Part 16 | Final Verification & Migration Sign-off | `[x]` Complete |
| Part 17 | Business Alerts, Reminders, Cheque Management, SMS & Import/Export | `[x]` Complete (153 passing tests) |
| Part 18 | Inline Quick-Add Modals, Entity Resolvers & Form State Persistence | `[x]` Complete (166 passing tests) |
| Part 19 | Double-Entry Accounting Indicators & Party Ledger Portal Suite | `[x]` Complete (170 passing tests) |
| Part 20 | Minimal UI/UX, Performance & Resource Optimization | `[x]` Complete (170 passing / test suite optimized) |
| Part 21 | Transaction Date Controls, Universal Date Filtering & Hardening | `[x]` Complete (170 passing tests) |
| Part 22 | AI Business Analytics & Decision Support Suite | `[x]` Complete (182 passing tests) |
| Part 23 | Admin User Visibility, Activity Tracking & Advanced Analytics Suite | `[x]` Complete (194 passing tests) |
| Part 24 | Google OAuth2 Social Authentication & Granular RBAC Permissions | `[x]` Complete (216 passing tests) |

---

## Systemized Documentation & Change Management Implementation Summary

### 1. Central Living Documentation Architecture (`docs/`)
- Created central documentation portal and navigation hub at `docs/README.md`.
- Implemented comprehensive `CHANGELOG.md` adhering to Keep a Changelog and Semantic Versioning (`v1.5.0`).
- Implemented structured change management protocol, 12-point impact checklist, and Change Request registry in `docs/CHANGE_MANAGEMENT.md`.
- Implemented complete End-to-End Requirements Traceability Matrix in `docs/TRACEABILITY_MATRIX.md` mapping requirements (`REQ-*`) to code, database, API, UI, tests, and documentation.

### 2. 16-Pillar Feature Documentation Standards (`docs/features/`)
- Standardized comprehensive feature documentation covering all 16 required sections:
  1. `inventory.md` — Product SKU, categorization, stock movements, valuation, low-stock alerts.
  2. `sales.md` — POS checkout, tax/discounting, receipts, atomic stock decrements.
  3. `purchases.md` — Vendor bills, supplier profiles, procurement inward stock.
  4. `payments.md` — Voucher settlement ledger, Cash/Bank/QR/Cheque, zero inventory mutation.
  5. `receivables-payables.md` — Udhaar credit sales/purchases, customer/supplier dues, overdue debt, party ledgers.
  6. `cheque-management.md` — Cheque lifecycle (Pending, Cleared, Bounced) and dynamic 7/3/2/1/0-day reminders.
  7. `notifications.md` — Comprehensive alert matrix across stock, financial dues, cheque schedules, and multi-channel delivery.
  8. `sms.md` — SMS gateway architecture, phone normalization, overdue debtor templates, rate limiting.
  9. `import-export.md` — CSV (UTF-8 BOM), styled Excel (.xlsx via OpenPyXL), 10MB upload guard, `ExportLog`.

### 3. Visual Architectural Diagram Suite (`docs/diagrams/`)
- Mermaid Entity-Relationship Diagram (`er-diagram.md`).
- Mermaid Context Level 0 and Process Level 1 Data Flow Diagrams (`dfd.md`).
- Mermaid Role-Based Use Case Diagrams across Cashier, Manager, Admin, and Seller (`use-case.md`).
- Mermaid Domain Services and Model Class Diagram (`class-diagram.md`).
- Mermaid POS Sales & Stock Decrement Activity Diagram (`activity-diagram.md`).
- Mermaid Udhaar Credit Sale & Partial Settlement Sequence Diagram (`sequence-diagram.md`).

### 4. Modular Subsystem Documentation
- Architecture: `docs/architecture/overview.md`, `modules.md`, `integrations.md`.
- Database: `docs/database/schema.md`, `relationships.md`, `migrations.md`.
- API: `docs/api/endpoints.md`, `authentication.md`.
- UI & Design System: `docs/ui/design-system.md`.
- Security: `docs/security/security.md`.
- Testing: `docs/testing/testing-strategy.md`, `test-cases.md`.

## Receivables & Payables Management Implementation Summary

### 1. Unified Relational Models & Zero Duplication
- Enhanced `apps.sales.models.Sale` and `apps.purchases.models.Purchase` with indexed `due_date`.
- Added dynamic financial properties: `subtotal`, `paid_amount`, `remaining_amount`, `is_overdue`, and `calculated_status` (`Unpaid`, `Partially Paid`, `Paid`, `Overdue`).
- Enhanced `apps.sales.models.Payment` with `notes` and `created_by` (FK to `User`).
- Created and applied non-destructive migrations: `sales.0002` and `purchases.0002`.

### 2. Framework-Agnostic Domain Service (`CreditService`)
- Pure Python domain service `backend/domain/services/credit_service.py`:
  - `create_credit_given`: Decrements inventory stock atomically, validates stock availability, creates Sale invoice.
  - `create_credit_taken`: Increments inventory stock atomically, creates Purchase bill.
  - `add_payment`: Incremental partial/full settlement, prevents overpayments, **never alters inventory stock**.
  - `get_credit_summary`: System-wide aggregate KPIs (given, received, customer dues, taken, supplier paid, supplier dues).
  - `get_customer_ledger` & `get_supplier_ledger`: Real-time chronological debit, credit, and running balance calculation.
  - `get_customers_dues` & `get_suppliers_dues`: Summarized outstanding balances per party.
  - Structured immutable `AuditLog` integration for all operations.

### 3. Dedicated Django Web UI (`apps/credit/`)
- Complete responsive views and navigation:
  - Dashboard (`/credit/`): KPIs, quick action cards, recent transactions.
  - Credit Given (`/credit/give/`, `/credit/given/`, `/credit/given/<id>/`).
  - Credit Taken (`/credit/take/`, `/credit/taken/`, `/credit/taken/<id>/`).
  - Payment Vouchers & History (`/credit/payments/`, `/credit/payments/add/`).
  - Outstanding Dues (`/credit/customers-dues/`, `/credit/suppliers-dues/`, `/credit/overdue/`).
  - Party Ledgers (`/credit/ledger/`, `/credit/ledger/customer/<id>/`, `/credit/ledger/supplier/<id>/`).
  - Reports & CSV Export Hub (`/credit/reports/`, `/credit/reports/export/csv/`).
- Full integration into Main Dashboard (`/dashboard/`), Customer Profile (`/sales/customers/<id>/`), Supplier Profile (`/purchases/suppliers/<id>/`), and base navigation sidebar.

### 4. FastAPI REST API Layer (`/api/v1/credit/`)
- Mounted routers with Pydantic request/response schemas:
  - `GET /api/v1/credit/summary`
  - `GET /api/v1/credit/given`, `POST /api/v1/credit/given`, `GET /api/v1/credit/given/{id}`
  - `GET /api/v1/credit/taken`, `POST /api/v1/credit/taken`, `GET /api/v1/credit/taken/{id}`
  - `POST /api/v1/credit/payments`
  - `GET /api/v1/credit/customers-dues`, `GET /api/v1/credit/suppliers-dues`, `GET /api/v1/credit/overdue`
  - `GET /api/v1/credit/ledger/customer/{id}`, `GET /api/v1/credit/ledger/supplier/{id}`

### 5. Automated Test Suite
- Comprehensive suite `tests/test_credit_management.py` with 19 tests.
- Entire repository test suite passes with **138 tests green (100% pass rate)**.

## Part 14 Implementation Summary: Performance, Logging, Accessibility & Hardening

### 1. Performance Optimization (14.1)
- **Response Timing Middleware**:
  - Implemented `apps.core_app.middleware.PerformanceTimingMiddleware`.
  - Attaches `X-Response-Time` latency header to all HTTP responses.
  - Automatically logs a performance warning for slow queries/requests taking longer than 500ms.
- **Database Query Tuning**:
  - Applied `select_related("category", "company", "seller")` to product listings and CSV/Excel exports.
  - Applied `select_related("customer", "company")` and `prefetch_related("items__product")` to sales and purchase invoices, eliminating N+1 database queries.
  - Standardized pagination with `paginate_queryset` across all listing tables (`per_page=15` or `20`).
- **Caching**:
  - Configured `CACHES['default']` with `LocMemCache` (ready for Redis in multi-instance production).

### 2. Structured Logging & Sensitive Data Redaction (14.2)
- **SensitiveDataFilter**:
  - Implemented `apps.core_app.logging_filters.SensitiveDataFilter`.
  - Integrated into root and console log handlers in `config/settings/base.py`.
  - Automatically redacts passwords, tokens, API secrets, and authorization Bearer headers before log persistence or terminal output.

### 3. Error Handling & Stack Trace Protection (14.3)
- Custom error handlers mounted in `config/urls.py`:
  - `handler404 = "apps.core_app.views.error_404"`
  - `handler500 = "apps.core_app.views.error_500"`
  - `handler403 = "apps.core_app.views.error_403"`
  - `handler400 = "apps.core_app.views.error_400"`
- Semantic error templates created in `templates/errors/` (`404.html`, `500.html`, `403.html`, `400.html`).
- Never exposes internal stack traces, database schema, or server filepaths to end users.

### 4. Security & Hardening (14.4 & 14.5)
- **Cookie Security**:
  - `SESSION_COOKIE_HTTPONLY = True`
  - `CSRF_COOKIE_HTTPONLY = True`
  - `SESSION_COOKIE_SAMESITE = "Lax"`
  - `CSRF_COOKIE_SAMESITE = "Lax"`
- **Security Headers**:
  - `X_FRAME_OPTIONS = "DENY"` (clickjacking protection).
  - `SECURE_CONTENT_TYPE_NOSNIFF = True` (MIME-sniffing prevention).
- **File Upload Hardening**:
  - Implemented 10MB file size limit in `parse_uploaded_file`.
  - Filename sanitization via `os.path.basename` and regex cleaning.
  - Strict extension whitelisting (`.csv`, `.xlsx`, `.xls`).
- **Secret Hygiene**:
  - Verified `.env.example` contains safe mock placeholders.
  - No secrets committed to source control.
  - Updated `docs/SECURITY.md` with full technical security documentation.
- **Zero Threat Clutter**:
  - All security controls are enforced internally; no user-facing alarmist threat pages.

### 5. Accessibility (14.6)
- Semantic HTML elements (`<main>`, `<nav>`, `<article>`, `<header>`, `<footer>`).
- Universal `:focus-visible` focus rings for keyboard navigation.
- High-contrast WCAG 2.1 AA compliant color pairing (slate-900 typography on pure white/neutral slate background).
- Clear accessible error messages with navigation back to safety.

### 6. Automated Verification
- `tests/test_performance_and_security.py`: 13 passing tests.
- Total test suite: 100 passing tests (100% pass rate).
- Original Flask project integrity verified (100% untouched).

---

## Part 20 — Minimal UI/UX, Performance & Resource Optimization Summary

### 1. Database & ORM Optimization
- **N+1 Query Elimination**: Updated `Sale` and `Purchase` property calculation methods (`paid_amount`, `subtotal`) to inspect `_prefetched_objects_cache` before firing secondary database queries.
- **Overdue Computation**: Rewrote `CreditService.get_credit_summary` to execute a single-pass scan with payment relation prefetching and `.exclude(payment_status=Sale.STATUS_PAID)`.
- **Date Boundary Scoping**: Updated `NotificationService.check_payment_due_reminders` and `check_cheque_reminders` to restrict SQL queries to upcoming 7-day ranges rather than scanning all open records across history.
- **Lazy Pagination**: Refactored `credit_given_list` and `credit_taken_list` to avoid in-memory list conversion when dynamic status filtering is not requested.

### 2. Multi-Tenancy Scoping & Isolation
- Enforced active company filtering across `dashboard`, `expense_list`, `customer_list`, `supplier_list`, `credit_given_list`, and `credit_taken_list`.
- Extended `StockService` (`low_stock_products`, `critical_stock_products`, `out_of_stock_products`) to support optional `company_id` parameter.

### 3. Frontend & Asset Optimization
- Removed render-blocking `@import` font call from `main.css`.
- Configured parallel preconnect and `<link rel="stylesheet">` tags in `base.html` with `display=swap` to reduce layout shift and network latency.

### 4. Bug Fixes & Usability
- Fixed `context_processors.py` broken import (`apps.dashboard.models.Notification` -> `apps.audit.models.Notification`), eliminating swallowed exceptions on every request and restoring unread notification badges.
- Fixed 404 links on dashboard (`/transactions/sales/` and `/transactions/purchases/` -> `{% url 'sales:list' %}` and `{% url 'purchases:list' %}`).
- Fixed KPI card key names on dashboard template to render live metrics.
- Fixed `NepaliDateService.format_nepali_date` to convert Gregorian date to Bikram Sambat date before formatting.
- Added 60-second in-memory cache throttle to `NotificationService.run_all_monitors` on dashboard load.

---

## Part 21 — Transaction Date Controls, Universal Date Filtering & Hardening

### 1. Granular Transaction & Due Date Controls
- **Purchase Inward Bills**: Added user-configurable `purchase_date` (defaults to today) and `due_date` to `PurchaseForm` and UI templates. Persisted atomically in `purchase_create`.
- **Sales Invoices**: Added user-configurable `sale_date` (defaults to today) and `due_date` to `SaleForm` and UI templates. Persisted atomically in `sale_create`.
- **Timezone Awareness**: Handled timezone offsets and time-preservation cleanly on all date submissions, preventing naive datetime warnings.

### 2. Universal Date Range & Multi-Parameter List Filtering
- **Sales Invoices (`/sales/`)**: Added `date_from`, `date_to`, and `status` query filters.
- **Purchase Bills (`/purchases/`)**: Added `date_from`, `date_to`, and `status` query filters.
- **Operating Expenses (`/expenses/`)**: Added `date_from`, `date_to`, category dropdown, and query parameter alignment between views and templates.
- **Receivables / Credit Given (`/credit/given/`)**: Added `date_from` and `date_to` range filters alongside status and customer selectors.
- **Payables / Credit Taken (`/credit/taken/`)**: Added `date_from` and `date_to` range filters alongside status and supplier selectors.

### 3. Interactive BS / AD Date Switcher & Dual Date Badges
- Implemented client-side `date_switcher.js` providing real-time bidirectional toggle between Gregorian (AD) and Bikram Sambat (BS) with synchronized persistence.
- Added dual AD and BS date badges across Sales Invoices, Purchase Bills, Operating Expenses, Receivables, and Payables list tables.
- Enhanced `/api/v1/dashboard/convert-date` and `/dashboard/convert-date/` with full Bikram Sambat month names (`Baisakh` - `Chaitra`) and formatted output strings (`formatted_bs_full`).

- Complete test suite passes at 100% (170 passing tests).

---

## Part 22 — Business Analytics & AI Decision Support Suite Summary

### 1. Multi-Tenant Aggregated Business Intelligence (`AnalyticsService`)
- Pure Python, framework-agnostic domain service at `backend/domain/services/analytics_service.py`.
- Computes single-pass multi-tenant operational KPIs across configurable lookback windows (7, 30, 90, 365 days):
  - Revenue, Purchases (Cost of Goods), Operating Expenses, Gross Profit, Net Profit, Gross Margin %, Net Margin %.
  - Period-over-period growth velocity and Average Order Value (AOV).
  - Inventory velocity: Top 5 fast-moving items vs stagnant / dead-capital stock (in-stock items with zero sales).
  - Operating expenses categorized by volume with percentage share.
  - Trade receivables, payables, net working capital, and upcoming 7-day cheque maturities.
  - Deterministic Business Health Score (0 - 100) and qualitative grade (Excellent, Healthy, Attention Needed, Critical Risk).

### 2. Hybrid AI & Deterministic Decision Support (`integrations/ai_analytics.py`)
- **LocalDeterministicAdvisor**:
  - Instantaneous, zero-cost, zero-latency rule engine calculating strategic priority directives.
  - Diagnoses out-of-stock liabilities, overdue receivables, negative working capital, and expense outliers.
- **AIAnalyticsService**:
  - Lightweight hybrid integration utilizing Google Gemini / OpenAI compatible models.
  - Sends compact, anonymized financial telemetry (< 350 tokens) with zero raw customer names or transaction logs.
  - Employs bounded 1-hour cache key hashing and 15 request/hour per-user rate limit controls.
  - Gracefully falls back to `LocalDeterministicAdvisor` upon missing API keys, network errors, or rate exhaustion.

### 3. FastAPI REST API Layer (`/api/v1/analytics/`)
- Mounted routers in `backend/api/routers/analytics.py` and registered in `backend/api/main.py`:
  - `GET /api/v1/analytics/summary`: Scoped business analytics and AI insights with Pydantic response validation (`BusinessAnalyticsResponse`).
  - `POST /api/v1/analytics/insights/refresh`: Triggers on-demand AI recommendations refresh with rate-limiting guardrails.

### 4. Dedicated Django Web UI (`/reports/analytics/`)
- High-aesthetic dashboard adhering strictly to `DESIGN_SYSTEM.md`:
  - Period selection pills (7d, 30d, 90d, 1y) with instant query persistence.
  - Executive AI Decision Support hero card with Health Score gauge, qualitative grade, Cashflow Outlook, Growth Opportunities, and Priority Action Plan.
  - Responsive pure CSS/HTML daily sales velocity sparkline/bar chart (zero external JS dependencies).
  - Fast-moving vs Dead Capital stock comparison tables.
  - Operating expenses distribution with visual meter bars.
  - Dedicated "Refresh AI Advisor" form action with user flash messages.
- Navigation integration:
  - Added "AI Analytics & Insights" link in base navigation sidebar.
  - Added prominent promo callout banner in Reports index (`/reports/`).
  - Added AI Analytics quick-launch action button in Main Dashboard header (`/dashboard/`).

### 5. Test Suite Verification
- Added automated test suite `tests/test_analytics_and_ai.py` with 12 comprehensive tests.
- Entire repository test suite passes with **182 tests green (100% pass rate)**.

---

## Part 23 — Admin User Visibility, Activity Tracking & Advanced Analytics Suite Summary

### 1. Admin User Management & Immediate Visibility
- **Table Data Synchronization**: Fixed context variable alignment between `user_views.py` and `user_list.html` (`page_obj` / `users`), ensuring newly created users immediately appear in the user list.
- **Search, Filtering & Pagination**: Implemented real-time multi-field search (username, name, email), role dropdown filtering, status filtering, and paginated table navigation.
- **Form Error Transparency**: Upgraded `UserCreateForm` and `user_form.html` to render prominent field-level validation feedback for duplicate emails and password strength violations.
- **Role Permission Alignment**: Updated `User.is_staff_member` property to treat cashier alongside staff, manager, and admin.

### 2. User Activity Tracking & Presence Monitoring
- **Lightweight Presence Middleware**: Implemented `UserActivityMiddleware` recording `last_activity` timestamps with a 60-second in-session write throttle to minimize database I/O.
- **Presence Status Properties**: Added `User.is_online`, `User.online_status_label`, and `User.account_status_label` with configurable `USER_ONLINE_TIMEOUT_MINUTES`.
- **Visual Presence Indicators**: Added pulsating green status dots for online users, neutral badges for offline users, and status toggle buttons.
- **Dashboard & User KPIs**: Added top-level metric counters: Total Users, Online Now, Offline Users, Active Accounts, and Disabled Accounts.

### 3. Advanced Business Analytics Suite & Strict Financial Distinction
- **Authoritative Accounting Principles**: Strictly decoupled earned Sales Revenue from actual Cash Received (customer settlement vouchers); classified outstanding receivables separately from liquid cash.
- **COGS & Cash Flow Precision**: Computed exact Cost of Goods Sold from product purchase costs, Gross/Net Margins, and Net Cash Flow (`Cash In - Cash Out`).
- **Intelligent Stock Reorder Intelligence**: Added automated low-stock reorder suggestions with estimated working capital requirements.
- **Extended Timeframe Horizons**: Added period presets (Today, Yesterday, This Week, This Month, This Quarter, This Year, Previous Year) and custom date range pickers.
- **Export & Reporting Hub**: Added CSV export endpoint at `/reports/analytics/export/csv/` and print-ready stylesheet for one-click PDF generation.

### 4. Test Suite Verification
- Added comprehensive test suite `tests/test_user_management_and_analytics.py` with 12 tests.
- Entire repository test suite passes with **194 tests green (100% pass rate)**.

---

## Part 24 — Google OAuth2 Social Authentication & Granular RBAC Permissions Summary

### 1. Google OAuth 2.0 OpenID Connect Integration
- **Framework-Agnostic OAuth Client (`integrations/google_oauth.py`)**:
  - Implemented `GoogleOAuthClient` with PKCE authorization URL generation, state token CSRF validation, authorization code token exchange, and UserInfo profile retrieval.
  - Built-in graceful development & testing mock mode with explicit credentials guard.
- **Shared Business Logic (`AuthService.login_or_register_via_google`)**:
  - Automatically reconciles Google accounts by `google_id` or verified email address.
  - Provisions new user accounts with default `staff` role, active company assignment, `is_active=True`, `email_verified=True`, and unusable password hashing.
  - Strictly rejects unverified Google email addresses and inactive accounts with clear `AuthenticationError` exceptions.
- **Django Web UI Views & Templates**:
  - Added `/auth/google/` (`google_login_view`) generating cryptographically secure random `state` tokens stored in user session.
  - Added `/auth/google/callback/` (`google_callback_view`) with strict CSRF state validation, audit attempt logging, user session login, and flash notifications.
  - Integrated branded "Sign in with Google" and "Sign up with Google" action buttons with SVG icons in `login.html` and `register.html`.
- **FastAPI REST API Layer**:
  - Added `GET /api/v1/auth/google` generating OpenID Connect authorization URLs and state tokens.
  - Added `POST /api/v1/auth/google/callback` exchanging code for JWT access & refresh tokens with Pydantic request/response validation.

### 2. Centralized Granular RBAC Permission Engine (`domain/permissions.py`)
- **Canonical Permission Identifiers (`Permission` Enum)**:
  - Defined 25+ granular permissions spanning Dashboard, User Management, Companies, Sellers, Inventory Master, Sales POS, Procurement Purchases, Expenses, Receivables & Payables (Credit Dues, Cheques, Payments), Reports, Analytics, and Import/Export.
- **Role Permission Mapping (`ROLE_PERMISSION_MAP`)**:
  - Mapped specific permission boundaries for `cashier`, `staff`, `manager`, and `customer`.
  - Admin/Owner possesses unrestricted permissions across all system domains.
- **Framework-Agnostic Utilities**:
  - `has_permission(user, permission)`: Validates individual permission for user.
  - `has_any_permission(user, *permissions)`: Validates possession of at least one permission.
  - `get_all_user_permissions(user)`: Retrieves complete set of permission keys.
- **Integration with Django & FastAPI**:
  - `permission_required_custom` decorator and `PermissionRequiredMixin` CBV mixin in `apps.accounts.permissions`.
  - `require_permission` and `require_any_permission` FastAPI dependencies in `backend/api/deps.py`.
  - `active_company` Django context processor injecting `user_permissions` into all templates.

### 3. Test Suite Verification
- Added comprehensive test suite `tests/test_google_oauth_and_rbac.py` with 22 tests.
- Entire repository test suite passes with **216 tests green (100% pass rate)**.

