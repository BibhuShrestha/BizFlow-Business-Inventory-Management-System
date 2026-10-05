# MIGRATION MAP — Flask → Django + FastAPI

> **Generated:** Part 1 — Inspect & Analyze  
> **Source project:** `e:/project/business` (Flask 2.3.3)  
> **Target project:** To be created in a separate folder (Django + FastAPI)

---

## Legend

| Column | Meaning |
|---|---|
| Flask Feature | Human-readable feature name |
| Flask Location | File/blueprint in the existing Flask project |
| Business Requirement | What the feature does in business terms |
| New Django App | The Django application that will own this domain |
| Django Model | Proposed Django ORM model name |
| Shared Service | Pure-Python service module (framework-agnostic) |
| FastAPI Endpoint | Proposed REST API path served by FastAPI |
| Web/UI | Django template view that serves the HTML UI |
| Migration Status | See MIGRATION_STATUS.md |
| Notes | Decisions, gotchas, obsolete patterns |

---

## 1. Authentication & Identity

| Flask Feature | Flask Location | Business Requirement | New Django App | Django Model | Shared Service | FastAPI Endpoint | Web/UI | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Email/password login | `app/auth/routes.py` → `login` | Authenticate staff/admin/customers | `accounts` | `User` | `services/auth_service.py` | `POST /api/v1/auth/token` | `accounts/login.html` | [ ] | Flask-Login → Django `AuthenticationBackend`; JWT for FastAPI |
| Google OAuth login | `app/auth/routes.py` → `google_login`, `google_callback` | Social login via Google account | `accounts` | `User` | `services/auth_service.py` | `GET /api/v1/auth/google` | `accounts/login.html` | [ ] | Use `python-social-auth` or `allauth` in Django |
| User registration | `app/auth/routes.py` → `register` | Self-registration with email verification | `accounts` | `User`, `EmailVerificationToken` | `services/auth_service.py` | `POST /api/v1/auth/register` | `accounts/register.html` | [ ] | Email verification token flow must be preserved |
| Email verification | `app/auth/routes.py` → `verify_email` | Activate account via tokenized link | `accounts` | `EmailVerificationToken` | `services/token_service.py` | `GET /api/v1/auth/verify-email/{token}` | redirect | [ ] | SHA-256 hashed token; 60-minute expiry |
| Logout | `app/auth/routes.py` → `logout` | End user session | `accounts` | — | — | `POST /api/v1/auth/logout` | redirect | [ ] | Blacklist JWT on logout for FastAPI |
| Forgot password | `app/auth/routes.py` → `forgot_password` | Request password reset email | `accounts` | `PasswordResetToken` | `services/token_service.py` | `POST /api/v1/auth/forgot-password` | `accounts/forgot_password.html` | [ ] | 30-minute expiry |
| Reset password | `app/auth/routes.py` → `reset_password` | Set new password via token link | `accounts` | `PasswordResetToken` | `services/token_service.py` | `POST /api/v1/auth/reset-password/{token}` | `accounts/reset_password.html` | [ ] | |
| Change password | `app/auth/routes.py` → `change_password` | In-session password change | `accounts` | `User` | `services/auth_service.py` | `PUT /api/v1/auth/change-password` | `accounts/change_password.html` | [ ] | Requires current password verification |
| Edit profile | `app/auth/routes.py` → `profile` | Update name, email, phone | `accounts` | `User` | — | `PUT /api/v1/users/me` | `accounts/profile.html` | [ ] | Email change triggers re-verification |
| Request re-verification | `app/auth/routes.py` → `request_email_verification` | Resend verification email | `accounts` | `EmailVerificationToken` | `services/token_service.py` | `POST /api/v1/auth/resend-verification` | redirect | [ ] | |
| Switch active company | `app/auth/routes.py` → `switch_company` | Set current active business context | `accounts` | `User` | — | `PUT /api/v1/users/me/active-company` | redirect | [ ] | `active_company_id` FK on User |
| Password strength rules | `app/auth/forms.py` → `validate_password_rules` | Enforce min 8/upper/lower/digit/special | `accounts` | — | `services/validators.py` | shared validator | shared | [ ] | Extract to pure-Python validator; reuse in Django + FastAPI |
| Audit log on auth events | `app/auth/routes.py` (inline) | Record login/logout/failed attempts | `audit` | `AuditLog` | `services/audit_service.py` | — | — | [ ] | Currently duplicated inline; centralize |

