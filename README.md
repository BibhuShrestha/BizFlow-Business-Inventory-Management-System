# BizFlow — Business Inventory Management System

> Django + FastAPI edition — staged migration from the original Flask project.

## Project Overview

**BizFlow** is a comprehensive multi-company business inventory, sales, purchase, and financial management system designed for small and medium enterprises (SMEs) in Nepal. It provides an integrated platform combining stock control, invoicing, vendor/customer ledgers, expense tracking, and reporting with native Nepali Bikram Sambat (BS) calendar integration.

This is a clean, modular **Django 6.0 + FastAPI** architecture migrated from a legacy Flask monolith. Django provides the server-rendered web UI, admin dashboard, ORM, and session auth; FastAPI delivers a high-performance REST API for future desktop and mobile clients; and all business logic lives in a shared, framework-agnostic domain/services layer.

---

## Features

- **Multi-Company Management** — manage multiple businesses/branches from one account
- **Inventory & Stock Control** — product catalog with SKU, stock levels, low-stock alerts, categories
- **Sales Invoicing** — create, manage, and print invoices with automatic stock deduction
- **Purchase Bills** — vendor bills with automatic stock intake
- **Receivables & Payables Management** — track Customer Receivables (Credit Given / Dr) and Supplier Payables (Credit Taken / Cr) with partial payments, overdue tracking, cheque schedules, and running ledgers
- **Expense Tracking** — operational expense categories and records
- **Financial Daybook & Reports** — daily, monthly, and custom-period reports
- **CSV / Excel / PDF Exports** — export any dataset
- **Nepali Bikram Sambat Date Support** — native BS calendar conversion and display
- **Role-Based Access Control** — admin, manager, staff, customer roles with enforced permissions
- **JWT API Authentication** — FastAPI REST API with access/refresh token support
- **Blue & White Minimal UI** — responsive, accessible, keyboard-navigable design

---

## Architecture

```
                        USERS
                          |
         +----------------+-----------------+
         |                |                 |
       Web             Desktop           Mobile
         |                |                 |
         v                +--------+--------+
      Django                       |
         |                         v
         +---------------------> FastAPI
                         |
                         v
               Application Services (Shared)
                         |
                         v
                   Domain Logic (Pure Python)
                         |
                         v
                  Repository / Data Layer
                         |
                         v
                 Django ORM --> SQLite (dev) / PostgreSQL (prod)
```

> **Key Rule:** Django and FastAPI are interfaces only. Business logic belongs in reusable, framework-agnostic services and domain modules under `backend/domain/`.

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Web UI | Django 6.0 | Server-rendered HTML, admin, ORM |
| REST API | FastAPI 0.142+ | JSON API for mobile, desktop, external clients |
| Business Logic | Python (pure) | Shared domain services and validators |
| Database (Dev) | SQLite | Fast zero-config local development |
| Database (Prod) | MySQL / PostgreSQL | Production-grade relational database |
| Auth (Web) | Django sessions + PBKDF2/Argon2 | Session-based web authentication |
| Auth (API) | JWT Bearer tokens | Stateless API authentication |
| Templates | Django Template Engine | Server-side HTML rendering |
| CSS | Vanilla CSS (custom design system) | Blue/white minimal responsive UI |
| Testing | pytest + pytest-django | Unit, integration, and API tests |

---

## Requirements

- Python 3.12+
- pip
- Git

Install all dependencies:

```bash
pip install -r requirements.txt
```

---

## Installation

### 1. Clone the repository

```bash
git clone <repo-url>
cd business_new
```

### 2. Create a virtual environment (recommended)

```bash
py -3.12 -m venv venv
venv\Scripts\activate       # Windows
source venv/bin/activate    # macOS / Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Environment Variables

Copy the example file and fill in your values:

```bash
copy .env.example .env
```

Key variables in `.env`:

```env
SECRET_KEY=your-django-secret-key
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
JWT_SECRET_KEY=your-jwt-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1
```

> **Never commit `.env` to source control.** See `.env.example` for all required variables with safe placeholder values.

---

## Database Setup

### Development (SQLite)

```bash
cd backend/django_app
py manage.py migrate
py manage.py createsuperuser
```

### Production (PostgreSQL / MySQL)

Update `DATABASE_URL` in `.env`:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/bizflow
```

