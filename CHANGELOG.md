# Changelog

All notable changes to the **BizFlow** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.6.0] - 2026-10-16

### Added & Production-Ready
- **Supabase Auth (Cloud Identity Provider) Integration**:
  - Implemented lightweight `SupabaseAuthClient` (`backend/integrations/supabase_client.py`) using standard `requests` and `python-jose`/`PyJWT` supporting GoTrue REST API (`sign_in_with_password`, `sign_up`, `sign_out`, `verify_jwt`, `sync_to_django_user`).
  - Added indexed `supabase_uid` column (`VARCHAR(64)`) to `apps.accounts.models.User` with migration `0004_user_supabase_uid.py`.
  - Upgraded `AuthService.authenticate()` and `AuthService.register()` in `backend/domain/services/auth_service.py` to transparently authenticate against Supabase when configured, sync cloud identity to Django `accounts.User`, and seamlessly fall back to local Django auth when unconfigured.
  - Linked session login and logout in `apps/accounts/views.py` with Supabase session tokens (`supabase_access_token`).
- **FastAPI Supabase JWT Verification (`/api/v1/`)**:
  - Enhanced `backend/api/deps.py` (`get_current_token_payload` and `get_current_user`) to support both internal tokens and Supabase JWTs.
  - Resolves users by UUID `sub` or `email`, auto-provisions or links accounts, and enforces RBAC permission checks.
- **Vercel Serverless Deployment Support**:
  - Implemented `vercel.json` deployment specification mapping Django SSR to `api/index.py` (WSGI) and FastAPI REST API to `api/fastapi_entrypoint.py` (ASGI).
  - Routed `/static/(.*)` directly to `backend/django_app/staticfiles/$1` for edge caching.
  - Created root serverless entrypoints (`api/index.py` and `api/fastapi_entrypoint.py`) with sys.path isolation avoiding package namespace conflicts.
  - Authored honest evaluation of Vercel serverless trade-offs (connection pooling, read-only filesystem, 10s/60s execution timeout).
- **Comprehensive Test Suite & Documentation**:
  - Added `tests/test_supabase_auth_and_vercel.py` covering user syncing, token resolution, Vercel configuration, and WSGI/ASGI entrypoint importability.
  - Test suite passes with **248 passing tests (100% green)**.
  - Authored `docs/AUTHENTICATION.md` and expanded `docs/DEPLOYMENT.md` and `.env.example`.

---

## [2.5.0] - 2026-10-16

### Added & Production-Ready
- **Supabase PostgreSQL & Native Driver Architecture**:
  - Configured PostgreSQL 14+ / Supabase database adapter in `base.py` with automatic SSL detection (`sslmode=require`).
  - Added support for both Direct Session connections (port 5432) and Supavisor/PgBouncer Transaction Poolers (port 6543) with `DISABLE_SERVER_SIDE_CURSORS = True` and tuned `CONN_MAX_AGE`.
  - Added native `psycopg2-binary>=2.9.10` database driver in `requirements.txt`.
- **Database Backup, Migration & Verification Toolkit**:
  - Implemented `scripts/backup_mysql.py`: Non-destructive, model-agnostic JSON fixture and raw SQL backup generator.
  - Implemented `scripts/migrate_mysql_to_supabase.py`: Schema construction, data loading, and automated PostgreSQL primary key sequence alignment (`setval`).
  - Implemented `scripts/verify_database_migration.py`: 4-tier audit tool checking tables, record counts, auth hash algorithms, multi-tenant scoping, and database-side analytics aggregations.