---

## 2. User Management

| Flask Feature | Flask Location | Business Requirement | New Django App | Django Model | Shared Service | FastAPI Endpoint | Web/UI | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|
| List all users | `app/users/routes.py` → `index` | Admin view of all system users | `accounts` | `User` | — | `GET /api/v1/users` | `accounts/users/index.html` | [ ] | Admin-only |
| Create user | `app/users/routes.py` → `create_user` | Admin creates new accounts | `accounts` | `User` | `services/auth_service.py` | `POST /api/v1/users` | `accounts/users/form.html` | [ ] | |
| Edit user | `app/users/routes.py` → `edit_user` | Admin edits user details and role | `accounts` | `User`, `Role` | — | `PUT /api/v1/users/{id}` | `accounts/users/form.html` | [ ] | |
| Toggle user status | `app/users/routes.py` → `toggle_status` | Activate/deactivate user account | `accounts` | `User` | — | `PATCH /api/v1/users/{id}/status` | redirect | [ ] | |
| Delete user | `app/users/routes.py` → `delete_user` | Remove user account | `accounts` | `User` | — | `DELETE /api/v1/users/{id}` | redirect | [ ] | Admin-only |

---

## 3. Roles & Permissions

| Flask Feature | Flask Location | Business Requirement | New Django App | Django Model | Shared Service | FastAPI Endpoint | Web/UI | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Role model | `app/models/role.py` | 4 system roles: admin, manager, staff, customer | `accounts` | `Role` | — | — | — | [ ] | Seeded on startup |
| `admin_required` decorator | `app/utils/decorators.py` | Restrict views to admin only | `accounts` | — | `services/permissions.py` | FastAPI `Depends` | Django `@permission_required` | [ ] | |
| `manager_required` decorator | `app/utils/decorators.py` | Restrict to admin + manager | `accounts` | — | `services/permissions.py` | FastAPI `Depends` | Django `@permission_required` | [ ] | |
| `staff_required` decorator | `app/utils/decorators.py` | Restrict to admin + manager + staff | `accounts` | — | `services/permissions.py` | FastAPI `Depends` | Django `@permission_required` | [ ] | customer = read-only |

---

## 4. Dashboard

| Flask Feature | Flask Location | Business Requirement | New Django App | Django Model | Shared Service | FastAPI Endpoint | Web/UI | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Landing page | `app/dashboard/routes.py` → `home` | Public marketing page | `core` | — | — | — | `core/landing.html` | [ ] | |
| Main dashboard | `app/dashboard/routes.py` → `index` | KPI summary: sales, purchases, stock | `core` | — | `services/dashboard_service.py` | `GET /api/v1/dashboard/summary` | `core/dashboard.html` | [ ] | |
| Admin dashboard | `app/dashboard/routes.py` → `admin_dashboard` | Extended admin KPIs | `core` | — | `services/dashboard_service.py` | `GET /api/v1/dashboard/admin` | `core/dashboard_admin.html` | [ ] | |
| Date conversion API | `app/dashboard/routes.py` → `convert_date` | AD ↔ BS (Bikram Sambat) conversion | `core` | — | `services/nepali_date_service.py` | `GET /api/v1/utils/convert-date` | AJAX | [ ] | |
| Nepali date Jinja filters | `app/__init__.py` | Format dates as BS in templates | `core` | — | `services/nepali_date_service.py` | — | Django template filter | [ ] | |

---

## 5. Companies

