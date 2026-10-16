# MIGRATION STATUS — Flask ➔ Django + FastAPI

> **Project:** Business Inventory Management System (BizFlow)  
> **Source:** `e:/project/business` (Flask 2.3.3 — Untouched, Read-Only)  
> **Target:** `e:/project/business_new/` (Django 6.0 + FastAPI REST API)  
> **Last Updated:** Part 29 — Supabase Database + Supabase Auth + Vercel Deployment Integration Completed (2026-10-16)

---

## Supabase Cloud Database, Supabase Auth & Vercel Deployment Update (2026-10-16)

- **Supabase Cloud Identity Provider**: Integrated GoTrue auth client for password login, cloud user provisioning, and FastAPI JWT token verification.
- **Supabase PostgreSQL & Pooler**: Production settings configured for port 5432 session connections and port 6543 Supavisor transaction pooler with `DISABLE_SERVER_SIDE_CURSORS = True`.
- **Database Backup, Migration & Audit Toolkit**: Model-agnostic MySQL to Supabase PostgreSQL migration (`scripts/migrate_mysql_to_supabase.py`), backup generator, and 4-tier verification suite (`scripts/verify_database_migration.py`).
- **Vercel Serverless Deployment**: Serverless specifications (`vercel.json`) with dual entrypoints (`api/index.py` WSGI, `api/fastapi_entrypoint.py` ASGI) and static asset routing.
- **Automated Verification**: Full test suite passes with **248 passing tests (100% green)**.

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
| Part 24 | Google OAuth2 Social Authentication & Granular RBAC Permissions | `[x]` Complete (221 passing tests) |
| Part 25 | UI/UX Component Standardization, Ergonomics & Design Consistency | `[x]` Complete (221 passing tests) |
| Part 27 | Multi-Tenant Hardening, Company Switching, Scoped User Mgmt & Keyboard Ergonomics | `[x]` Complete (231 passing tests) |
| Part 28 | Supabase PostgreSQL Migration, Production Hardening & Deployment | `[x]` Complete (231 passing tests) |
| Part 29 | Supabase Database + Supabase Auth + Vercel Deployment Integration | `[x]` Complete (248 passing tests) |

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
  - Added interactive local developer OAuth sandbox simulation page (`google_dev_login.html`) to facilitate instantaneous one-click dev testing without requiring live GCP credentials in `DEBUG` mode.
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
  - **Role-Based UI Feature Filtering (`base.html`, `dashboard/index.html`, `inventory/product_list.html`)**:
    - **Customer Role**: Restricted strictly to Customer Portal (`Product Catalog`). Hidden from internal financial dashboard, transactions (sales/purchases/expenses), parties, reports, AI analytics, supplier payables, cheques, import/export, and wholesale buy prices.
    - **Cashier Role**: Restricted to Counter POS duties: sales checkout, product sell prices, customer directory, and customer credit settlement vouchers. Hidden from procurement purchases, vendor payables, expenses, cheques, daybook, and business profit reports.
    - **Staff Role**: Operational duties: sales, purchases, physical stock movements, suppliers, and basic expenses. Hidden from company settings, executive P&L net profit, AI analytics, supplier payables oversight, cheques, and bulk data import/export.
    - **Manager Role**: Unrestricted operational oversight across all business transactions, payables, cheques, and reports, excluding admin user provisioning.
    - **Admin/Owner Role**: Unrestricted full access across all modules, configurations, and user management.

### 3. Test Suite Verification
- Added comprehensive test suite `tests/test_google_oauth_and_rbac.py` with 27 tests.
- Entire repository test suite passes with **221 tests green (100% pass rate)**.

---

## Part 25 — UI/UX Component Standardization, Ergonomics & Design Consistency Summary

### 1. Design System Tokens & Components (`main.css`)
- **Filter Bar & Search Box Pattern (`.filter-bar`, `.search-input-wrap`)**: Unified filter container with inline SVG search icon, consistent input paddings, and flex wrapping across desktop and mobile viewports.
- **Enhanced Empty States (`.empty-state`, `.empty-state-icon-wrap`)**: Styled empty states across all table views providing contextual icons, clear explanations, and primary call-to-action buttons.
- **Skeleton Loaders (`.skeleton`, `@keyframes skeletonShimmer`)**: Standardized shimmer animations for async loading states.
- **Micro-interactions**: Table row hover transitions, active button scaling, and elevated primary button focus states.

