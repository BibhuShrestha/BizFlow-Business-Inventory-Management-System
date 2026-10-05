# BizFlow Documentation Portal

> **Central Living Documentation & Change Management System for BizFlow**  
> *A unified Business Inventory & ERP System built with Django 5.1+ (SSR Web UI & Admin) and FastAPI (REST API).*

---

## 1. Documentation as a Living System

Documentation in BizFlow is **not a one-time deliverable**. It is an active, living subsystem synchronized continuously with the codebase, database schema, API contracts, business rules, and automated test suite.

Whenever any feature, module, database model, API endpoint, UI workflow, business rule, notification, security policy, or integration is added, modified, renamed, or deprecated, the corresponding documentation must be updated in the same change commit.

```
Code ⟷ Database Migration ⟷ API Contracts ⟷ UI ⟷ Tests ⟷ Documentation ⟷ Diagrams
```

---

## 2. Documentation Directory Map

```text
docs/
├── README.md                      # Central portal & documentation index (this file)
├── PRD.md                         # Product Requirements Document & system scope
├── CHANGELOG.md                   # Semantic versioning changelog & chronological releases
├── CHANGE_MANAGEMENT.md           # Change request protocol, impact analysis & DoD
├── TRACEABILITY_MATRIX.md         # End-to-end requirement-to-code-to-test traceability
│
├── architecture/                  # System architecture specifications
│   ├── overview.md                # System topology, hybrid Django + FastAPI design
│   ├── modules.md                 # Complete breakdown of all 13 Django apps & routers
│   └── integrations.md            # Email, OAuth, SMS, PDF, and file export pipelines
│
├── database/                      # Database architecture & schema
│   ├── schema.md                  # Comprehensive table definitions & data types
│   ├── relationships.md           # Foreign keys, cardinality, and referential integrity
│   └── migrations.md              # Migration ledger, sequence, and rollback guidelines
│
├── api/                           # REST API layer (FastAPI)
│   ├── endpoints.md               # API route catalog, parameters, schemas, responses
│   └── authentication.md          # JWT bearer tokens, refresh rotation, permissions
│
├── features/                      # Deep-dive 16-point feature specifications
│   ├── inventory.md               # Products, categories, stock ledger, valuation
│   ├── sales.md                   # Invoices, customers, discounting, cash sales
│   ├── purchases.md               # Vendor purchase orders, supplier bills, stock in
│   ├── payments.md                # Payment vouchers, cash/bank/QR settlements
│   ├── receivables-payables.md    # Udhaar / credit tracking, dues, party ledgers
│   ├── cheque-management.md       # Cheque issuance, receipt, clearing, reminder rules
│   ├── notifications.md           # In-app, popup, SMS alert triggers & thresholds
│   ├── sms.md                     # SMS gateway architecture, templates, retry logic
│   └── import-export.md           # Excel (.xlsx) & CSV file parsing and export engine
│
├── security/                      # Application security guidelines
│   └── security.md                # Auth, Argon2/PBKDF2, CSRF, JWT, RBAC, audit logging
│
├── testing/                       # Quality assurance & verification
│   ├── testing-strategy.md        # Test pyramid, in-memory SQLite isolation, guidelines
│   └── test-cases.md              # Catalog of 138+ automated test cases & matrix
│
├── ui/                            # Design system & frontend architecture
│   └── design-system.md           # Design tokens, Royal Blue palette, accessibility
│
└── diagrams/                      # System visual architecture (Mermaid)
    ├── er-diagram.md              # Complete relational Entity-Relationship model
    ├── dfd.md                     # Data Flow Diagrams (Context Level 0 & Level 1)
    ├── use-case.md                # Role-based use case model (Cashier, Manager, Admin)
    ├── class-diagram.md           # Domain services, models, and repositories classes
    ├── activity-diagram.md        # Sales invoice & stock decrement workflow
    └── sequence-diagram.md        # Udhaar credit sale & partial payment flow
```

---

## 3. Single Source of Truth Registry

To prevent discrepancies and maintain architectural integrity, BizFlow designates authoritative sources of truth:

| Concern | Authoritative Source of Truth | Synchronized Secondary Artifacts |
|---|---|---|
| **Database Schema** | Django ORM Models (`backend/django_app/apps/*/models.py`) | [`docs/database/schema.md`](file:///e:/project/Business%20Management%20System/docs/database/schema.md), [`docs/diagrams/er-diagram.md`](file:///e:/project/Business%20Management%20System/docs/diagrams/er-diagram.md) |
| **API Contracts** | FastAPI Route Handlers & Pydantic Schemas (`backend/api/`) | [`docs/api/endpoints.md`](file:///e:/project/Business%20Management%20System/docs/api/endpoints.md), OpenAPI `/api/docs` |
| **Business Logic** | Pure Domain Services (`backend/domain/services/`) | [`docs/features/*.md`](file:///e:/project/Business%20Management%20System/docs/features/), Unit Tests in `tests/` |
| **User Interface** | Django Templates & Static CSS (`backend/django_app/`) | [`docs/ui/design-system.md`](file:///e:/project/Business%20Management%20System/docs/ui/design-system.md) |
| **Requirements** | Product Requirements Document | [`docs/PRD.md`](file:///e:/project/Business%20Management%20System/docs/PRD.md), [`docs/TRACEABILITY_MATRIX.md`](file:///e:/project/Business%20Management%20System/docs/TRACEABILITY_MATRIX.md) |
| **Notification Rules** | Notification Service & Feature Spec | [`docs/features/notifications.md`](file:///e:/project/Business%20Management%20System/docs/features/notifications.md) |
| **System Evolution** | Change Management System & Changelog | [`docs/CHANGE_MANAGEMENT.md`](file:///e:/project/Business%20Management%20System/docs/CHANGE_MANAGEMENT.md), [`CHANGELOG.md`](file:///e:/project/Business%20Management%20System/CHANGELOG.md) |

---

## 4. Feature Documentation Standard (16 Pillars)

Every feature document located in `docs/features/` adheres to a strict 16-point standard:

1. **Purpose**: Executive statement of why the feature exists and business problem solved.
2. **Scope**: What is included, supported boundaries, and what is out of scope.
3. **User Roles**: Access privileges (Super Admin, Company Admin, Manager, Cashier, Viewer).
4. **Business Rules**: Mathematical formulas, validations, thresholds, edge conditions.
5. **User Workflow**: Step-by-step end-user interaction journey.
6. **Database Relationships**: Models, table fields, foreign keys, cascade policies.
7. **API Endpoints**: REST endpoints, HTTP methods, request payloads, responses.
8. **UI Pages & Components**: Django view routes, template files, forms, modals.
9. **Notifications & Alerts**: In-app triggers, threshold alerts, dispatched events.
10. **Security Considerations**: CSRF, object-level permissions, tenant scoping, sanitization.
11. **Validation Rules**: Pydantic schemas, Django clean methods, domain constraints.
12. **Error Handling**: Custom domain exceptions, HTTP status codes, error user feedback.
13. **Import/Export Behavior**: CSV/Excel templates, field mapping, parsing logic.
14. **Testing Requirements**: Unit, integration, and UI verification test cases.
15. **Related Features**: Interconnected subsystems and cross-module couplings.
16. **Change History**: Chronological log of changes to the feature specification.

---

## 5. Change Impact Analysis & Definition of Done

Before modifying any feature, execute an **Impact Analysis**:

```text
Change Request
      ↓
Business Logic (backend/domain/services/)
      ↓
Database Schema & Migrations (backend/django_app/apps/*/models.py)
      ↓
API Routers & Schemas (backend/api/)
      ↓
UI Views & Templates (backend/django_app/apps/*/views.py)
      ↓
Notification Rules (features/notifications.md)
      ↓
Security & Permissions (apps/accounts/permissions.py)
      ↓
Automated Tests (tests/)
      ↓
Documentation & Diagrams (docs/)
```

A feature or modification is considered **DONE** only when:
- [x] Code passes PEP 8 formatting and type checks.
- [x] Database migrations are generated, tested, and reversible.
- [x] API endpoints return expected Pydantic response models and accurate status codes.
- [x] UI templates comply with the design system and WCAG AA accessibility standards.
- [x] 100% of automated tests pass (`python -m pytest`).
- [x] Relevant feature documents in `docs/features/` are updated.
- [x] API, Database, and UI documentation reflect current state.
- [x] Diagrams (ER, Sequence, Activity) match modified flows.
- [x] [`CHANGELOG.md`](file:///e:/project/Business%20Management%20System/CHANGELOG.md) and [`docs/CHANGE_MANAGEMENT.md`](file:///e:/project/Business%20Management%20System/docs/CHANGE_MANAGEMENT.md) record the change entry.
