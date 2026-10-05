# Security Architecture & Threat Mitigation

> **BizFlow Enterprise Security Guidelines**  
> *Authentication, Password Hashing, CSRF Defense, Rate Limiting, RBAC, and Audit Protocols.*

---

## 1. Authentication & Credential Storage

### A. Password Hashing
- Utilizes Django's modern password hashers with Argon2 (`Argon2PasswordHasher`) or PBKDF2-SHA256 (`PBKDF2PasswordHasher`).
- Strict minimum entropy enforced via `domain.validators.password.validate_password`:
  - Minimum 8 characters.
  - At least 1 uppercase letter, 1 lowercase letter, 1 number, and 1 special symbol.

### B. Session & Cookie Security
- `SESSION_COOKIE_HTTPONLY = True`: Blocks JavaScript `document.cookie` access (mitigating XSS session hijacking).
- `CSRF_COOKIE_HTTPONLY = False`: Allows front-end fetch/XHR handlers to read CSRF token.
- `SESSION_COOKIE_SECURE = True` in production (enforces HTTPS delivery).

---

## 2. Authorization & Multi-Tenancy Scoping

### A. Role-Based Access Control (RBAC)
BizFlow defines 5 hierarchical roles:
1. **Super Admin**: System owner, cross-company management, database backups.
2. **Company Admin**: Tenant owner, company settings, user provisioning, audit logs.
3. **Manager**: Inventory stock adjustments, vendor orders, customer credit overrides, financial daybook.
4. **Cashier**: POS checkout, receipt generation, incoming payment logging (Read-only on cost prices).
5. **Seller**: Restricted strictly to own seller product catalog and order dispatch.

### B. Multi-Tenancy Boundary Enforcement
Every query executed in Django views and FastAPI routes enforces company tenancy:
```python
queryset = Sale.objects.filter(company=request.user.active_company)
```

---

## 3. Defense Against Common Vulnerabilities

| Threat | Mitigation Mechanism in BizFlow |
|---|---|
| **SQL Injection** | Exclusively parameterized queries executed via Django ORM. Raw string formatting in SQL is strictly prohibited. |
| **Cross-Site Scripting (XSS)** | Django template auto-escaping enabled by default; Pydantic and Django forms sanitize incoming HTML entities. |
| **CSRF Attacks** | Django CSRF token middleware enforced on all state-altering POST/PUT/DELETE forms. |
| **Brute Force Attacks** | Rate-limiting middleware and lockout mechanisms on `/accounts/login/` and `/api/v1/auth/login`. |
| **Path Traversal** | Filename sanitization via `os.path.basename` on all uploaded file attachments. |
| **Information Leakage** | Production setting `DEBUG = False`; custom error pages (403, 404, 500) hide stack traces. Sensitive log fields masked via `SensitiveDataFilter`. |

---

## 4. Audit Logging (`apps.audit.models.AuditLog`)
Every critical business action (password change, user promotion, large credit sale, payment voucher, manual stock adjustment) creates an immutable audit log recording:
- `user`: Authenticated operator
- `module`: Target subsystem (`Sales`, `Inventory`, `Credit`, `Auth`)
- `action`: Specific operation (`CREATE`, `UPDATE`, `VOID`)
- `ip_address` & `user_agent`: Client network signature
- `old_values` & `new_values`: JSON delta representation
- `timestamp`: UTC creation time