| Flask Feature | Flask Location | Business Requirement | New Django App | Django Model | Shared Service | FastAPI Endpoint | Web/UI | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|
| List companies | `app/companies/routes.py` → `index` | Browse and search company records | `companies` | `Company` | — | `GET /api/v1/companies` | `companies/index.html` | [ ] | Search by name, phone, VAT/PAN |
| Create company | `app/companies/routes.py` → `create_company` | Register new business entity | `companies` | `Company` | — | `POST /api/v1/companies` | `companies/form.html` | [ ] | Manager-required |
| Edit company | `app/companies/routes.py` → `edit_company` | Update company profile | `companies` | `Company` | — | `PUT /api/v1/companies/{id}` | `companies/form.html` | [ ] | |
| Company detail | `app/companies/routes.py` → `detail` | View company with sellers and products | `companies` | `Company`, `Seller`, `Product` | — | `GET /api/v1/companies/{id}` | `companies/detail.html` | [ ] | |
| Delete company | `app/companies/routes.py` → `delete_company` | Remove company, cascade sellers | `companies` | `Company` | — | `DELETE /api/v1/companies/{id}` | redirect | [ ] | |
| Upload company logo | `app/companies/routes.py` → `upload_logo` | Attach image logo | `companies` | `Company` | `services/file_service.py` | `POST /api/v1/companies/{id}/logo` | redirect | [ ] | Django `MEDIA_ROOT` instead of `static/uploads/` |
| Export CSV | `app/companies/routes.py` → `export_csv` | Download CSV | `companies` | `Company` | `services/export_service.py` | `GET /api/v1/companies/export?format=csv` | download | [ ] | |
| Export Excel | `app/companies/routes.py` → `export_excel` | Download XLSX | `companies` | `Company` | `services/export_service.py` | `GET /api/v1/companies/export?format=xlsx` | download | [ ] | |
| Import CSV/XLSX | `app/companies/routes.py` → `import_companies` | Bulk-import companies | `companies` | `Company` | `services/import_service.py` | `POST /api/v1/companies/import` | `import_upload.html` | [ ] | Upsert by company name |
| Sample template | `app/companies/routes.py` → `sample_template` | Download import template | `companies` | — | `services/export_service.py` | `GET /api/v1/companies/import/template` | download | [ ] | |

---

## 6. Sellers

| Flask Feature | Flask Location | Business Requirement | New Django App | Django Model | Shared Service | FastAPI Endpoint | Web/UI | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|
| List sellers | `app/sellers/routes.py` → `index` | Browse sellers with company filter | `companies` | `Seller` | — | `GET /api/v1/sellers` | `sellers/index.html` | [ ] | |
| Create seller | `app/sellers/routes.py` → `create_seller` | Register a seller representative | `companies` | `Seller` | — | `POST /api/v1/sellers` | `sellers/form.html` | [ ] | Manager-required |
| Edit seller | `app/sellers/routes.py` → `edit_seller` | Update seller details | `companies` | `Seller` | — | `PUT /api/v1/sellers/{id}` | `sellers/form.html` | [ ] | |
| Delete seller | `app/sellers/routes.py` → `delete_seller` | Remove seller record | `companies` | `Seller` | — | `DELETE /api/v1/sellers/{id}` | redirect | [ ] | |
| Export/Import sellers | `app/sellers/routes.py` | CSV/XLSX export and bulk import | `companies` | `Seller` | `services/export_service.py` | `GET /api/v1/sellers/export`, `POST /api/v1/sellers/import` | download | [ ] | |

---

## 7. Products & Categories