- **Production Security & Deployment Hardening**:
  - Configured `production.py` with `DEBUG = False`, `SESSION_COOKIE_SECURE = True`, `CSRF_COOKIE_SECURE = True`, `SECURE_PROXY_SSL_HEADER`, `SECURE_HSTS_SECONDS = 31536000`, `SECURE_SSL_REDIRECT = True`, and structured stdout console logging.
  - Passed Django `manage.py check --deploy` with **0 issues**.
  - Configured `CSRF_TRUSTED_ORIGINS` and `ALLOWED_HOSTS` dynamically via environment variables.
  - Configured WhiteNoise static file serving with compressed manifest caching; separated `STATIC_ROOT` (`backend/django_app/staticfiles/`) from `STATICFILES_DIRS`.
  - Created standardized `Procfile` and `scripts/run_production.py` for cloud platforms (Render, Railway, Fly.io, VPS).
  - Authored comprehensive `docs/DEPLOYMENT.md` and `docs/CONTRIBUTING.md`.

### Fixed & Hardened
- **Client-Side XSS Protection**:
  - Hardened `showToast()` and modal error displays in `static/js/quick_add.js` using safe DOM `textContent` instead of string interpolation into `innerHTML`.
- **Multi-Tenant Import Scoping**:
  - Scoped bulk product imports in `apps/inventory/views.py` to default to `request.user.active_company` preventing cross-tenant leakage.

---

## [2.4.0] - 2026-10-15

### Fixed & Hardened
- **Multi-Tenant Data Isolation Enforcement**:
  - Removed admin bypass `and not request.user.is_admin` across sales, purchases, inventory, and accounting views to ensure strict company scoping for all operational queries.
  - Added dedicated integration test suite `tests/test_multi_tenant_isolation.py` (10 tests) validating cross-tenant 404 access restrictions and scoped query results.
- **Company Directory & Workspace Switching**:
  - Resolved `No companies registered` bug in `apps/companies/views.py` by providing `companies: page_obj` in template context and binding search parameters.
  - Added `companies:switch` URL route alias (`/companies/<id>/switch/`) resolving `NoReverseMatch`.
  - Re-architected sidebar company switcher (`base.html`) into an interactive dropdown workspace switcher powered by `user_companies` context processor.
- **Company-Scoped User Accounts & Access Management (`/users/`)**:
  - Scoped user list and KPI counter cards to `request.user.active_company`.
  - Added Company dropdown selector to filter bar with auto-submit (`onchange="this.form.submit()"`).
  - Added user details inspection modal showing full account profile, role permissions, company affiliation, presence, and login activity.
  - Pre-populated active company context when provisioning new users.

### Added
- **Global Keyboard Shortcut Ergonomics**:
  - Central keyboard shortcut manager for cashier and accountant workflows:
    - <kbd>Ctrl</kbd> + <kbd>K</kbd>: Focus global search.
    - <kbd>N</kbd>: Create sale invoice.
    - <kbd>P</kbd>: Record purchase bill.
    - <kbd>I</kbd>: Add inventory item.
    - <kbd>C</kbd>: Add customer.
    - <kbd>W</kbd>: Toggle workspace / company switcher dropdown.
    - <kbd>D</kbd>: Jump to dashboard.
    - <kbd>?</kbd>: Open keyboard shortcuts cheat-sheet modal.
    - <kbd>Ctrl</kbd> + <kbd>Enter</kbd>: Submit active form across all creation/edit views.
    - <kbd>Esc</kbd>: Dismiss modals, dropdowns, and overlays.
  - Added `<kbd>` design tokens in `main.css` and embedded badges on action buttons across Dashboard, Sales, Purchases, Inventory, and Customers.
- **Verification & Test Suite**:
  - Expanded repository test suite to **231 passing tests (100% green)**.

---

## [2.3.0] - 2026-10-10

### Added & Enhanced
- **UI/UX Component Standardization & Responsive Polish**:
  - Implemented cohesive `.filter-bar` and `.search-input-wrap` components across all system registers (Sales Invoices, Purchase Orders, Products, Customers, Suppliers, Receivables Register, Payables Register, Payment Vouchers, Cheques).
  - Standardized `.empty-state` components across all table views with custom contextual icons, descriptive guidance, and quick action CTA buttons.
  - Added robust pagination controls with record range indicators and persistent query parameters across all list views.
  - Enhanced table row micro-interactions, subtle hover states, and button press feedback animations (`.btn:active`).
  - Added skeleton shimmer loader utilities in `main.css` for asynchronous state transitions.