### 2. View & Register Standardization
- **Core Registers**: Upgraded Sales Invoices (`sale_list.html`), Purchase Orders (`purchase_list.html`), Products Catalog (`product_list.html`), Customer Directory (`customer_list.html`), Supplier Directory (`supplier_list.html`), Receivables Register (`credit_given_list.html`), Payables Register (`credit_taken_list.html`), Settlement Vouchers (`payment_list.html`), and Cheque Management (`cheques_list.html`).
- **Pagination**: Implemented comprehensive pagination blocks across all list views showing active page numbers, total counts, and preserving active search/filter URL parameters.
- **Cashier Ergonomics**: Added `Ctrl + Enter` / `Cmd + Enter` invoice quick submit listener, real-time Nepali currency formatting, and sticky summary sidebars in Sales (`sale_form.html`) and Purchases (`purchase_form.html`).
- **URL Aliasing**: Added `/inventory/create/` route alias.

### 3. Test Suite Verification
- Verified all 221 tests across backend, API, domain services, security, RBAC, and UI passing with 100% green status.

---

## Part 26 — 5-Star UI/UX Design System Implementation (Figma Make Specification)

### 1. Extracted & Standardized Specifications (`Create Business Inventory Website.make`)
- Extracted design archive containing canvas assets, Figma specifications, UI components, and design system tokens.
- Standardized UI/UX architecture to eliminate generic looks and elevate BizFlow into an executive-grade 5-star inventory platform.

### 2. Core Visual & Layout Enhancements
- **Illuminated Brand Identity**: Added `.brand-mark` with illuminated 3-bar logo badge (`#3B82F6` with glowing blue elevation) and "Business, in motion" subtext.
- **Active Company Switcher**: Added `.company-switcher` elevated card in sidebar displaying 2-letter monogram logo, active company name, and fast switching dropdown.
- **Omnipresent Topbar Controls**: Added keyboard-accelerated global search (`Ctrl+K` / `⌘K`), dual Bikram Sambat (BS) & Gregorian (AD) date pill (`.date-chip`), and interactive notification dropdown center (`.notification-panel`) with priority category badges.
- **Sidebar Ergonomics & Debit/Credit Standardization**: Standardized navigation groups into Workspace, Debit & Credit, Manage, and Admin; updated terminology from colloquial "Udhaar & Credit" to professional "Debit & Credit" as specified; added persistent user account footer (`.sidebar-user`).
- **4 Key Executive KPI Cards**: Added `.metric-card` grid displaying Today's Sales, Customer Receivables (Dr), Vendor Purchases / Payables (Cr), and Net Profit / Inventory Stock Value with dynamic trend badges (`↑` / `↓`).
- **7-Day Sales Overview Bar Chart**: Added responsive, pure CSS bar chart with day labels, revenue summary, and highlighted peak day tooltip.
- **Operational Cash Flow Donut**: Added circular conic-gradient donut chart showing cash inflow vs outflow proportion with net cash flow health indicator.
- **Recent Invoices & Stock Alerts Panels**: Added instant text filtering on recent invoices with customer avatar badges; added low stock alert cards with visual threshold progress tracks.

### 3. Backend View & Context Enrichment
- Enhanced `dashboard.views.index` to compute daily sales trends vs yesterday, 7-day normalized bar chart series, cash inflow/outflow proportions, itemized low-stock thresholds, and dual BS/AD date strings.
- Preserved 100% of RBAC permission guards for Customer, Cashier, Staff, Manager, and Admin roles.
- Design system token compliance verified across all required palette colors, focus outlines, and responsive breakpoints.

---

## Part 27 — Multi-Tenant Hardening, Company Switching, Scoped User Mgmt & Keyboard Ergonomics

### 1. Multi-Tenant Data Isolation Enforcement
- **Strict Queryset Scoping**: Audited and removed administrative bypasses (`and not request.user.is_admin`) in `apps/sales/views.py`, `apps/purchases/views.py`, `apps/inventory/views.py`, and `apps/accounting/views.py`.
- **Zero Cross-Tenant Leakage**: All operational querysets (`Sale.objects.filter(company=company)`, `Purchase.objects.filter(company=company)`, `Product.objects.filter(company=company)`, etc.) are bound strictly to `request.user.active_company`, regardless of user role.
- **Tenant Authorization Guards**: Accessing resources from another company returns an immediate HTTP 404 response.