| Flask Feature | Flask Location | Business Requirement | New Django App | Django Model | Shared Service | FastAPI Endpoint | Web/UI | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|
| List products | `app/products/routes.py` → `index` | Browse product catalog | `inventory` | `Product` | — | `GET /api/v1/products` | `inventory/products/index.html` | [ ] | Visible to customers |
| Create product | `app/products/routes.py` → `create_product` | Add new product | `inventory` | `Product` | — | `POST /api/v1/products` | `inventory/products/form.html` | [ ] | |
| Edit product | `app/products/routes.py` → `edit_product` | Update product details and pricing | `inventory` | `Product` | — | `PUT /api/v1/products/{id}` | `inventory/products/form.html` | [ ] | |
| Category management | `app/products/routes.py` → `categories` | Create/list product categories | `inventory` | `Category` | — | `GET /api/v1/categories`, `POST /api/v1/categories` | `inventory/categories.html` | [ ] | |
| Export/Import products | `app/products/routes.py` | CSV/XLSX export and bulk import | `inventory` | `Product` | `services/export_service.py` | `GET /api/v1/products/export`, `POST /api/v1/products/import` | download | [ ] | |
| `stock_value` property | `app/models/product.py` | `current_stock × purchase_price` | `inventory` | `Product` | model property | — | — | [ ] | Keep as Django model property |

---

## 8. Inventory & Stock Movements

| Flask Feature | Flask Location | Business Requirement | New Django App | Django Model | Shared Service | FastAPI Endpoint | Web/UI | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Stock movement list | `app/inventory/routes.py` → `index` | History of all IN/OUT movements | `inventory` | `StockMovement` | — | `GET /api/v1/inventory/movements` | `inventory/index.html` | [ ] | Staff-required |
| Manual adjustment | `app/inventory/routes.py` → `adjust_stock` | Manually adjust product stock count | `inventory` | `StockMovement`, `Product` | `services/stock_service.py` | `POST /api/v1/inventory/adjust` | `inventory/adjust.html` | [ ] | Manager-required |
| Auto stock on sale | `app/sales/routes.py` (inline) | Decrease stock on sale creation | `inventory` | `StockMovement` | `services/stock_service.py` | — | — | [ ] | Currently embedded; must be extracted to service |
| Auto stock on purchase | `app/purchases/routes.py` (inline) | Increase stock on purchase creation | `inventory` | `StockMovement` | `services/stock_service.py` | — | — | [ ] | Currently embedded; must be extracted |
| Stock reversal on delete | `app/sales/routes.py`, `purchases/routes.py` | Reverse stock on cancellation | `inventory` | `StockMovement` | `services/stock_service.py` | — | — | [ ] | |

---

## 9. Customers

| Flask Feature | Flask Location | Business Requirement | New Django App | Django Model | Shared Service | FastAPI Endpoint | Web/UI | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|
| List customers | `app/customers/routes.py` → `index` | Browse customer directory | `sales` | `Customer` | — | `GET /api/v1/customers` | `sales/customers/index.html` | [ ] | |
| Create customer | `app/customers/routes.py` → `create_customer` | Register customer with credit info | `sales` | `Customer` | — | `POST /api/v1/customers` | `sales/customers/form.html` | [ ] | Includes opening balance and credit limit |
| Edit customer | `app/customers/routes.py` → `edit_customer` | Update customer details | `sales` | `Customer` | — | `PUT /api/v1/customers/{id}` | `sales/customers/form.html` | [ ] | |

---

## 10. Suppliers

| Flask Feature | Flask Location | Business Requirement | New Django App | Django Model | Shared Service | FastAPI Endpoint | Web/UI | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|
| List suppliers | `app/suppliers/routes.py` → `index` | Browse supplier directory | `purchases` | `Supplier` | — | `GET /api/v1/suppliers` | `purchases/suppliers/index.html` | [ ] | |
| Create supplier | `app/suppliers/routes.py` → `create_supplier` | Register supplier with opening balance | `purchases` | `Supplier` | — | `POST /api/v1/suppliers` | `purchases/suppliers/form.html` | [ ] | |
| Edit supplier | `app/suppliers/routes.py` → `edit_supplier` | Update supplier details | `purchases` | `Supplier` | — | `PUT /api/v1/suppliers/{id}` | `purchases/suppliers/form.html` | [ ] | |

---

## 11. Sales