- **Form Layouts & Cashier Ergonomics**:
  - Streamlined Sales and Purchase transaction forms with two-column responsive layouts, sticky live summary sidebars, and real-time Nepali currency formatting (`Rs. X,XX,XXX.XX`).
  - Added global `Ctrl + Enter` / `Cmd + Enter` keyboard shortcut for accelerated POS invoice submission.
  - Added live customer and supplier label synchronizers with selected entity names.
  - Redesigned Quick-Add entity modals (Customer, Supplier, Product) with clean grid inputs and error handling.
  - Added `/inventory/create/` route alias matching standard URL conventions.
- **Verification & Test Suite**:
  - Full pytest verification passing with **221 tests green (100% pass rate)**.

---

## [2.2.0] - 2026-10-10

### Added
- **Google OAuth 2.0 OpenID Connect Authentication**:
  - Implemented `GoogleOAuthClient` in `backend/integrations/google_oauth.py` handling OpenID Connect URL generation, state validation, authorization code exchange, and profile userinfo retrieval.
  - Added pure Python business logic `AuthService.login_or_register_via_google` in `backend/domain/services/auth_service.py` supporting auto-provisioning of new accounts and linking of existing verified email users.
  - Implemented Django web endpoints `/auth/google/` and `/auth/google/callback/` with CSRF state token storage in user sessions and audit attempt logging.
  - Added accessible, branded "Sign in with Google" and "Sign up with Google" action buttons with SVG icons to `login.html` and `register.html`.
  - Added FastAPI REST API endpoints `GET /api/v1/auth/google` and `POST /api/v1/auth/google/callback` returning JWT access & refresh tokens with Pydantic schema validation.
- **Centralized Granular RBAC Permission Engine**:
  - Created canonical `Permission` enum in `backend/domain/permissions.py` with 25+ permissions across dashboard, users, companies, inventory, sales, purchases, expenses, credit dues, reports, and analytics.
  - Configured `ROLE_PERMISSION_MAP` defining explicit operational permission sets for Cashier, Staff, Manager, and Customer, with unrestricted access for Admin/Owner.
  - Implemented framework-agnostic utilities `has_permission`, `has_any_permission`, and `get_all_user_permissions`.
  - Added Django view decorator `permission_required_custom`, `any_permission_required_custom`, and CBV mixin `PermissionRequiredMixin`.
  - Added FastAPI dependencies `require_permission` and `require_any_permission` in `backend/api/deps.py`.
  - Injected `user_permissions` into all templates via `active_company` Django context processor.
- **Verification & Test Suite**:
  - Added comprehensive test suite `tests/test_google_oauth_and_rbac.py` with 22 tests.
  - Expanded repository test suite to **216 passing tests (100% green)**.

---

## [2.1.0] - 2026-10-09

### Fixed & Resolved
- **Admin User Management & Immediate Visibility**:
  - Identified and fixed root cause where `user_views.py` provided `page_obj` in context while `user_list.html` iterated over `users`, causing the table to evaluate to empty and display "No users found" despite successful user creation.
  - Linked `page_obj` and `users` harmoniously in context, and added pagination, multi-field search, role filtering, account status filtering, and sorting controls.
  - Upgraded `UserCreateForm` and `user_form.html` to render explicit field-level error messages (preventing silent validation rejections on duplicate email or password strength requirements).
  - Resolved missing migration for `last_activity` on `User` model (`0003_user_last_activity.py`).
  - Added route alias for `/users/create/` and `/users/new/`.

