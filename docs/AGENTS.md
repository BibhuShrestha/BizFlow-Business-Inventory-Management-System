# AGENTS.md -- AI Coding Agent Operating Manual

> **Primary Instruction Manual for AI Coding Assistants working on BizFlow.**  
> Read this document completely before generating or modifying any code in this repository.

---

## 1. Project Overview

BizFlow is a business management and inventory ERP system migrating from a legacy Flask monolith (`e:/project/business`) to a modern hybrid **Django 5.1+ / 6.0 + FastAPI** architecture (`e:/project/business_new`).

- **Django**: Powers the Server-Side Rendered (SSR) Web UI, Admin portal, ORM models, session authentication, and database migrations.
- **FastAPI**: Powers the high-performance REST API layer (`/api/v1/`) for desktop and mobile clients.
- **Domain Services**: Houses framework-agnostic pure Python business logic consumed identically by both Django and FastAPI.
- **Original Project**: Located at `e:/project/business`. **It must remain completely untouched, pristine, and never modified.**

---

## 2. Architecture Rules

1. **Separation of Concerns**:
   - `backend/django_app/`: UI views, forms, templates, URL routing, admin definitions.
   - `backend/api/`: FastAPI routers, Pydantic request/response schemas, API dependencies.
   - `backend/domain/`: Pure business logic, services (`SaleService`, `StockService`, etc.), and domain validators.
   - `backend/core/`: Application settings, security utilities (JWT, hashing), custom exceptions.
2. **Unified Database Access**:
   - Both Django and FastAPI use the **Django ORM** against a shared database.
   - FastAPI bootstraps Django ORM at startup (`django.setup()`) inside `backend/api/main.py`.
   - Never introduce a second ORM (such as SQLAlchemy or Tortoise) into the target project.
3. **No Direct Model Mutations in Controllers**:
   - Complex business calculations (e.g. creating a sale invoice that decrements stock and updates customer ledger) **must** reside in domain services, never inside view functions or route handlers.

---

## 3. Directory Rules

All code and assets must strictly adhere to the project tree:

```
business_new/
├── backend/
│   ├── django_app/
│   │   ├── config/settings/ (base.py, development.py, production.py, testing.py)
│   │   ├── apps/            (accounts, companies, inventory, sales, purchases, accounting, reports, audit, core_app)
│   │   ├── static/          (css/, js/, vendor/)
│   │   └── templates/       (base/, accounts/, dashboard/, etc.)
│   ├── api/
│   │   ├── main.py
│   │   ├── routers/         (health, auth, users, inventory, sales, purchases, reports)
│   │   └── schemas/         (pydantic schemas)
│   ├── core/                (config.py, security.py, exceptions.py)
│   ├── domain/              (services/, validators/, repositories/)
│   └── integrations/        (email, oauth, pdf)
├── desktop/                 (Future desktop client specs)
├── mobile/                  (Future mobile client specs)
├── docs/                    (All project architecture, PRD, API, DB docs)
└── tests/                   (Unified pytest suite)
```

Never create top-level directories outside of this defined architecture without explicit architectural approval.

---

## 4. Coding Rules

1. **Python Standards**:
   - Target Python 3.12+. Use modern type annotations (`list[str]`, `str | None`).
   - Follow PEP 8 guidelines strictly (4 spaces indentation, maximum line length 100 characters where practical).
   - Write descriptive function, class, and variable names (`calculate_invoice_tax` not `calc_tx`).
2. **Framework-Agnostic Services**:
   - Domain services must accept primitive data types or typed dataclasses/Pydantic models, returning domain objects or dictionaries.
   - Domain services must **never** accept HTTP request objects (`django.http.HttpRequest` or `fastapi.Request`).
3. **Error Handling**:
   - Raise explicit exceptions defined in `backend/core/exceptions.py` (`InsufficientStockError`, `NotFoundError`, `ValidationError`).
   - Never swallow exceptions silently with bare `except: pass`.

---

## 5. Database Rules

1. **Single Source of Truth**:
   - Django migrations manage all schema changes. Never run manual raw DDL commands outside of migrations.
2. **Multi-Tenancy Scoping**:
   - Every multi-tenant model must have a foreign key to `companies.Company`.
   - Every query performed in views or API routes must explicitly filter by the authenticated user's active company.
3. **Atomic Operations**:
   - Multi-table mutations (such as saving invoice lines, decrementing stock, and updating accounts) must be wrapped in `transaction.atomic()`.
4. **Explicit Primary Keys and Indices**:
   - Maintain `company_id`, `created_at`, `status`, and foreign keys indexed for high-volume operational queries.

---

## 6. API Rules

1. **Versioning**:
   - All REST API endpoints must be prefixed with `/api/v1/`.
2. **Schema Validation**:
   - All request bodies and query parameters must be validated using strictly typed Pydantic models.
   - Return appropriate HTTP status codes: `200 OK`, `201 Created`, `204 No Content`, `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`, `409 Conflict`, `422 Unprocessable Entity`.
