# Security & Hardening Documentation

## 1. Principles & Objectives
Security is built natively into the application architecture rather than retrofitted as an afterthought.
- **Fail Securely**: Default deny permissions and explicit authorization checks.
- **Defense in Depth**: Multiple security layers (reverse proxy, middleware, framework-level ORM escaping, domain services, and database constraints).
- **Clean User Experience**: Technical protections are enforced transparently behind the scenes without user-facing threat matrix clutter (no alarmist dashboards listing DDoS, malware, or brute force warnings).
- **Zero Credential Leaks**: Credentials, tokens, and secrets are excluded from source control and redacted from log files.

---

## 2. Authentication & Authorization

### Web Interface (Django)
- **Session Framework**: Backed by secure database-stored sessions.
- **Cookie Protections**:
  - `SESSION_COOKIE_HTTPONLY = True` (blocks JavaScript access via `document.cookie`).
  - `CSRF_COOKIE_HTTPONLY = True` (prevents cross-site cookie tampering).
  - `SESSION_COOKIE_SAMESITE = 'Lax'` and `CSRF_COOKIE_SAMESITE = 'Lax'` (mitigates cross-site request forgery).
  - `SESSION_COOKIE_SECURE = True` in production (enforces HTTPS-only transmission).
- **Password Hasher Compatibility**: Supports Argon2, PBKDF2-SHA256, and legacy Flask Werkzeug scrypt/pbkdf2 hashes for zero-downtime credential migration.

### API Interface (FastAPI)
- **JWT Bearer Authentication**: Short-lived access tokens (30 minutes) and refresh tokens (7 days).
- **Stateless Verification**: Cryptographically signed using HMAC-SHA256 with server-side secret key.
- **Token Invalidation**: Immediate logout revocation support.

### Role-Based Access Control (RBAC)
Four primary permission tiers enforced across Django views and FastAPI routers:
| Role | Access Scope |
|------|--------------|
| `admin` | Full system control, user lifecycle management, audit logs, system configuration |
| `manager` | Financial daybook, reports, inventory adjustments, company & seller settings |
| `staff` | Daily operations: sales invoices, purchase bills, product catalog, customer/supplier records |
| `customer` | Read-only access to published public items and historical self-invoices |

---

## 3. Logging & Sensitive Data Redaction

Logging is implemented through `apps.core_app.logging_filters.SensitiveDataFilter`.

### What Is Logged
- Authentication events (successful logins, failed attempts, logouts with IP/User-Agent).
- Business transactions (order creation, stock adjustments, invoice generation).
- Background job processing and failures.
- System warnings and unhandled exceptions (logged internally with full detail).

### What Is NEVER Logged
The `SensitiveDataFilter` actively sanitizes log records, regex-masking any data matching:
- Passwords (`password`, `pass`, `new_password`)
- Bearer tokens and authorization headers
- API keys and shared secrets
- Personally identifiable financial numbers or raw card/cheque credentials

---

## 4. Error Handling & Stack Trace Protection

- End users are never presented with raw Python tracebacks, database queries, or server internals.
- Dedicated semantic error templates:
  - `400 Bad Request` (`templates/errors/400.html`)
  - `403 Forbidden` (`templates/errors/403.html`)
  - `404 Not Found` (`templates/errors/404.html`)
  - `500 Server Error` (`templates/errors/500.html`)
- All error views log underlying technical tracebacks to internal server logs while rendering clean, accessible, branded user responses.

---

## 5. File Upload Hardening

File intake in `apps.core_app.exports.parse_uploaded_file`:
- **Size Limitation**: Strict 10MB maximum file size ceiling. Oversized payloads are immediately rejected.
- **Filename Sanitization**: Uploaded filenames are stripped of directory traversal sequences via `os.path.basename` and regex filtering.
- **Extension Whitelist**: Only `.csv`, `.xlsx`, and `.xls` files are accepted for import pipelines.
- **MIME/Header Inspection**: Uploaded data streams are validated for tabular format before domain ingestion.

---

## 6. HTTP Security Headers

Every HTTP response includes hardening headers:
| Header | Value | Purpose |
|--------|-------|---------|
| `X-Frame-Options` | `DENY` | Clickjacking prevention |
| `X-Content-Type-Options` | `nosniff` | MIME-type sniffing prevention |
| `X-Response-Time` | Dynamic (e.g. `24.5ms`) | Performance latency transparency |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Protects sensitive URL query parameters |

---

## 7. Performance & Optimization Architecture

- **Database Indexes**: Applied on foreign keys, transaction dates (`sale_date`, `purchase_date`), SKU identifiers, and invoice numbers.
- **Query Optimization**: Extensive use of `select_related()` on single foreign keys (`customer`, `company`, `supplier`, `category`) and `prefetch_related()` on many-to-many/reverse relations (`items__product`) to eliminate N+1 database queries.
- **Pagination**: Uniform pagination across all list interfaces (`per_page=15` or `20`) using `paginate_queryset` to prevent memory exhaustion on large datasets.
- **Caching**: Configured `LocMemCache` for development/testing, ready for Redis in production (`CACHES['default']`).
- **Response Latency Profiling**: `PerformanceTimingMiddleware` logs a warning for any request taking longer than 500ms to assist proactive query tuning.

---

## 8. Accessibility (a11y) & UX Hardening

- **Semantic HTML5**: Native `<main>`, `<nav>`, `<header>`, `<article>`, `<section>`, and `<footer>` elements.
- **Accessible Form Controls**: Every input element is paired with an explicit `<label for="...">`, assistive helper text, and high-visibility error messaging.
- **Keyboard Navigation**: Universal visible focus indicator (`:focus-visible`) styling across all interactive elements (buttons, inputs, links).
- **Color Contrast**: Complies with WCAG 2.1 AA standard using high-contrast slate-900 typography on white/neutral backgrounds.

---

## 9. Udhaar / Credit Financial Security & Controls

- **Role-Based Financial Authorization**:
  - `staff` and above can record credit transactions and register payment settlements.
  - Deletion of existing credit records or payment vouchers is strictly restricted to `admin` and `manager` roles (`@role_required(["admin", "manager"])`).
- **Overpayment Prevention**:
  - Validates all incoming payment amounts against the target transaction's remaining balance (`amount <= remaining_amount`).
  - Attempts to submit payments exceeding the outstanding due are blocked at both Domain Service and Form/API validation levels.
- **Inventory Mutation Isolation**:
  - Payment vouchers modify strictly cash and party ledger receivables/payables.
  - Payment voucher execution is architecturally isolated from inventory stock mutation to prevent stock drift.
- **Tenant Isolation**:
  - All credit transactions, customer records, supplier records, and payments are strictly partitioned by `company_id`.
- **Immutable Audit Logging**:
  - Every credit creation, modification, deletion, and payment transaction logs an entry in `AuditLog` including user ID, IP address, action, and payload summary.