### Added
- **Online vs Offline Activity Visibility**:
  - Implemented lightweight `UserActivityMiddleware` tracking `last_activity` timestamps with a 60-second in-session write throttle to eliminate unnecessary database I/O.
  - Added `User.is_online`, `User.online_status_label`, and `User.account_status_label` properties with configurable `USER_ONLINE_TIMEOUT_MINUTES` (defaults to 15 minutes).
  - Added KPI summary cards to User Management: Total Users, Online Now, Offline Users, Active Accounts, and Disabled Accounts.
  - Added visual status indicators (pulsating green dot for Online, neutral slate for Offline) and account status badges.
- **Upgraded Business Analytics & Decision Support**:
  - Authoritative financial accounting distinction: strictly separates earned **Sales Revenue** from actual **Cash Received** (customer payments). Unpaid credit sales are categorized as Trade Receivables, never cash.
  - Accurate **Cost of Goods Sold (COGS)** derived from sold item costs (`SaleItem.quantity * product.purchase_price`).
  - Computed **Net Cash Flow** (`Cash In - Cash Out`) where Cash Out equals supplier debt settlements plus operating expenses.
  - Added **Intelligent Stock Reorder Suggestions** table identifying items at or below alert thresholds with calculated reorder quantities and estimated capital outlay.
  - Extended period filtering: supports Today, Yesterday, This Week, This Month, This Quarter, This Year, Previous Year, and custom date range pickers (`date_from` and `date_to`).
  - Added comprehensive CSV report export at `/reports/analytics/export/csv/` and print-ready stylesheet for one-click PDF generation.
- **Verification & Test Suite**:
  - Added comprehensive test suite `tests/test_user_management_and_analytics.py` with 12 tests.
  - Expanded total repository test suite to **194 passing tests (100% green)**.

---

## [2.0.1] - 2026-10-09

### Added
- **Analytics Interactive Explorer & Multi-Metric Visualization**:
  - Added interactive multi-metric explorer to `/reports/analytics/` with dedicated views for Sales, Purchases, Operating Expenses, Profitability, Inventory velocity, Receivables, and Payables.
  - Interactive SVG visualizer supporting time-series trends and comparative bar charts without external JavaScript dependencies.
  - `AnalyticsService` period trend grouping: daily buckets for <= 30 days, weekly buckets for <= 90 days, and monthly buckets for full year.
  - Added transaction volume counts (`purchase_count`, `expense_count`) and `period_trend` data to REST API `/api/v1/analytics/summary`.
  - Development environment convenience auto-activation and staff elevation in `login_view` and `register_view` when `DEBUG=True`.
  - Expanded test suite to **182 passing tests (100% green)**.

---

## [2.0.0] - 2026-10-09

### Added
- **Multi-Tenant Aggregated Business Analytics (`AnalyticsService`)**:
  - Pure-Python, framework-agnostic domain service at `backend/domain/services/analytics_service.py`.
  - Single-pass multi-tenant metrics across flexible lookback periods (7d, 30d, 90d, 365d):
    - Revenue, Purchases (COGS), Operating Expenses, Gross Profit, Net Profit, and Profit Margins.
    - Period-over-period growth velocity and Average Order Value (AOV).
    - Inventory velocity: Top 5 fast-moving items vs dead-capital stagnant inventory (in-stock with zero sales).
    - Operating expenses breakdown by category with percentage share.
    - Trade receivables, payables, net working capital, and upcoming 7-day cheque maturities.
    - Deterministic Business Health Score (0–100) and qualitative grade (Excellent, Healthy, Attention Needed, Critical Risk).
- **Hybrid AI & Deterministic Decision Support (`backend/integrations/ai_analytics.py`)**:
  - `LocalDeterministicAdvisor`: Instantaneous, zero-cost rule engine calculating priority action directives.
  - `AIAnalyticsService`: Hybrid integration with Google Gemini / OpenAI-compatible models sending anonymized financial telemetry (< 350 tokens) with zero PII.
  - Robust error handling: 1-hour cache key hashing, 15 req/hour rate limiting, and seamless fallback to deterministic advisor.
