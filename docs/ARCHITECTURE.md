# Architecture Document

> **System Architecture for BizFlow (Django + FastAPI Migration)**

---

## 1. Overview & API-First Architectural Philosophy

BizFlow is built on a clean, layered **API-first architecture** designed to ensure complete separation of presentation and business logic.
In this paradigm, **Django and FastAPI are interface adapters**, not business containers.

### Anti-Pattern Avoided:
```
[ Django Template ] ──► [ Monolithic View Logic ] ──► [ Direct DB Queries ]
```
*Why this fails:* Business logic becomes trapped inside server-side HTML view functions, requiring duplicate implementations when adding mobile, desktop, or REST endpoints.

### Target Architecture:
```
          ┌─────────────────────────────────────────────────────────────┐
          │                      INTERFACE LAYER                        │
          │                                                             │
          │  ┌─────────────────────────┐   ┌─────────────────────────┐  │
          │  │     Django Web App      │   │       FastAPI App       │  │
          │  │ (SSR UI / Admin / Sess) │   │ (REST API / JWT / CORS) │  │
          │  └────────────┬────────────┘   └────────────┬────────────┘  │
          └───────────────┼─────────────────────────────┼───────────────┘
                          │                             │
                          │   HTTP / Form Post          │   HTTP / JSON
                          ▼                             ▼
          ┌─────────────────────────────────────────────────────────────┐
          │             APPLICATION SERVICES LAYER (backend/services/)   │
          │                                                             │
          │  • AuthService        • StockService        • SaleService   │
          │  • PurchaseService    • CreditService       • ReportService │
          │  • NepaliDateService                                        │
          └──────────────────────────────┬──────────────────────────────┘
                                         │
                                         ▼
          ┌─────────────────────────────────────────────────────────────┐
          │             DOMAIN LOGIC LAYER (backend/domain/)            │
          │                                                             │
          │  • Domain Exceptions (InsufficientStockError, NotFoundError)│
          │  • Domain Validators (Password complexity, stock rules)     │
          │  • Value Objects & Invariants                               │
          └──────────────────────────────┬──────────────────────────────┘
                                         │
                                         ▼
          ┌─────────────────────────────────────────────────────────────┐
          │         DATA ACCESS / REPOSITORY LAYER (backend/repositories)│
          │                                                             │
          │  • BaseRepository (Tenant-scoped queries, CRUD abstractions) │
          │  • Django ORM Models (Accounts, Inventory, Sales, etc.)     │
          └──────────────────────────────┬──────────────────────────────┘
                                         │
                                         ▼
          ┌─────────────────────────────────────────────────────────────┐
          │                      DATABASE LAYER                         │
          │                                                             │
          │  • Development: SQLite (Fast, zero-config local runs)       │
          │  • Production:  PostgreSQL 14+ / MySQL 8.0                  │
          │  • In-Memory:   SQLite (:memory: for sub-second test runs)  │
          └─────────────────────────────────────────────────────────────┘
```

---

## 2. Shared Business Logic Organization

The `backend/` directory is structured to make business logic 100% reusable across interfaces:

```
backend/
├── domain/                      # Pure domain definitions & business invariants
│   ├── exceptions.py            # Framework-agnostic error hierarchy
│   ├── services/                # Core domain business rule calculations
│   │   ├── credit_service.py    # Udhaar / Credit calculations, dues, payments & ledgers
│   │   └── ...
│   └── validators/              # Validation algorithms (e.g. password strength)
│
├── services/                    # Application services coordinating workflows
│   ├── auth_service.py          # User authentication and session orchestration
│   ├── stock_service.py         # Inventory deductions, additions, reconciliations
│   ├── sale_service.py          # Invoicing, line item calculations, taxes
│   ├── purchase_service.py      # Supplier bills and stock increments
│   └── nepali_date.py           # Bikram Sambat (BS) to Gregorian (AD) conversions
│
├── repositories/                # Data access layer
│   ├── base.py                  # Multi-tenant CompanyScoped repository base
│   └── ...                      # Model-specific query managers
│
├── validators/                  # Shared input validation rules
│   └── password.py              # Password complexity & format verifiers
│
├── integrations/                # External service gateways
│   ├── email.py                 # SMTP and transactional notifications
│   └── google_oauth.py          # Google OAuth 2.0 social auth client
│
├── core/                        # Cross-cutting foundational modules
│   ├── config.py                # Environment configuration
│   ├── security.py              # JWT token encoding/decoding & Argon2 hashing
│   └── exceptions.py            # Base application exception classes
│
├── django_app/                  # Django Web Application Interface
│   ├── config/settings/         # Settings (base.py, dev, prod, test)
│   ├── apps/                    # Django apps containing ORM models and SSR views
│   ├── static/                  # Shared CSS, JS, and vendor assets
│   └── templates/               # Server-rendered HTML templates (Bootstrap 5)
│
└── api/                         # FastAPI Application Interface
    ├── main.py                  # ASGI entry point (bootstraps Django ORM)
    ├── routers/                 # REST endpoints (/api/v1/...)
    └── schemas/                 # Strictly typed Pydantic models
```

---

## 3. Technology Stack & Responsibilities