### 2. Company Directory & Workspace Switching
- **Company Directory Fix**: Resolved empty state ("No companies registered") in `apps/companies/views.py` by providing `companies: page_obj` in the template context and preserving search query state.
- **Route Aliasing**: Added `path("<int:pk>/switch/", views.set_active_company, name="switch")` in `apps/companies/urls.py` ensuring compatibility with both `companies:switch` and `companies:set_active`.
- **Interactive Sidebar Workspace Switcher**: Upgraded `.company-switcher` in `templates/base/base.html` into a click-to-open dropdown powered by the `user_companies` context processor (`apps.core_app.context_processors.active_company`), enabling instant multi-tenant switching with active checkmarks and "Manage All Companies" link.

### 3. Company-Scoped User Management (`/users/`)
- **Active Company Scoping**: Filtered the primary user directory list and executive user KPI cards (`Total Users`, `Active Now`, `Administrators`, `Staff Members`) strictly to `request.user.active_company`.
- **Company Switcher Filter**: Added multi-tenant `<select>` dropdown in `/users/` filter bar with auto-submit (`onchange="this.form.submit()"`) allowing administrators to view users across different company workspaces.
- **User Detail Inspection Modal**: Implemented dynamic modal inspection dialog displaying detailed user profile attributes: Full Name, Email, Active Status, Role Badge, Primary Company, Created Timestamp, and Last Login Timestamp.
- **User Provisioning Context**: Pre-selects active company during user creation.

### 4. Cashier & Global Keyboard Shortcut Ergonomics
- **Central Keyboard Shortcut Manager**: Implemented unobtrusive global shortcut listener in `templates/base/base.html` with intelligent input-field isolation (ignoring keystrokes when editing inputs, textareas, or selects):
  - <kbd>Ctrl</kbd> + <kbd>K</kbd>: Focus global search bar.
  - <kbd>N</kbd>: Jump to New Sale Invoice checkout.
  - <kbd>P</kbd>: Jump to New Purchase Order intake.
  - <kbd>I</kbd>: Jump to Add Product to inventory.
  - <kbd>C</kbd>: Jump to Add Customer modal/page.
  - <kbd>W</kbd>: Toggle interactive Workspace / Company Switcher dropdown.
  - <kbd>D</kbd>: Jump to Main Financial Dashboard.
  - <kbd>?</kbd>: Open Keyboard Shortcuts Cheatsheet Modal.
  - <kbd>Ctrl</kbd> + <kbd>Enter</kbd>: Accelerated form submission across all forms.
  - <kbd>Esc</kbd>: Dismiss active modals, dropdowns, and overlays.
- **Visual Shortcut Badges**: Standardized `<kbd>` design tokens in `backend/django_app/static/css/main.css` and embedded visual badge cues on primary action buttons across views.
- **Keyboard Shortcuts Cheatsheet Modal**: Added accessible `#shortcuts-modal` dialog displaying organized groups (Navigation, Quick Actions, General).

### 5. Automated Test Suite Verification
- Added dedicated test suite `tests/test_multi_tenant_isolation.py` (10 tests) validating:
  - Strict multi-company sale, purchase, product, customer, and supplier isolation.
  - Proper HTTP 404 responses when attempting cross-company detail access.
  - Workspace switching endpoint behavior and session persistence.
- Full test suite passes with **231 tests green, 5 skipped, 0 failures (100% pass rate)**.

---

## Part 28 — Supabase PostgreSQL Migration, Production Hardening & Deployment

### 1. Supabase PostgreSQL & Native Driver Architecture
- **PostgreSQL 14+ / Supabase Database Adapter**: Configured in `backend/django_app/config/settings/base.py` and `production.py` with automatic SSL detection (`sslmode=require`).
- **Direct & Pooler Connection Modes**: Added support for both Direct Session connections (port 5432) and Supavisor/PgBouncer Transaction Poolers (port 6543) with `DISABLE_SERVER_SIDE_CURSORS = True` and tuned `CONN_MAX_AGE`.
- **Database Driver**: Added native `psycopg2-binary>=2.9.10` database driver in `requirements.txt`.