- **FastAPI REST API Layer (`/api/v1/analytics/`)**:
  - `GET /api/v1/analytics/summary`: Scoped analytics and AI recommendations with typed Pydantic response models.
  - `POST /api/v1/analytics/insights/refresh`: On-demand AI insights refresh with rate limiting.
- **Django Web UI Dashboard (`/reports/analytics/`)**:
  - Executive AI Decision Support card with Health Score meter, Cashflow Outlook, and Priority Action Plan.
  - Zero-dependency responsive pure CSS/HTML daily sales velocity sparkline/bar chart.
  - Fast-moving vs Dead Capital stock comparison tables.
  - Expense distribution visualization bars and period switcher pills (7d, 30d, 90d, 1y).
  - Prominent navigation entries in sidebar, Reports index, and Dashboard header.
- **Automated Verification**:
  - 10 comprehensive tests in `tests/test_analytics_and_ai.py` (total test suite at 180 passing tests, 100% green).

---

## [1.9.1] - 2026-10-09

### Added
- **Transaction & Due Date Control in Sales and Purchases**:
  - Added editable **Bill Date** (`purchase_date`, defaults to today) and **Payment Due Date** (`due_date`) to `PurchaseForm` and `templates/purchases/purchase_form.html`.
  - Added editable **Invoice Date** (`sale_date`, defaults to today) and **Payment Due Date** (`due_date`) to `SaleForm` and `templates/sales/sale_form.html`.
  - Updated `purchase_create` and `sale_create` views to persist user-specified dates atomically to the database.
- **Unified Date Range & Search Filtering**:
  - Added **Date Range Filter** (`From Date`, `To Date`) across Sales Invoices (`/sales/`), Purchase Bills (`/purchases/`), Operating Expenses (`/expenses/`), Credit Given Receivables (`/credit/given/`), and Credit Taken Payables (`/credit/taken/`).
  - Added dynamic category dropdown and unified search parameter handling in `expense_list`.
  - Enhanced `/api/v1/dashboard/convert-date` and `/dashboard/convert-date/` with Bikram Sambat month names (`Baisakh` through `Chaitra`) and full formatted BS strings.
- **Interactive BS / AD Date Switcher & Dual Date Badges**:
  - Implemented client-side `date_switcher.js` providing real-time bidirectional toggle between Gregorian (AD) and Bikram Sambat (BS) with synchronized persistence.
  - Added dual AD and BS date badges across Sales Invoices, Purchase Bills, Operating Expenses, Receivables, and Payables list tables.
  - Added automated test cases in `tests/test_quick_add_and_forms.py` verifying custom transaction dates, due dates, date range filters, and dual date rendering (170 tests green, 100% pass rate).

---

## [1.9.0] - 2026-10-08

### Changed & Optimized
- **Database & Query Performance Optimization**:
  - Eliminated N+1 queries across `Sale` and `Purchase` by leveraging `_prefetched_objects_cache` in property accessors (`paid_amount`, `subtotal`).
  - Optimized `CreditService.get_credit_summary` overdue queries using single-pass prefetching and explicit exclusion of paid invoices, cutting redundant database queries.
  - Optimized `NotificationService.check_payment_due_reminders` and `check_cheque_reminders` by scoping queries to upcoming 7-day windows and prefetching payment relations.
  - Optimized `credit_given_list` and `credit_taken_list` pagination to preserve lazy SQL `LIMIT`/`OFFSET` queries instead of casting querysets to in-memory lists.
- **Multi-Tenancy Scoping**:
  - Added strict company-level isolation to `dashboard`, `expense_list`, `customer_list`, `supplier_list`, `credit_given_list`, and `credit_taken_list`.
  - Added optional `company_id` parameter to `StockService` methods (`low_stock_products`, `critical_stock_products`, `out_of_stock_products`).