3. **Interactive Documentation**:
   - OpenAPI documentation must be accessible at `/api/docs` and Redoc at `/api/redoc`.
   - Every route must include a clear docstring, summary, tags, and response models.
4. **Authentication**:
   - Protected API routes must use FastAPI dependencies (`Depends(get_current_user)`).

---

## 7. UI Rules

1. **Design System Adherence**:
   - Use the design tokens defined in `backend/django_app/static/css/main.css` and documented in `docs/DESIGN_SYSTEM.md`.
   - Follow the primary brand color `#1E40AF` (Royal Blue) and neutral palette.
2. **Accessibility & Usability**:
   - Include semantic HTML5 tags (`<main>`, `<nav>`, `<header>`, `<section>`, `<table>`).
   - Ensure all input controls have associated `<label>` elements.
   - Provide visual feedback for asynchronous actions (loading spinners, toast alerts).
   - Maintain full keyboard navigation support for high-frequency cashier workflows.

---

## 8. Security Rules

1. **Secret Management**:
   - Never commit sensitive secrets, API keys, database passwords, or JWT keys into source control.
   - Read all secrets from environment variables via `django-environ` / `pydantic-settings`.
2. **Password Security**:
   - Enforce strong password complexity rules via `domain.validators.password.validate_password`.
   - Store passwords using modern cryptographic hashes (Argon2 or PBKDF2-SHA256).
3. **Injection Prevention**:
   - Use parameterized queries via Django ORM at all times. Raw SQL queries must be avoided.
4. **Token Security**:
   - JWT access tokens must have short expiration periods (default 60 minutes).
   - Refresh tokens must be rotated or validated against revocation lists upon logout.

---

## 9. SEO Rules

1. **Indexability Policy**:
   - All authenticated application views (Dashboard, Invoices, Customers, Reports, Settings) are private business data and **MUST** have `<meta name="robots" content="noindex, nofollow">`.
   - The public entry points (Login, Register, Forgot Password, Landing) may have descriptive title tags and meta descriptions, but must avoid keyword stuffing.
2. **Semantic Hierarchy**:
   - Ensure a single `<h1>` tag per page representing the view's primary title.
   - Use logical heading hierarchy (`<h1>` -> `<h2>` -> `<h3>`).
3. **No SEO Spam**:
   - Never add deceptive hidden text, repetitive keyword blocks, or irrelevant anchor tags.

---

## 10. Testing Rules

1. **Test Before Complete**:
   - Every part implementation must run relevant tests before completion is reported.
   - The test suite must pass with 100% green status (`python -m pytest`).
2. **Test Independence**:
   - Unit and integration tests must run cleanly without depending on an external live database server (use in-memory SQLite settings via `config.settings.testing`).
3. **Preserve Flask Tests**:
   - Never modify or break the original Flask project test suite in `e:/project/business/tests`.

---

## 11. Documentation Rules

1. **Keep Documents Current**:
   - Update `docs/MIGRATION_STATUS.md` immediately upon completing any milestone or part.
   - Document any API endpoint changes in `docs/API.md`.
   - Document any database model adjustments in `docs/DATABASE.md`.
2. **Readable Markdown**:
   - Maintain clear GitHub-flavored markdown with accurate tables, code blocks, and diagrams.

---

## 12. Git Rules

1. **Clear Commit Intent**:
   - Commit messages must clearly state the part or feature implemented (e.g. `feat(part-3): complete migration documentation`).
2. **Branch Discipline**:
   - Work on staged branches or verify atomic commits per migration part.
3. **Clean Diffs**:
   - Never leave trailing whitespace, temporary debug loggers, or commented-out debris in committed files.

---

## 13. Things AI Agents Must NOT Do

The following rules are absolute and must never be violated under any circumstances:

1. **DO NOT modify the original Flask project** (`e:/project/business`). It must remain strictly read-only as a reference.
2. **DO NOT delete existing functionality without explicit user approval**.
3. **DO NOT duplicate business logic** across Django views and FastAPI routes; use the shared `domain/` layer.
4. **DO NOT expose secrets, keys, or credentials** in code, docs, or artifacts.
5. **DO NOT bypass or ignore failing tests**. If a test fails, diagnose and resolve the root cause.
6. **DO NOT introduce unnecessary dependencies or bulky frameworks** when simple, maintainable Python/Django solutions suffice.
7. **DO NOT rewrite working modules without a clear technical rationale**.
8. **DO NOT change API contracts, parameters, or schemas without updating documentation**.
9. **DO NOT make private authenticated pages indexable** by web crawlers or search engines.
10. **DO NOT add SEO spam, hidden text, or manipulative meta tags**.
11. **DO NOT implement future parts early**. Staged migration requires completing only the current part before stopping.