Then run:

```bash
py manage.py migrate
```

---

## Django Setup

```bash
cd backend/django_app
py manage.py migrate
py manage.py collectstatic
py manage.py createsuperuser
```

---

## FastAPI Setup

FastAPI shares Django ORM models through Django setup bootstrapping. No separate database is required.

```bash
cd backend
py -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8001
```

API documentation is available at:

- Swagger UI: `http://localhost:8001/api/docs`
- ReDoc: `http://localhost:8001/api/redoc`

---

## Running Development Server

**Terminal 1 — Django web UI (port 8000):**

```bash
cd backend/django_app
py manage.py runserver
```

**Terminal 2 — FastAPI REST API (port 8001):**

```bash
cd backend
py -m uvicorn api.main:app --reload --port 8001
```

| Service | URL | Purpose |
|---------|-----|---------|
| Django Web UI | http://localhost:8000 | Main web application |
| FastAPI REST API | http://localhost:8001 | REST API for clients |
| API Docs (Swagger) | http://localhost:8001/api/docs | Interactive API docs |
| Django Admin | http://localhost:8000/admin/ | Admin backend |

---

## Running Tests

```bash
py -3.12 -m pytest tests/ -v
```

Run a specific test file:

```bash
py -3.12 -m pytest tests/test_django_web_application.py -v
```

Run with coverage:

```bash
py -3.12 -m pytest tests/ --cov=backend --cov-report=html
```

Currently **100 tests passing** (100% pass rate).

---

## Project Structure

```
business_new/
|
+-- backend/
|   +-- django_app/          Django web application
|   |   +-- manage.py
|   |   +-- config/          Settings (base, dev, prod, testing)
|   |   +-- apps/            Django applications
|   |   |   +-- accounts/    Users, roles, authentication
|   |   |   +-- companies/   Company and seller management
|   |   |   +-- inventory/   Products, categories, stock movements
|   |   |   +-- sales/       Sales invoices, customers
|   |   |   +-- purchases/   Purchase bills, suppliers
|   |   |   +-- accounting/  Expenses, daybook
|   |   |   +-- reports/     Financial and inventory reports
|   |   |   +-- dashboard/   Home, dashboard, notifications
|   |   |   +-- core_app/    Pagination, exports, middleware, error handlers
|   |   |   +-- audit/       Audit log
|   |   +-- templates/       HTML templates
|   |   +-- static/          CSS, JS, images
|   |   +-- media/           User-uploaded files
|   |
|   +-- api/                 FastAPI REST API
|   |   +-- main.py          App entry point
|   |   +-- routers/         Route handlers (auth, health, ...)
|   |   +-- schemas/         Pydantic request/response models
|   |   +-- dependencies/    Dependency injection (auth, DB)
|   |   +-- middleware/      Custom ASGI middleware
|   |
|   +-- domain/              Shared pure-Python business logic
|   |   +-- services/        Business services (stock, sale, purchase, report)
|   |   +-- validators/      Input validators (password, etc.)
|   |   +-- repositories/    Data access abstractions
|   |
|   +-- core/                Shared utilities
|   |   +-- config/          Core configuration
|   |   +-- exceptions/      Custom exception classes
|   |   +-- security/        JWT, hashing utilities
|   |
|   +-- integrations/        External service clients (email, Google OAuth, AI)
|
+-- tests/                   Pytest test suite (100 tests)
+-- docs/                    Full documentation suite
|   +-- PRD.md               Product Requirements Document
|   +-- ARCHITECTURE.md      Architecture design document
|   +-- DESIGN_SYSTEM.md     UI/UX design system
|   +-- SECURITY.md          Security and hardening guide
|   +-- TESTING.md           Testing strategy
|   +-- API.md               REST API documentation
|   +-- DATABASE.md          Database schema and relationships
|   +-- MIGRATION_MAP.md     Flask-to-Django migration map
|   +-- MIGRATION_STATUS.md  Migration progress tracker
|   +-- SEO.md               SEO strategy
|   +-- SEO_CHECKLIST.md     SEO pre-release checklist
|   +-- CODE_STYLE.md        Code style and standards
|   +-- AGENTS.md            AI agent instruction manual
|   +-- DEVELOPMENT.md       Developer setup and workflows
+-- mobile/                  Mobile client placeholder (Flutter / React Native)
+-- desktop/                 Desktop client placeholder (PySide6 / Tauri)
+-- scripts/                 Utility scripts
+-- .env.example             Environment variable template
+-- .gitignore
+-- pyproject.toml           Build and pytest configuration
+-- requirements.txt         Python dependencies
+-- README.md                This file
```