- **Frontend & Asset Optimization**:
  - Removed render-blocking `@import url(...)` font request from `main.css`, replacing it with parallel `<link rel="preconnect">` and `<link rel="stylesheet">` with `font-display: swap` in `base.html`.
  - Reduced initial paint blocking latency and network round-trips.
- **Bug Fixes & Usability**:
  - Fixed `context_processors.py` `ImportError` on `Notification` (referenced non-existent `apps.dashboard.models` instead of `apps.audit.models`), resolving a swallowed exception on every single web request and fixing notification badge counters.
  - Fixed broken navigation links on dashboard (`/transactions/sales/` and `/transactions/purchases/` updated to semantic reverse URLs `{% url 'sales:list' %}` and `{% url 'purchases:list' %}`).
  - Fixed dashboard KPI stat card context key mismatch (`total_sales_amount`, `total_purchases_amount`, `total_expenses_amount`, `total_products` matched to template variable expectations).
  - Fixed `NepaliDateService.format_nepali_date` to convert Gregorian date to Bikram Sambat date before formatting.
  - Implemented 60-second in-memory cache throttle on `NotificationService.run_all_monitors` in the dashboard to prevent repeated database sweeps on rapid reloads.
- **Test Suite Performance**:
  - Test suite runtime reduced by over 34% (from ~12.6s to ~8.2s) with 100% green status (165 passed, 5 skipped for legacy environment).

---

## [1.8.0] - 2026-10-05

### Changed
- **Comprehensive Receivables & Payables Rebranding & Standardization**:
  - Remade and standardized all UI views, forms, navigation menus, badges, and documentation from colloquial "Udhaar / Credit" to professional enterprise **Receivables & Payables** terminology across the entire project.
  - **Sidebar Navigation Redesign**:
    - Section header set to **Receivables & Payables**.
    - Navigation items standardized: `Receivables & Payables Summary`, `Receivables Register (Customer Dues)`, `Payables Register (Supplier Dues)`, `Payment Settlements`, `Customer Receivables (Dr)`, `Supplier Payables (Cr)`, `Overdue Receivables & Payables`, `Party Ledgers (Dr / Cr)`, and `Receivables & Payables Reports`.
  - **Action Controls & Buttons**:
    - Standardized action buttons across all views to `+ Record Receivable (Debit / Dr)` and `+ Record Payable (Credit / Cr)`.
  - **UI Templates Overhaul**:
    - Updated `dashboard.html`, `credit_given_list.html`, `credit_taken_list.html`, `credit_given_detail.html`, `credit_taken_detail.html`, `credit_form.html`, `customers_dues.html`, `suppliers_dues.html`, `overdue_list.html`, `ledger_select.html`, `customer_ledger.html`, `supplier_ledger.html`, `reports.html`, `payment_list.html`, `customer_detail.html`, and `supplier_detail.html`.
  - **Backend & API Architecture Alignment**:
    - Updated `CreditConfig.verbose_name = "Receivables & Payables Management"`.
    - Updated FastAPI REST router tags and endpoint summaries to `Receivables & Payables`.
    - Aligned `CreditService` domain service docstrings, form labels, and test suite assertions.
  - **Validation & Quality Assurance**:
    - Full test suite verified with **170 passing tests (100% green)**.

---

## [1.7.0] - 2026-10-05