| Flask Feature | Flask Location | Business Requirement | New Django App | Django Model | Shared Service | FastAPI Endpoint | Web/UI | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|
| List sales | `app/sales/routes.py` → `index` | Browse sales invoices | `sales` | `Sale` | — | `GET /api/v1/sales` | `sales/index.html` | [ ] | Staff-required |
| Create sale | `app/sales/routes.py` → `create_sale` | Record multi-line sales invoice | `sales` | `Sale`, `SaleItem` | `services/sales_service.py` | `POST /api/v1/sales` | `sales/form.html` | [ ] | Decrements stock; cheque/cash/QR payment |
| Sale detail | `app/sales/routes.py` → `detail` | View invoice with line items | `sales` | `Sale`, `SaleItem` | — | `GET /api/v1/sales/{id}` | `sales/detail.html` | [ ] | |
| Delete sale | `app/sales/routes.py` → `delete_sale` | Cancel sale and restore stock | `sales` | `Sale`, `StockMovement` | `services/sales_service.py` | `DELETE /api/v1/sales/{id}` | redirect | [ ] | Manager-required |

---

## 12. Purchases

| Flask Feature | Flask Location | Business Requirement | New Django App | Django Model | Shared Service | FastAPI Endpoint | Web/UI | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|
| List purchases | `app/purchases/routes.py` → `index` | Browse purchase orders | `purchases` | `Purchase` | — | `GET /api/v1/purchases` | `purchases/index.html` | [ ] | Staff-required |
| Create purchase | `app/purchases/routes.py` → `create_purchase` | Record multi-line purchase order | `purchases` | `Purchase`, `PurchaseItem` | `services/purchase_service.py` | `POST /api/v1/purchases` | `purchases/form.html` | [ ] | Increments stock; cheque support |
| Purchase detail | `app/purchases/routes.py` → `detail` | View PO with line items | `purchases` | `Purchase`, `PurchaseItem` | — | `GET /api/v1/purchases/{id}` | `purchases/detail.html` | [ ] | |
| Delete purchase | `app/purchases/routes.py` → `delete_purchase` | Cancel PO and reverse stock | `purchases` | `Purchase`, `StockMovement` | `services/purchase_service.py` | `DELETE /api/v1/purchases/{id}` | redirect | [ ] | Manager-required |

---

## 13. Payments

| Flask Feature | Flask Location | Business Requirement | New Django App | Django Model | Shared Service | FastAPI Endpoint | Web/UI | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Payment recording | `app/models/payment.py` | Record Cash, Cheque, QR transactions | `sales`, `purchases` | `Payment` | `services/payment_service.py` | `POST /api/v1/payments` | — | [ ] | Linked to Sale OR Purchase |
| Cheque payment fields | `app/models/payment.py` | `cheque_number`, `cheque_date`, `bank_name` | — | `Payment` | — | — | — | [ ] | Preserve on model |
| QR payment reference | `app/models/payment.py` | `qr_reference` field | — | `Payment` | — | — | — | [ ] | |
| Payment status on documents | `app/models/sale.py`, `purchase.py` | `payment_status`: Due/Paid/Partial | `sales`, `purchases` | `Sale`, `Purchase` | — | — | — | [ ] | |

---

## 14. Expenses

| Flask Feature | Flask Location | Business Requirement | New Django App | Django Model | Shared Service | FastAPI Endpoint | Web/UI | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|
| List expenses | `app/expenses/routes.py` → `index` | Browse business expense records | `accounting` | `Expense` | — | `GET /api/v1/expenses` | `accounting/expenses/index.html` | [ ] | Manager-required |
| Create expense | `app/expenses/routes.py` → `create_expense` | Record a business expense | `accounting` | `Expense` | — | `POST /api/v1/expenses` | `accounting/expenses/form.html` | [ ] | Expense category is free-text |

---

## 15. Accounting (Journal)

