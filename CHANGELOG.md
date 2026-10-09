# Changelog

All notable changes to the **BizFlow** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
  - Added automated test cases in `tests/test_quick_add_and_forms.py` verifying custom transaction dates, due dates, and all date range filters (169 tests green, 100% pass rate).

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