### 2. Database Backup, Migration & Verification Toolkit
- **MySQL Backup Generator (`scripts/backup_mysql.py`)**: Non-destructive, model-agnostic JSON fixture and raw SQL backup generator preserving tenant foreign keys.
- **Migration Pipeline (`scripts/migrate_mysql_to_supabase.py`)**: Automated schema construction, data loading, and automated PostgreSQL primary key sequence alignment (`setval`).
- **4-Tier Verification Suite (`scripts/verify_database_migration.py`)**: Automated audit checking table presence, row counts, PBKDF2/Argon2 password hash compatibility, multi-tenant scoping, and analytics aggregations.

### 3. Production Hardening & Security Audit
- **Deployment Settings**: Configured `production.py` with `DEBUG = False`, `SESSION_COOKIE_SECURE = True`, `CSRF_COOKIE_SECURE = True`, `SECURE_PROXY_SSL_HEADER`, `SECURE_HSTS_SECONDS = 31536000`, `SECURE_SSL_REDIRECT = True`, and structured console logging. Passed `manage.py check --deploy` with 0 issues.
- **WhiteNoise Static File Serving**: Configured WhiteNoise with compressed manifest caching; separated `STATIC_ROOT` (`backend/django_app/staticfiles/`) from `STATICFILES_DIRS`.
- **Container / Cloud Deployment**: Authored standardized `Procfile` and `scripts/run_production.py` for cloud platforms (Render, Railway, Fly.io, VPS).
- **Client-Side XSS Protection**: Hardened `showToast()` and modal error displays in `static/js/quick_add.js` using safe DOM `textContent`.
- **Automated Verification**: Added `tests/test_audit_and_production_readiness.py` covering production settings, pooler URL parsing, and migration toolkit importability.

---

## Part 29 — Supabase Database + Supabase Auth + Vercel Deployment Integration

### 1. Supabase Cloud Auth Integration
- **Lightweight Supabase Auth Client (`backend/integrations/supabase_client.py`)**: Implemented REST client utilizing Supabase GoTrue API for `sign_in_with_password`, `sign_up`, `sign_out`, `verify_jwt`, and `sync_to_django_user`.
- **Database Identity Sync**: Added indexed `supabase_uid` column (`VARCHAR(64)`) to `apps.accounts.models.User` with non-destructive migration `0004_user_supabase_uid.py`.
- **Unified Domain Service**: Upgraded `AuthService.authenticate()` and `AuthService.register()` in `backend/domain/services/auth_service.py` to authenticate against Supabase when configured, sync cloud identity to Django `accounts.User`, and seamlessly fall back to local Django auth when unconfigured.
- **Web Session Integration**: Linked session login and logout in `apps/accounts/views.py` with Supabase session tokens (`supabase_access_token`).

### 2. FastAPI Supabase JWT Verification (`/api/v1/`)
- Enhanced `backend/api/deps.py` (`get_current_token_payload` and `get_current_user`) to support both internal tokens and Supabase JWTs.
- Resolves users by UUID `sub` or `email`, auto-provisions or links accounts, and enforces RBAC permission checks.

### 3. Vercel Serverless Deployment Architecture
- **Deployment Manifest (`vercel.json`)**: Configured routing mapping Django SSR to `api/index.py` (WSGI) and FastAPI REST API to `api/fastapi_entrypoint.py` (ASGI), with `/static/(.*)` routed to edge-cached static assets.
- **Root Serverless Entrypoints (`api/index.py`, `api/fastapi_entrypoint.py`)**: Sys.path isolation ensuring clean imports in AWS Lambda / Vercel runtime.
- **Documentation**: Authored `docs/AUTHENTICATION.md` and expanded `docs/DEPLOYMENT.md` and `.env.example`.

### 4. Comprehensive Test Suite Verification
- Added `tests/test_supabase_auth_and_vercel.py` validating client configuration, credentials exchange, user syncing, Vercel manifest syntax, and WSGI/ASGI entrypoint importability.
- Repository test suite passes with **248 passing tests, 5 skipped, 0 failures (100% pass rate)**.