| Flask Feature | Flask Location | Business Requirement | New Django App | Django Model | Shared Service | FastAPI Endpoint | Web/UI | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Chart of accounts | `app/models/accounting.py` → `Account` | Ledger accounts with code | `accounting` | `Account` | — | `GET /api/v1/accounts` | — | [ ] | **No UI route exists** — model only |
| Journal entry | `app/models/accounting.py` → `JournalEntry` | Double-entry bookkeeping | `accounting` | `JournalEntry` | `services/accounting_service.py` | `POST /api/v1/journal-entries` | — | [ ] | **Blueprint folder is empty** |
| Journal entry item | `app/models/accounting.py` → `JournalEntryItem` | Debit/credit line on entry | `accounting` | `JournalEntryItem` | — | — | — | [ ] | |

---

## 16. Reports

| Flask Feature | Flask Location | Business Requirement | New Django App | Django Model | Shared Service | FastAPI Endpoint | Web/UI | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Business summary report | `app/reports/routes.py` → `index` | Total sales, purchases, expenses, net profit | `reports` | — | `services/report_service.py` | `GET /api/v1/reports/summary` | `reports/index.html` | [ ] | Manager-required |
| Day Book | `app/reports/routes.py` → `daybook` | All transactions for a selected date | `reports` | — | `services/report_service.py` | `GET /api/v1/reports/daybook?date=YYYY-MM-DD` | `reports/daybook.html` | [ ] | |

---

## 17. Notifications

| Flask Feature | Flask Location | Business Requirement | New Django App | Django Model | Shared Service | FastAPI Endpoint | Web/UI | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Notification model | `app/models/notification.py` | In-app notifications per user | `core` | `Notification` | — | `GET /api/v1/notifications` | — | [ ] | **Blueprint folder exists but is empty** — no routes yet |

---

## 18. Audit Logging

| Flask Feature | Flask Location | Business Requirement | New Django App | Django Model | Shared Service | FastAPI Endpoint | Web/UI | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Audit log | `app/models/audit_log.py` | Who did what, when, before/after JSON | `audit` | `AuditLog` | `services/audit_service.py` | `GET /api/v1/audit-logs` | — | [ ] | **Blueprint empty** — currently logged inline per route |
| Login history | `app/models/login_history.py` | Record login attempts (IP, method) | `audit` | `LoginHistory` | `services/audit_service.py` | `GET /api/v1/login-history` | — | [ ] | Model exists but **no route writes to it** |

---

## 19. Email

| Flask Feature | Flask Location | Business Requirement | New Django App | Django Model | Shared Service | FastAPI Endpoint | Web/UI | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Send email | `app/auth/services.py` → `send_email` | Generic SMTP dispatch | `accounts` | — | `services/email_service.py` | — | — | [ ] | Flask-Mail → Django `send_mail` or `anymail` |
| Verification email | `app/auth/services.py` | Send verification link | `accounts` | `EmailVerificationToken` | `services/email_service.py` | — | — | [ ] | |
| Reset email | `app/auth/services.py` | Send password reset link | `accounts` | `PasswordResetToken` | `services/email_service.py` | — | — | [ ] | |
| Email log model | `app/models/email_log.py` | Record every outgoing email | `accounts` | `EmailLog` | `services/email_service.py` | — | — | [ ] | Exists but **no route writes to it** |

---

## 20. File Uploads & Exports

| Flask Feature | Flask Location | Business Requirement | New Django App | Django Model | Shared Service | FastAPI Endpoint | Web/UI | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Company logo upload | `app/companies/routes.py` → `handle_logo_upload` | Save PNG/JPG/SVG/WEBP image | `companies` | `Company` | `services/file_service.py` | `POST /api/v1/companies/{id}/logo` | — | [ ] | Flask `static/uploads/` → Django `MEDIA_ROOT` |
| CSV export utility | `app/utils/excel_csv.py` → `generate_csv_response` | Generate CSV download | shared | — | `services/export_service.py` | — | — | [ ] | |
| Excel export utility | `app/utils/excel_csv.py` → `generate_excel_response` | Generate styled XLSX download | shared | — | `services/export_service.py` | — | — | [ ] | Uses openpyxl |
| File upload parser | `app/utils/excel_csv.py` → `parse_uploaded_file` | Parse CSV or XLSX to row dicts | shared | — | `services/import_service.py` | — | — | [ ] | |
| Export log model | `app/models/export_log.py` | Record every export operation | shared | `ExportLog` | `services/export_service.py` | — | — | [ ] | Exists but **no route writes to it** |