### Django
- **Web Application**: Server-side rendered views using Bootstrap 5 for standard desktop browser users.
- **Django Admin**: Built-in superuser management, emergency data administration, and model inspection.
- **Authentication & Sessions**: Built-in secure session engine (`django.contrib.sessions`), HTTP-only cookies, and CSRF protection for web UI users.
- **Management Tools**: Custom `python manage.py` commands for database seeding, migrations, and operational maintenance.
- **Database Migrations & ORM**: Central schema definition for the entire system.

### FastAPI
- **REST API**: Asynchronous, high-performance JSON endpoints prefixed with `/api/v1/`.
- **API Documentation**: Automated OpenAPI/Swagger (`/api/docs`) and ReDoc (`/api/redoc`).
- **Token Security**: Stateless OAuth2 Bearer JWT authentication for headless clients.
- **Client Integration**: Primary backend for mobile apps, desktop POS terminals, and external integrations.
- **AI Integrations**: Asynchronous streaming endpoints for AI assistant queries.

### Database Architecture
- **Development**: SQLite (`inventory.db`) for rapid local setup without external database daemon prerequisites.
- **Testing**: In-memory SQLite (`:memory:`) ensuring the automated test suite executes in under 1 second.
- **Production**: Full production support for **PostgreSQL** and **MySQL**.
  - Configured seamlessly through `DATABASE_URL` (e.g. `postgresql://user:pass@host:5432/dbname` or `mysql://user:pass@host:3306/dbname`).
  - Architecture is database-agnostic through Django ORM and does **not** depend on SQLite-specific SQL or dialect quirks.

---

## 4. Future Client Architecture

```
                               ┌─────────────────────────┐
                               │       FastAPI REST      │
                               │        (/api/v1/)       │
                               └────────────┬────────────┘
                                            │ HTTPS / JSON / JWT
                    ┌───────────────────────┼───────────────────────┐
                    │                       │                       │
                    ▼                       ▼                       ▼
          ┌───────────────────┐   ┌───────────────────┐   ┌───────────────────┐
          │   Web Frontend    │   │Desktop POS Client │   │Mobile Applications│
          │  (React/Vue/Next) │   │ (PySide6 / Tauri) │   │ (Flutter / RN)    │
          └───────────────────┘   └───────────────────┘   └─────────┬─────────┘
                                                                    │
                                                              ┌─────┴─────┐
                                                              │           │
                                                           Android       iOS
```

### Desktop Client Options (Future Scope)
1. **PySide6 / Qt**: Recommended for native hardware integration (thermal receipt printers, USB barcode scanners, customer-facing pole displays, offline SQLite queue).
2. **Tauri (Rust + Web)**: Ultra-compact binaries (< 15MB) with minimal memory footprint.
3. **Electron**: Cross-platform POS wrapper sharing web UI components.

### Mobile Client Options (Future Scope)
1. **Flutter**: Single Dart codebase compiling to native ARM code for both Android and iOS with direct Bluetooth thermal printer support.
2. **React Native**: Cross-platform TypeScript application sharing domain types.
3. **Native Android (Kotlin) & Native iOS (Swift)**: Reserved for high-volume enterprise barcode terminals (Zebra, Honeywell).

---

## 5. Udhaar / Credit Management Architecture & Data Flow

The Udhaar / Credit feature integrates seamlessly across Django Web UI, FastAPI, Domain Services, and Database layers without creating redundant entities.

### Core Data Flow Diagram:
```
[ Cashier / User / API Client ]
             │
             ▼
   [ Interface Layer ]
   ├── Django: /credit/give/ | /credit/take/ | /credit/payments/
   └── FastAPI: /api/v1/credit/given | /credit/taken | /credit/payments
             │
             ▼
   [ CreditService (backend/domain/services/credit_service.py) ]
   ├── Validation (Positive amounts, stock availability, overpayment bounds)
   ├── Multi-line product subtotal, discount, VAT computation
   │
   ├── [ If Credit Given ]:
   │   ├── Creates Sale record with due_date
   │   ├── Decrements Product current_stock atomically
   │   ├── Logs OUT StockMovement
   │   └── Updates Customer receivable ledger
   │
   ├── [ If Credit Taken ]:
   │   ├── Creates Purchase record with due_date
   │   ├── Increments Product current_stock atomically
   │   ├── Logs IN StockMovement
   │   └── Updates Supplier payable ledger
   │
   └── [ If Payment Added ]:
       ├── Validates: payment_amount <= remaining_amount
       ├── Creates Payment record with created_by audit link
       ├── Recalculates remaining balance and dynamic status:
       │   (Unpaid -> Partially Paid -> Paid / Overdue)
       └── INVENTORY STOCK IS NEVER TOUCHED BY PAYMENTS
```

### Invariant Accounting & Ledger Engine:
1. **Zero Database Table Duplication**: Reuses existing `Sale`, `Purchase`, `Payment`, `SaleItem`, and `PurchaseItem` models.
2. **Deterministic Running Balance**:
   - Customer statement: `Balance_i = Balance_{i-1} + Sale_Total_i - Payment_Amount_i`.
   - Supplier statement: `Balance_i = Balance_{i-1} + Purchase_Total_i - Payment_Amount_i`.
3. **Audit Trail**: Every creation, update, payment, and deletion emits an immutable `AuditLog` entry.