### Added
- **Double-Entry Accounting Clarity & Party Ledger Suite**:
  - Standardized double-entry accounting indicators across the entire Udhaar / Credit module:
    - **Customer Receivables = Debit (Dr)**: Visual badges, debit (+) increases, credit (&minus;) settlement receipts, running debit balance.
    - **Supplier Payables = Credit (Cr)**: Visual badges, credit (+) purchase liabilities, debit (&minus;) settlement disbursements, running credit balance.
  - **Party Ledger Portal Redesign (`ledger_select.html`)**:
    - Side-by-side dedicated panels for Customer Ledgers (Debit / Dr) and Supplier Ledgers (Credit / Cr).
    - Real-time client-side search filtering on party dropdowns.
    - Top outstanding debtors and creditors quick-access cards.
    - Double-click selection and auto-redirect support.
  - **Customer & Supplier Ledger Statements (`customer_ledger.html`, `supplier_ledger.html`)**:
    - Modern profile summary grids displaying credit limits, opening balances, and net outstanding dues.
    - Print-ready statements (`window.print()`) with dedicated print media styles hiding UI navigation.
    - Clear chronological ledger rows with separate Debit, Credit, and Running Balance columns.
  - **Payment Vouchers & Settlements View Upgrade (`payment_list.html`)**:
    - Added settlement direction badges (`📥 Received (Settles Dr)` vs `📤 Disbursed (Settles Cr)`).
    - Aggregate filtered volume stat card and responsive pagination.
- **Multi-Tenancy Scoping & Data Isolation**:
  - Enforced strict `active_company` scoping across `ledger_select`, `customer_ledger`, and `supplier_ledger` views in `apps/credit/views.py`.
- **Automated Test Suite Expansion**:
  - Added 4 comprehensive view tests in `tests/test_credit_management.py`.
  - Expanded test suite to **170 passing tests (100% green)**.

---

## [1.6.0] - 2026-10-05

### Added
- **Inline Quick-Add Modals & Entity Creation Engine**:
  - Implemented lightweight accessible modal popups allowing users to add **Companies**, **Customers**, **Suppliers**, **Products**, **Categories**, and **Sellers** directly within form views without page refreshes or losing form inputs.
  - Added JSON/AJAX API response handling to `company_create`, `supplier_create`, `product_create`, `category_create`, and `seller_create`.
  - Added `static/js/quick_add.js` supporting asynchronous modal submission, instant dropdown option insertion, auto-selection, live calculation triggering, and non-blocking toast alerts.
- **Form State Persistence & Redirect Recovery**:
  - Implemented `sessionStorage` automatic draft persistence across `sale_form.html`, `purchase_form.html`, and `product_form.html` to guarantee zero loss of entered fields during page reload or redirect.
  - Added `return_to` / `next` query parameter support returning back to the originating form with newly created entity IDs pre-selected (`?company_id=...`, `?supplier_id=...`, `?customer_id=...`).
- **Form Template Redesign & Field Alignment**:
  - Completely redesigned `sale_form.html`, `purchase_form.html`, and `product_form.html` to match backend form definitions.
  - Added live interactive subtotal, discount, tax, and grand total calculations.
  - Added empty state onboarding warnings guiding users to set up company profiles.
- **Automated Test Suite**:
  - Added 13 comprehensive unit and integration tests in `tests/test_quick_add_and_forms.py`.
  - Full suite expanded to **166 passing tests (100% green)**.

---

## [1.5.0] - 2026-10-03

### Added
- **Centralized Living Documentation System**:
  - Implemented modular documentation tree under `docs/` (`architecture/`, `database/`, `api/`, `features/`, `security/`, `testing/`, `ui/`, `diagrams/`).
  - Added 16-point standard feature documents for Inventory, Sales, Purchases, Payments, Receivables/Payables, Cheque Management, Notifications, SMS, and Import/Export.
  - Added full suite of Mermaid architectural diagrams (ER Diagram, Context & Process DFD, Role Use Cases, Class Diagram, Activity Diagram, Sequence Diagram).
  - Added comprehensive End-to-End Traceability Matrix (`docs/TRACEABILITY_MATRIX.md`).
  - Added structured Change Management protocol with Change Request registry (`docs/CHANGE_MANAGEMENT.md`).
- **Notification Engine Specification**:
  - Defined multi-channel alert matrix (In-App, Popup, Notification Center, SMS) with exact triggers for low/critical/out-of-stock, overdue payments, and cheque clearing reminders.