---

## API Documentation

The FastAPI REST API is versioned at `/api/v1/`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/auth/login | Login and receive access + refresh tokens |
| POST | /api/v1/auth/refresh | Refresh access token |
| POST | /api/v1/auth/logout | Revoke tokens |
| GET | /api/v1/auth/me | Get current user profile |
| GET | /api/v1/health | Health check |
| GET | /api/v1/credit/summary | Credit KPI summary (given, taken, dues) |
| GET | /api/v1/credit/given | List credit given transactions |
| POST | /api/v1/credit/given | Create customer credit invoice |
| GET | /api/v1/credit/taken | List supplier credit transactions |
| POST | /api/v1/credit/taken | Create supplier purchase credit |
| POST | /api/v1/credit/payments | Settle partial / full payment |
| GET | /api/v1/credit/ledger/customer/{id} | Customer statement of account |
| GET | /api/v1/credit/ledger/supplier/{id} | Supplier statement of account |

Interactive documentation: `http://localhost:8001/api/docs`

Full API documentation: [docs/API.md](docs/API.md)

---

## Receivables & Payables Management Guide

The **Receivables & Payables** module provides complete credit and debt lifecycle management:

### 1. Recording Receivables / Customer Credit (Debit / Dr)
- Navigate to **Receivables & Payables > Receivables Register** (or click `+ Record Receivable`).
- Select the Customer, Transaction Date, and Due Date.
- Add one or multiple items with quantity, unit price, and discount/tax.
- Optionally enter an initial paid amount.
- Submitting immediately deducts inventory stock and reflects in Customer Due and Customer Ledger.

### 2. Recording Payables / Supplier Credit (Credit / Cr)
- Navigate to **Receivables & Payables > Payables Register** (or click `+ Record Payable`).
- Select the Supplier, Bill number, and Due Date.
- Add line items with quantities and unit costs.
- Submitting immediately increments inventory stock and reflects in Supplier Due and Supplier Ledger.

### 3. Recording Payments & Settlements
- Open any transaction detail page or click **Add Payment**.
- Enter payment amount (cannot exceed remaining balance), method (Cash, Bank, QR/Fonepay, Cheque), reference, and notes.
- Submitting records a payment voucher, reduces the outstanding balance, and updates the status (`Unpaid` -> `Partially Paid` -> `Paid`).
- **Inventory stock is unaffected** by payments.

### 4. Viewing Party Ledgers (Statement of Accounts)
- Navigate to **Receivables & Payables > Party Ledgers** (or click **View Receivables/Payables Ledger** from any Customer/Supplier profile).
- Select the party and date range to view the chronological statement of debits, credits, and running balance.
- Print statements directly via the **Print Statement** action.

---

## Admin Setup

Access the Django admin panel at `http://localhost:8000/admin/`.

Create a superuser:

```bash
cd backend/django_app
py manage.py createsuperuser
```

The admin panel provides full access to all models including users, roles, products, sales, purchases, and audit logs.

---

## SEO

BizFlow uses a two-zone SEO approach:

- **Public Zone** (indexable): Landing page, login, register, forgot-password — these have proper meta titles, descriptions, canonical URLs, and Open Graph tags.
- **Private Zone** (non-indexable): All dashboard, inventory, sales, purchase, and API pages include `<meta name="robots" content="noindex, nofollow">` and return `X-Robots-Tag: noindex` HTTP headers.

`robots.txt` is served at `/robots.txt` and `sitemap.xml` at `/sitemap.xml`.