---

## 21. Configuration

| Flask Feature | Flask Location | Business Requirement | New Django App | Django Model | Shared Service | FastAPI Endpoint | Web/UI | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Base config | `config.py` → `BaseConfig` | DB URL, SECRET_KEY, mail, Google OAuth, AI key | — | — | — | — | — | [ ] | Move to Django `settings.py` + env vars |
| Dev / Prod / Testing configs | `config.py` | Environment-specific settings | — | — | — | — | — | [ ] | Django settings modules pattern |
| Security headers middleware | `app/__init__.py` → `set_secure_headers` | X-Frame-Options, CSP, Referrer-Policy etc. | — | — | — | — | Django middleware | [ ] | Use `django-csp` or custom middleware |
| Auto-migrate columns | `app/__init__.py` | Runtime `ALTER TABLE` statements | — | — | — | — | — | [!] | **Obsolete** — Django migrations handle this |
| Auto-seed roles | `app/__init__.py` | Seed 4 roles if not present | `accounts` | `Role` | — | — | Data migration | [ ] | Use Django data migration |
| First-user-to-admin startup | `app/__init__.py` | Promote first user to admin on startup | `accounts` | `User` | — | — | — | [!] | **Fragile** — replace with `createsuperuser` |

---

## 22. Cross-Cutting / Shared

| Flask Feature | Flask Location | Business Requirement | New Django App | Django Model | Shared Service | FastAPI Endpoint | Web/UI | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Active company context processor | `app/__init__.py` → `inject_active_company` | Inject company into all templates | `core` | — | — | — | Django context processor | [ ] | |
| Nepali date conversion | `app/__init__.py` → `to_nepali_date/datetime` | Display BS calendar dates | `core` | — | `services/nepali_date_service.py` | — | Template filter | [ ] | Locale requirement; must be preserved |
| Health check | `app/__init__.py` → `/health` | Return app + DB status JSON | `core` | — | — | `GET /api/v1/health` | — | [ ] | |
| Error pages | `app/__init__.py` + `templates/errors/` | 400/401/403/404/429/500 pages | `core` | — | — | FastAPI exception handlers | Django error templates | [ ] | |

---

## 23. Obsolete / Tech Debt

| Item | Flask Location | Issue | Recommendation |
|---|---|---|---|
| Inline `ALTER TABLE` auto-migration | `app/__init__.py` | Runtime schema changes; errors silently swallowed | **Remove** — Django migrations handle this |
| Inline audit logging | Auth routes, etc. | `AuditLog` creation duplicated across many route functions | Centralize in `services/audit_service.py` + Django signals |
| `admin_required` defined twice | `app/dashboard/routes.py` AND `app/utils/decorators.py` | Duplicate with different implementation | Use only the shared decorator from `utils/decorators.py` |
| Empty blueprint folders | `app/ai/`, `app/accounting/`, `app/notifications/`, `app/payments/`, `app/audit/`, `app/email/` | Models exist, no routes | Decide: implement or remove |
| `LoginHistory` model | `app/models/login_history.py` | Model exists; **no route ever writes to it** | Wire up in new auth service |
| `ExportLog` model | `app/models/export_log.py` | Model exists; **no route ever writes to it** | Wire up in export service |
| `Account`, `JournalEntry`, `JournalEntryItem` | `app/models/accounting.py` | Models exist; no routes or UI at all | Build accounting module or mark as future scope |
| `AI_API_KEY` config | `config.py` | Config key present; `app/ai/` is empty | Design AI feature scope before migration |
| First-user-to-admin startup check | `app/__init__.py` | Fragile on multi-process deploy | Replace with `manage.py createsuperuser` |

---

*See [MIGRATION_STATUS.md](MIGRATION_STATUS.md) for current progress tracking.*
