# Changelog

> For the primary project changelog, please see the root [CHANGELOG.md](file:///e:/project/BizFlow%20%E2%80%94%20Business%20Inventory%20Management%20System/CHANGELOG.md).

All releases, major modifications, enhancements, bug fixes, and architectural additions are versioned and logged chronologically in [`CHANGELOG.md`](file:///e:/project/BizFlow%20%E2%80%94%20Business%20Inventory%20Management%20System/CHANGELOG.md).

---

### Latest Release: `v2.5.0` (2026-10-16)

- **Supabase PostgreSQL & Native Driver Architecture**: Full PostgreSQL 14+ and Supabase support with direct and connection pooler handling, SSL enforcement, and `psycopg2-binary`.
- **Database Backup, Migration & Verification Suite**: Scripts for non-destructive JSON/SQL backup, automated sequence alignment (`setval`), and 4-tier data verification.
- **Production Hardening**: Production settings audited with 0 issues via `manage.py check --deploy`, WhiteNoise static file serving, and Procfile configuration.
- **XSS & Multi-Tenant Import Hardening**: Protected client-side toast and error handlers against XSS and scoped bulk inventory imports to active company.

---

### Previous Release: `v2.4.0` (2026-10-15)

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
- **Global Keyboard Shortcut Ergonomics**:
  - Central keyboard shortcut manager for cashier and accountant workflows (<kbd>Ctrl+K</kbd>, <kbd>N</kbd>, <kbd>P</kbd>, <kbd>I</kbd>, <kbd>C</kbd>, <kbd>W</kbd>, <kbd>D</kbd>, <kbd>?</kbd>, <kbd>Ctrl+Enter</kbd>, <kbd>Esc</kbd>).
  - Added `<kbd>` design tokens in `main.css` and embedded badges on action buttons across Dashboard, Sales, Purchases, Inventory, and Customers.
- **Verification & Test Suite**:
  - Full pytest verification passing with **231 tests green, 5 skipped, 0 failures (100% pass rate)**.

---

### Previous Releases:

#### `v2.3.0` (2026-10-10)
- UI/UX component standardization (`.filter-bar`, `.search-input-wrap`, `.empty-state`).
- Streamlined Sales and Purchase transaction forms with two-column responsive layouts, sticky live summary sidebars, and real-time Nepali currency formatting (`Rs. X,XX,XXX.XX`).
- 221 automated tests passing green.

#### `v2.2.0` (2026-10-09)
- Google OAuth2 social login integration and granular role-based permissions matrix (Customer, Cashier, Staff, Manager, Admin).
- 221 automated tests passing green.

#### `v2.1.0` (2026-10-08)
- AI Business Analytics & Decision Support suite (`/reports/analytics/`).
- 182 automated tests passing green.

#### `v2.0.0` (2026-10-06)
- Double-entry accounting indicators, running balance party ledgers (Customer & Supplier).
- 170 automated tests passing green.

#### `v1.5.0` (2026-10-03)
- Implemented modular living documentation system under `docs/`.
- 16-point standard feature documentation across Inventory, Sales, Purchases, Payments, Credit/Receivables/Payables, Cheque Management, Notifications, SMS, and Import/Export.
- Full Mermaid diagram suite (ER, DFD, Use Case, Class, Activity, Sequence).
- Comprehensive Requirements Traceability Matrix (`docs/TRACEABILITY_MATRIX.md`).
- Structured Change Management & Change Request registry (`docs/CHANGE_MANAGEMENT.md`).