Full SEO strategy: [docs/SEO.md](docs/SEO.md)  
Pre-release checklist: [docs/SEO_CHECKLIST.md](docs/SEO_CHECKLIST.md)

---

## Production Notes

Before deploying to production:

1. Set `DEBUG=False` in `.env`
2. Set a strong `SECRET_KEY` (50+ random characters)
3. Set `ALLOWED_HOSTS` to your actual domain
4. Use PostgreSQL: update `DATABASE_URL`
5. Set `SESSION_COOKIE_SECURE=True` (HTTPS only)
6. Run behind a reverse proxy (Nginx/Caddy) with HTTPS
7. Run `py manage.py collectstatic`
8. Never commit `.env` to source control

See [docs/SECURITY.md](docs/SECURITY.md) for the full production security checklist.

---

## Future Mobile & Desktop Architecture

### Mobile (Android & iOS)
Recommended stack: **Flutter** or **React Native** consuming the FastAPI REST API at `/api/v1/`.

```
Mobile App --> FastAPI /api/v1/ --> Django ORM --> Database
```

See [mobile/README.md](mobile/README.md) for details.

### Desktop
Recommended stack: **PySide6/Qt** or **Tauri** consuming the FastAPI REST API.

```
Desktop App --> FastAPI /api/v1/ --> Django ORM --> Database
```

See [desktop/README.md](desktop/README.md) for details.

---

## Troubleshooting

### `No module named 'django'`
Make sure your virtual environment is activated and dependencies are installed:
```bash
pip install -r requirements.txt
```

### `DJANGO_SETTINGS_MODULE not set`
Run from within `backend/django_app/` or set the env var:
```bash
set DJANGO_SETTINGS_MODULE=config.settings.development
```

### Database migration errors
Delete old `db.sqlite3` and re-run migrations in development:
```bash
cd backend/django_app
py manage.py migrate
```

### FastAPI port conflict
Change the port:
```bash
py -m uvicorn api.main:app --reload --port 8002
```

### Tests failing
Ensure you are using Python 3.12:
```bash
py -3.12 -m pytest tests/ -v
```

---

## Living Documentation & Change Management System

BizFlow maintains a **centralized, living, synchronized documentation system** under [`docs/`](docs/README.md). Documentation evolves synchronously with code, migrations, tests, and API contracts.

| Document | Purpose |
|----------|---------|
| [docs/README.md](docs/README.md) | **Central Documentation Portal & Sitemap** |
| [CHANGELOG.md](CHANGELOG.md) | **Chronological releases & semantic versioning (v1.5.0)** |
| [docs/CHANGE_MANAGEMENT.md](docs/CHANGE_MANAGEMENT.md) | **Change Request protocol, impact analysis & Definition of Done** |
| [docs/TRACEABILITY_MATRIX.md](docs/TRACEABILITY_MATRIX.md) | **End-to-end requirement to code, API, UI & test mapping** |
| [docs/PRD.md](docs/PRD.md) | Product requirements and user stories |
| [docs/features/](docs/features/) | **16-point feature specs** (Inventory, Sales, Purchases, Payments, Credit, Cheques, Notifications, SMS, Import/Export) |
| [docs/diagrams/](docs/diagrams/) | **Mermaid visual diagrams** (ER, DFD Level 0/1, Use Cases, Class, Activity, Sequence) |
| [docs/architecture/](docs/architecture/) | Modular system architecture, modules catalog, and integrations |
| [docs/database/](docs/database/) | Database schema, foreign keys, relationships, and migrations |
| [docs/api/](docs/api/) | REST API endpoint specifications and JWT authentication |
| [docs/ui/design-system.md](docs/ui/design-system.md) | UI/UX design tokens, components, and accessibility |
| [docs/security/security.md](docs/security/security.md) | Security architecture, Argon2/PBKDF2, and threat defense |
| [docs/testing/](docs/testing/) | Testing strategy and 138+ automated test cases |
| [docs/MIGRATION_STATUS.md](docs/MIGRATION_STATUS.md) | Migration progress tracker |
| [AGENTS.md](AGENTS.md) | AI coding agent operating manual |