- **Cheque Lifecycle Management Rules**:
  - Documented complete cheque lifecycle (Issued/Received, Due, Cleared, Bounced, Cancelled) and dynamic 7-day, 3-day, 2-day, 1-day, due-today reminder schedules.

### Changed
- Refactored documentation portals to establish single authoritative sources of truth for Database, API, and Domain logic.
- Synchronized terminology across documentation, UI templates, and API endpoints (`Receivables & Payables Summary`).

---

## [1.4.0] - 2026-10-02

### Added
- **Udhaar / Credit Management System (Receivables & Payables)**:
  - Added `CreditService` pure domain service (`backend/domain/services/credit_service.py`) supporting atomic credit sales, credit purchases, and partial payments without double inventory mutations.
  - Implemented customer dues and supplier dues aggregation with real-time balance calculations.
  - Implemented chronological party ledgers with running balance tracking for customers and suppliers.
  - Added dedicated Django Web UI module (`apps/credit/`) featuring Credit Dashboard, Give Credit, Take Credit, Payment Vouchers, Outstanding Dues, and Overdue tracking.
  - Added FastAPI REST API endpoints (`/api/v1/credit/`): `summary`, `given`, `taken`, `payments`, `customers-dues`, `suppliers-dues`, `overdue`, and `ledger`.
  - Added non-destructive database migrations (`sales.0002`, `purchases.0002`) adding indexed `due_date` and `Payment.created_by` / `Payment.notes`.
- **Automated Test Suite**:
  - Added 19 comprehensive tests in `tests/test_credit_management.py`.
  - Expanded test suite to **138 green tests (100% pass rate)**.

---

## [1.3.0] - 2026-10-02

### Added
- **Performance & Security Hardening (Part 14)**:
  - Implemented `PerformanceTimingMiddleware` attaching `X-Response-Time` latency headers and logging warnings for queries > 500ms.
  - Tuned relational database queries using `select_related` and `prefetch_related` across product and invoice listings, eliminating N+1 query bottlenecks.
  - Added structured Python logging with automatic sensitive credential redaction (`SensitiveDataFilter`).
  - Configured caching layer (`CACHES['default']`) ready for in-memory or Redis backends.
  - Added WCAG AA accessibility compliance enhancements: skip links, ARIA labels, semantic table headers, and form-input pairings.
  - Added automated test suite `tests/test_performance_and_security.py`.

---

## [1.2.0] - 2026-10-01

### Added
- **File Management & Export Engine (Part 12)**:
  - Added CSV and formatted Excel (.xlsx) file generation utilities with UTF-8 BOM encoding.
  - Added uploaded spreadsheet parser supporting CSV and XLSX formats with 10MB guard and filename sanitization.
  - Added transactional email service with fallback logging to `EmailLog`.
  - Implemented audit logging (`AuditLog`) capturing user, module, action, IP, and timestamp.

---

## [1.1.0] - 2026-09-30

### Added
- **Authentication & RBAC Foundation (Part 7)**:
  - Custom user model supporting multi-tenancy and company scoping.
  - Hybrid session authentication (Django web) and JWT Bearer token authentication (FastAPI REST).
  - Role-Based Access Control (RBAC): Super Admin, Company Admin, Manager, Cashier, Viewer.
  - Token revocation list (`RevokedToken`) for secure logout.

---

## [1.0.0] - 2026-09-28

### Added
- **Initial Hybrid Architecture Migration**:
  - Scaffolding of target hybrid Django 5.1+ / FastAPI project.
  - Bootstrapping of Django ORM inside FastAPI (`django.setup()`).
  - Relational database schema with 20+ models across 13 apps.
  - Core domain services for Sales, Purchases, Stock, and Authentication.
  - Minimalist Royal Blue & Slate design system (`docs/DESIGN_SYSTEM.md`).
