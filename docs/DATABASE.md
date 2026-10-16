# Database Architecture & Schema Documentation

> **Target Database Design & Migration Foundation for BizFlow**  
> Complete schema specification, entity relationships, integrity constraints, and legacy mapping.

---

## 1. Overview & Architectural Principles

BizFlow utilizes **Django ORM** as the unified data access and schema management layer for both the Django Web UI and the FastAPI REST layer.
The schema is database-agnostic:
- **Local Development**: SQLite (`inventory.db`) with zero setup overhead.
- **Automated Testing**: In-memory SQLite (`:memory:`) executing test suites in under a second.
- **Production Support**: **PostgreSQL 14+** and **MySQL 8.0** configured dynamically via `DATABASE_URL`.

### Universal Model Conventions:
1. **Primary Keys**: Standard auto-incrementing integer / 64-bit BigAutoField primary keys (`id`).
2. **Timestamps**: Timezone-aware audit fields (`created_at` via `auto_now_add=True`, `updated_at` via `auto_now=True`).
3. **Multi-Tenant Isolation**: High-frequency business models store an indexed foreign key to `companies.Company`.
4. **Referential Integrity**: Explicit `on_delete` policies (`CASCADE`, `SET_NULL`, `RESTRICT`) matching business rules.
5. **Exact Monetary Storage**: All financial and tax figures use `DecimalField` (e.g. `max_digits=14, decimal_places=2`) to guarantee zero floating-point roundoff errors.

---

## 2. Entity Relationship Overview

```
[ Role ] 1 ──◄ N [ User ] ◄────────────── (created_by) ──────────────┐
                   │                                                  │
                   ├── (active_company) ──► [ Company ] 1 ──◄ N [ Seller ]
                   │                             │                    │
                   ├── 1 ──◄ N [ LoginHistory ]  ├── 1 ──◄ N [ Customer ] 1 ──◄ N [ Sale ] 1 ──◄ N [ SaleItem ] ──► [ Product ]
                   ├── 1 ──◄ N [ EmailToken ]    ├── 1 ──◄ N [ Supplier ] 1 ──◄ N [ Purchase ] 1 ──◄ N [ PurchaseItem ] ──► [ Product ]
                   ├── 1 ──◄ N [ PasswordToken ] ├── 1 ──◄ N [ Expense ]             ▲             ▲
                   ├── 1 ──◄ N [ Notification ]  └── 1 ──◄ N [ Product ] 1 ──◄ N [ StockMovement ] │
                   └── 1 ──◄ N [ AuditLog ]                    │                     │             │
                                                               └── N ──► 1 [ Category ]             │
                                                                                     │             │
                                                                           1 ──◄ N [ Payment ] ────┘
```

---

## 3. Legacy Flask Model to New Django Model Mapping

| # | Flask Model (`app/models/`) | Legacy Table | Target Django App | Target Django Model | Target DB Table | Business Purpose |
|---|---|---|---|---|---|---|
| 1 | `role.py` | `roles` | `apps.accounts` | `Role` | `roles` | Role-based authorization (`admin`, `manager`, `staff`, `customer`). |
| 2 | `user.py` | `users` | `apps.accounts` | `User` | `users` | User identity, email authentication, and company context. |
| 3 | `email_verification_token.py` | `email_verification_tokens` | `apps.accounts` | `EmailVerificationToken` | `email_verification_tokens` | 60-min activation tokens with SHA-256 hash. |
| 4 | `password_reset_token.py` | `password_reset_tokens` | `apps.accounts` | `PasswordResetToken` | `password_reset_tokens` | 30-min secure tokens for forgotten credentials. |
| 5 | `login_history.py` | `login_history` | `apps.accounts` | `LoginHistory` | `login_history` | Audit trail of IP addresses, devices, and auth success. |
| 6 | `company.py` | `companies` | `apps.companies` | `Company` | `companies` | Multi-tenant company profiles, tax PAN, and logos. |
| 7 | `seller.py` | `sellers` | `apps.companies` | `Seller` | `sellers` | Sales agents and representatives under companies. |
| 8 | `category.py` | `categories` | `apps.inventory` | `Category` | `categories` | Product classification groups. |
| 9 | `product.py` | `products` | `apps.inventory` | `Product` | `products` | Catalog items with SKU, unit, pricing, and stock. |
| 10 | `stock.py` (`StockMovement`) | `stock_movements` | `apps.inventory` | `StockMovement` | `stock_movements` | Immutable ledger of all IN/OUT inventory flows. |
| 11 | `stock.py` (`StockAdjustment`) | `stock_adjustments` | `apps.inventory` | `StockAdjustment` | `stock_adjustments` | Manual stock count adjustments with justification. |
| 12 | `customer.py` | `customers` | `apps.sales` | `Customer` | `customers` | Customer directories, credit limits, opening balances. |
| 13 | `sale.py` | `sales` | `apps.sales` | `Sale` | `sales` | Sales invoices, discounts, taxes, and payment status. |
| 14 | `sale_item.py` | `sale_items` | `apps.sales` | `SaleItem` | `sale_items` | Individual line items on a customer sales invoice. |
| 15 | `payment.py` | `payments` | `apps.sales` | `Payment` | `payments` | Cash/Bank/Cheque payment vouchers linked to sales/purchases. |
| 16 | `supplier.py` | `suppliers` | `apps.purchases` | `Supplier` | `suppliers` | Vendor directory with credit and contact records. |
| 17 | `purchase.py` | `purchases` | `apps.purchases` | `Purchase` | `purchases` | Purchase invoices from suppliers with tax details. |
| 18 | `purchase_item.py` | `purchase_items` | `apps.purchases` | `PurchaseItem` | `purchase_items` | Individual product items received on a purchase bill. |
| 19 | `expense.py` | `expenses` | `apps.accounting` | `Expense` | `expenses` | Operational expenses categorized and allocated. |
| 20 | `accounting.py` (`Account`) | `accounts` | `apps.accounting` | `Account` | `accounts` | Chart of Accounts ledger codes. |
| 21 | `accounting.py` (`JournalEntry`) | `journal_entries` | `apps.accounting` | `JournalEntry` | `journal_entries` | General Journal transaction headers. |
| 22 | `accounting.py` (`JournalEntryItem`) | `journal_entry_items` | `apps.accounting` | `JournalEntryItem` | `journal_entry_items` | Double-entry debit/credit ledger lines. |
| 23 | `audit_log.py` | `audit_logs` | `apps.audit` | `AuditLog` | `audit_logs` | System security events, modifications, and diffs. |
| 24 | `notification.py` | `notifications` | `apps.audit` | `Notification` | `notifications` | In-app user notifications and alerts. |
| 25 | `email_log.py` | `email_logs` | `apps.audit` | `EmailLog` | `email_logs` | Dispatched SMTP notification tracking. |
| 26 | `export_log.py` | `export_logs` | `apps.audit` | `ExportLog` | `export_logs` | History of downloaded Excel, PDF, and CSV files. |

---

## 4. Detailed Table Specifications

### 4.1 `apps.accounts`
- **`roles`**:
  - `id` (PK), `name` (VARCHAR(64), UNIQUE, INDEXED), `description` (VARCHAR(255)).
- **`users`**:
  - `id` (PK), `email` (VARCHAR(255), UNIQUE, INDEXED), `name` (VARCHAR(128)), `password` (VARCHAR(128)), `phone` (VARCHAR(32)), `is_active` (BOOL), `is_staff` (BOOL), `is_superuser` (BOOL), `email_verified` (BOOL), `google_id` (VARCHAR(255), UNIQUE, NULL), `role_id` (FK -> `roles.id`, SET_NULL), `active_company_id` (FK -> `companies.id`, SET_NULL), `created_at`, `updated_at`.
- **`email_verification_tokens`**:
  - `id` (PK), `user_id` (FK -> `users.id`, CASCADE), `token_hash` (VARCHAR(255), INDEXED), `expires_at` (DATETIME), `used` (BOOL), `created_at`.
- **`password_reset_tokens`**:
  - `id` (PK), `user_id` (FK -> `users.id`, CASCADE), `token_hash` (VARCHAR(255), INDEXED), `expires_at` (DATETIME), `used` (BOOL), `created_at`.
- **`login_history`**:
  - `id` (PK), `user_id` (FK -> `users.id`, SET_NULL), `timestamp`, `ip_address` (VARCHAR(64)), `user_agent` (VARCHAR(255)), `method` (VARCHAR(64)), `success` (BOOL), `message` (VARCHAR(255)).

### 4.2 `apps.companies`
- **`companies`**:
  - `id` (PK), `company_name` (VARCHAR(255), INDEXED), `company_phone` (VARCHAR(32), INDEXED), `vat_pan_number` (VARCHAR(64), INDEXED), `address` (TEXT), `logo_url` (VARCHAR(255)), `created_at`, `updated_at`.
- **`sellers`**:
  - `id` (PK), `seller_name` (VARCHAR(255), INDEXED), `seller_phone` (VARCHAR(32), INDEXED), `company_id` (FK -> `companies.id`, SET_NULL), `created_at`, `updated_at`.

### 4.3 `apps.inventory`
- **`categories`**:
  - `id` (PK), `name` (VARCHAR(128), UNIQUE, INDEXED), `description` (VARCHAR(255)), `is_active` (BOOL), `created_at`, `updated_at`.
- **`products`**:
  - `id` (PK), `sku` (VARCHAR(64), UNIQUE, INDEXED), `name` (VARCHAR(255), INDEXED), `category_id` (FK -> `categories.id`, RESTRICT), `company_id` (FK -> `companies.id`, SET_NULL), `seller_id` (FK -> `sellers.id`, SET_NULL), `unit` (VARCHAR(32)), `purchase_price` (DECIMAL(12,2)), `selling_price` (DECIMAL(12,2)), `tax_rate` (DECIMAL(5,2)), `minimum_stock` (INT), `current_stock` (INT), `description` (TEXT), `is_active` (BOOL), `created_at`, `updated_at`.
- **`stock_movements`**:
  - `id` (PK), `product_id` (FK -> `products.id`, CASCADE), `movement_type` (VARCHAR(32): IN/OUT), `quantity` (INT), `reference_type` (VARCHAR(64)), `reference_id` (INT, NULL), `description` (TEXT), `created_at`.
- **`stock_adjustments`**:
  - `id` (PK), `product_id` (FK -> `products.id`, CASCADE), `adjustment_type` (VARCHAR(16)), `quantity` (INT), `reason` (TEXT), `adjusted_by_id` (FK -> `users.id`, SET_NULL), `created_at`.

### 4.4 `apps.sales`
- **`customers`**:
  - `id` (PK), `name` (VARCHAR(255), INDEXED), `phone` (VARCHAR(32)), `email` (VARCHAR(255), NULL), `address` (TEXT), `opening_balance` (DECIMAL(12,2)), `credit_limit` (DECIMAL(12,2)), `company_id` (FK -> `companies.id`, SET_NULL), `is_active` (BOOL), `created_at`, `updated_at`.
- **`sales`**:
  - `id` (PK), `invoice_number` (VARCHAR(64), UNIQUE, INDEXED), `bill_number` (VARCHAR(64), INDEXED), `customer_id` (FK -> `customers.id`, SET_NULL), `company_id` (FK -> `companies.id`, SET_NULL), `sale_date` (DATETIME), `due_date` (DATE, NULL, INDEXED), `discount` (DECIMAL(12,2)), `tax` (DECIMAL(12,2)), `total` (DECIMAL(14,2)), `payment_status` (VARCHAR(32): Due, Partial, Paid), `payment_method` (VARCHAR(32)), `cheque_number` (VARCHAR(64)), `cheque_date` (DATE), `notes` (TEXT), `is_active` (BOOL), `created_at`, `updated_at`.
  - *Dynamic Properties*: `subtotal`, `paid_amount`, `remaining_amount`, `is_overdue`, `calculated_status`.
- **`sale_items`**:
  - `id` (PK), `sale_id` (FK -> `sales.id`, CASCADE), `product_id` (FK -> `products.id`, RESTRICT), `quantity` (INT), `unit_price` (DECIMAL(12,2)), `tax_rate` (DECIMAL(5,2)), `discount` (DECIMAL(12,2)), `total` (DECIMAL(14,2)), `created_at`.
- **`payments`**:
  - `id` (PK), `payment_date` (DATETIME), `amount` (DECIMAL(14,2)), `payment_method` (VARCHAR(32)), `status` (VARCHAR(32)), `reference` (VARCHAR(255)), `remarks` (TEXT), `notes` (TEXT, NULL), `created_by_id` (FK -> `users.id`, SET_NULL), `cheque_number` (VARCHAR(64)), `cheque_date` (DATETIME), `bank_name` (VARCHAR(128)), `qr_reference` (VARCHAR(255)), `sale_id` (FK -> `sales.id`, SET_NULL), `purchase_id` (FK -> `purchases.id`, SET_NULL), `customer_id` (FK -> `customers.id`, SET_NULL), `supplier_id` (FK -> `suppliers.id`, SET_NULL), `created_at`.
  - *Dynamic Properties*: `display_notes`.

### 4.5 `apps.purchases`
- **`suppliers`**:
  - `id` (PK), `name` (VARCHAR(255), INDEXED), `phone` (VARCHAR(32)), `email` (VARCHAR(255), NULL), `address` (TEXT), `opening_balance` (DECIMAL(12,2)), `company_id` (FK -> `companies.id`, SET_NULL), `is_active` (BOOL), `created_at`, `updated_at`.
- **`purchases`**:
  - `id` (PK), `purchase_number` (VARCHAR(64), UNIQUE, INDEXED), `bill_number` (VARCHAR(64), INDEXED), `supplier_id` (FK -> `suppliers.id`, SET_NULL), `company_id` (FK -> `companies.id`, SET_NULL), `purchase_date` (DATETIME), `due_date` (DATE, NULL, INDEXED), `discount` (DECIMAL(12,2)), `tax` (DECIMAL(12,2)), `total` (DECIMAL(14,2)), `payment_status` (VARCHAR(32)), `payment_method` (VARCHAR(32)), `cheque_number` (VARCHAR(64)), `cheque_date` (DATE), `notes` (TEXT), `is_active` (BOOL), `created_at`, `updated_at`.
  - *Dynamic Properties*: `subtotal`, `paid_amount`, `remaining_amount`, `is_overdue`, `calculated_status`.
- **`purchase_items`**:
  - `id` (PK), `purchase_id` (FK -> `purchases.id`, CASCADE), `product_id` (FK -> `products.id`, RESTRICT), `quantity` (INT), `unit_price` (DECIMAL(12,2)), `discount` (DECIMAL(12,2)), `tax_rate` (DECIMAL(5,2)), `total` (DECIMAL(14,2)), `created_at`.

### 4.6 `apps.accounting`
- **`expense_categories`**:
  - `id` (PK), `name` (VARCHAR(128), UNIQUE, INDEXED), `description` (VARCHAR(255)), `created_at`.
- **`expenses`**:
  - `id` (PK), `category` (VARCHAR(128)), `description` (TEXT), `amount` (DECIMAL(14,2)), `expense_date` (DATETIME), `payment_method` (VARCHAR(32)), `reference` (VARCHAR(255)), `company_id` (FK -> `companies.id`, SET_NULL), `user_id` (FK -> `users.id`, SET_NULL), `created_at`.
- **`accounts`**:
  - `id` (PK), `name` (VARCHAR(128), UNIQUE, INDEXED), `code` (VARCHAR(32), UNIQUE, INDEXED), `description` (VARCHAR(255)), `created_at`.
- **`journal_entries`**:
  - `id` (PK), `entry_date` (DATETIME), `description` (TEXT), `reference_type` (VARCHAR(64)), `reference_id` (INT), `company_id` (FK -> `companies.id`, SET_NULL), `created_at`.
- **`journal_entry_items`**:
  - `id` (PK), `journal_entry_id` (FK -> `journal_entries.id`, CASCADE), `account_id` (FK -> `accounts.id`, RESTRICT), `debit` (DECIMAL(14,2)), `credit` (DECIMAL(14,2)).

### 4.7 `apps.audit`
- **`audit_logs`**:
  - `id` (PK), `user_id` (FK -> `users.id`, SET_NULL), `module` (VARCHAR(128)), `action` (VARCHAR(128)), `record_type` (VARCHAR(64)), `record_id` (INT), `description` (TEXT), `old_values` (JSON), `new_values` (JSON), `ip_address` (VARCHAR(64)), `user_agent` (VARCHAR(255)), `success` (BOOL), `created_at`.
- **`notifications`**:
  - `id` (PK), `user_id` (FK -> `users.id`, CASCADE), `title` (VARCHAR(255)), `message` (TEXT), `link` (VARCHAR(255)), `is_read` (BOOL), `created_at`.
- **`email_logs`**:
  - `id` (PK), `user_id` (FK -> `users.id`, SET_NULL), `recipient` (VARCHAR(255)), `subject` (VARCHAR(255)), `message` (TEXT), `status` (VARCHAR(64)), `created_at`.
- **`export_logs`**:
  - `id` (PK), `user_id` (FK -> `users.id`, SET_NULL), `module` (VARCHAR(128)), `format` (VARCHAR(32)), `filters` (JSON), `record_count` (INT), `success` (BOOL), `created_at`.

---

## 5. Migration Strategy & Data Transformation Rules

1. **Password Hash Compatibility**:
   - Flask uses Werkzeug's `pbkdf2:sha256` or `scrypt` hashing.
   - Django's `PBKDF2PasswordHasher` natively verifies standard PBKDF2-SHA256 hashes (`pbkdf2_sha256$...`).
   - A custom password hasher adapter will verify legacy Werkzeug hashes on first login and automatically upgrade the stored hash to Django Argon2 / PBKDF2 without forcing user password resets.
2. **Date & Time Preservation**:
   - All dates from MySQL `DATETIME` are read in UTC and imported with timezone awareness (`timezone.utc`).
3. **Foreign Key Integrity Verification**:
   - Order of data migration:
     `Roles` ➔ `Companies` ➔ `Users` ➔ `Sellers` ➔ `Categories` ➔ `Products` ➔ `Customers` ➔ `Suppliers` ➔ `Sales` ➔ `Purchases` ➔ `SaleItems` / `PurchaseItems` ➔ `StockMovements` ➔ `Expenses` ➔ `Payments` ➔ `AuditLogs`.

---

## 6. Udhaar / Credit Management Data Schema & Integrity Rules

The Credit Management system is architected to avoid duplicate tables by leveraging the core relational sales, purchase, and payment entities.

### Key Data Invariants:
1. **Due Date Tracking**:
   - Both `sales` and `purchases` include indexed nullable `due_date` columns (`models.DateField(null=True, blank=True, db_index=True)`).
   - Dynamic check `is_overdue = (due_date and date.today() > due_date and remaining_amount > 0)`.
2. **Payment Allocation**:
   - `Payment.sale_id` links customer receivable settlements to a specific sales invoice.
   - `Payment.purchase_id` links supplier payable settlements to a specific purchase bill.
   - `Payment.created_by` links the user responsible for receiving or disbursing funds for audit accountability.
3. **Balance Calculation & Status Transition**:
   - `remaining_amount = total - sum(payment.amount)`
   - `calculated_status`:
     - If `total_paid == 0`: `"Unpaid"`
     - If `0 < total_paid < total`: `"Partially Paid"`
     - If `total_paid >= total`: `"Paid"`
4. **Ledger Derivation**:
   - Customer Ledger merges `Sale` debits and `Payment` credits chronologically ordered by transaction date.
   - Supplier Ledger merges `Purchase` credits and `Payment` debits chronologically ordered by transaction date.
5. **No Stock Mutation on Payment**:
   - Zero `StockMovement` records are created upon payment creation or deletion. Inventory movements are restricted strictly to invoice generation and deletion.

---

## 7. Cheques, Notifications & SMS Database Schema

### 7.1 Cheque Model (`apps.credit.models.Cheque` -> `cheques`)
- **Table**: `cheques`
- **Fields**:
  - `id`: BigAutoField (PK)
  - `company_id`: ForeignKey to `companies.Company` (Multi-tenancy)
  - `cheque_type`: CharField (`GIVEN`, `RECEIVED`)
  - `cheque_number`: CharField(64, db_index=True)
  - `bank_name`: CharField(128, db_index=True)
  - `amount`: DecimalField(max_digits=14, decimal_places=2)
  - `cheque_date`: DateField(db_index=True)
  - `customer_id`: Nullable ForeignKey to `sales.Customer`
  - `supplier_id`: Nullable ForeignKey to `purchases.Supplier`
  - `sale_id`: Nullable ForeignKey to `sales.Sale`
  - `purchase_id`: Nullable ForeignKey to `purchases.Purchase`
  - `payment_id`: Nullable OneToOneField to `sales.Payment`
  - `status`: CharField (`PENDING`, `CLEARED`, `BOUNCED`, `CANCELLED`, default `PENDING`, db_index=True)
  - `notes`: TextField (running remarks with timestamped status audit trail)
  - `created_by_id`: Nullable ForeignKey to `accounts.User`
  - `created_at`, `updated_at`: DateTimeField

### 7.2 Notification & Preference Models (`apps.audit.models`)
- **Table**: `notifications`
  - `id`: BigAutoField (PK)
  - `user_id`: Nullable ForeignKey to `accounts.User`
  - `company_id`: Nullable ForeignKey to `companies.Company`
  - `title`: CharField(255)
  - `message`: TextField
  - `notification_type`: CharField(64, db_index=True) (`low_stock`, `critical_stock`, `out_of_stock`, `stock_received`, `stock_restored`, `payment_due`, `payment_overdue`, `cheque_due_soon`, `cheque_due_today`, `cheque_overdue`, etc.)
  - `priority`: CharField (`critical`, `high`, `normal`, `info`)
  - `module`: CharField(64)
  - `record_id`: Nullable IntegerField
  - `dedup_key`: CharField(255, db_index=True) (Prevents redundant alerts for same state)
  - `is_popup`: BooleanField (Triggers modal / floating dismissible banner)
  - `popup_dismissed`: BooleanField (Indicates user dismissed floating banner)
  - `is_read`: BooleanField (Indicates user marked notification read in center)
  - `created_at`: DateTimeField(auto_now_add=True)

- **Table**: `notification_preferences`
  - `id`: BigAutoField (PK)
  - `user_id`: OneToOneField to `accounts.User`
  - Granular toggles: `notify_low_stock`, `notify_critical_stock`, `notify_out_of_stock`, `notify_stock_received`, `notify_stock_restored`, `notify_payment_due`, `notify_payment_overdue`, `notify_cheque_due_soon`, `notify_cheque_due_today`, `notify_cheque_overdue`, `notify_receivable_due`, `notify_receivable_overdue`, `notify_payable_due`, `notify_payable_overdue`.
  - Delivery channels: `sms_enabled` (bool), `sms_phone_number` (varchar), `popup_enabled` (bool).

- **Table**: `sms_logs`
  - `id`: BigAutoField (PK)
  - `user_id`: Nullable ForeignKey to `accounts.User`
  - `company_id`: Nullable ForeignKey to `companies.Company`
  - `recipient`: CharField(32, db_index=True)
  - `message`: TextField
  - `notification_type`: CharField(64)
  - `status`: CharField(32) (`Sent`, `Failed`, `Deduplicated`)
  - `provider`: CharField(64)
  - `dedup_key`: CharField(255, db_index=True)
  - `error_message`: TextField
  - `created_at`: DateTimeField(auto_now_add=True)

### 7.3 Inventory Critical Stock Extension
- **Table**: `products`
  - `critical_stock`: IntegerField(default=0, help_text="Critical low stock alert threshold")
  - `stock_status` logic:
    - `current_stock <= 0` ➔ `out_of_stock`
    - `0 < current_stock <= effective_critical_stock` ➔ `critical`
    - `effective_critical_stock < current_stock <= minimum_stock` ➔ `low`
    - `current_stock > minimum_stock` ➔ `normal`

---

## 8. Supabase PostgreSQL Production Migration & Operation

### 8.1 MySQL to PostgreSQL Type Mapping

| MySQL Datatype | PostgreSQL / Supabase Datatype | Django Field Mapping | Preservation Note |
|---|---|---|---|
| `AUTO_INCREMENT` / `INT` / `BIGINT` | `BIGSERIAL` / `IDENTITY` | `models.BigAutoField` | Sequences preserved via `setval(pg_get_serial_sequence())`. |
| `TINYINT(1)` | `BOOLEAN` | `models.BooleanField` | Values `1` ➔ `true`, `0` ➔ `false`. |
| `DATETIME` | `TIMESTAMP WITH TIME ZONE` | `models.DateTimeField` | Stored in UTC, localized via `TIME_ZONE="Asia/Kathmandu"`. |
| `JSON` | `JSONB` | `models.JSONField` | Native binary indexed JSON in PostgreSQL. |
| `DECIMAL(14,2)` | `NUMERIC(14,2)` | `models.DecimalField` | Exact financial monetary precision guaranteed. |
| `VARCHAR(N)` | `VARCHAR(N)` | `models.CharField` | Preserves character lengths and collation. |
| `LONGTEXT` / `TEXT` | `TEXT` | `models.TextField` | Unbounded text support. |

### 8.2 Supabase Connection Architectures

1. **Direct Connection (Port 5432)**:
   - URL: `postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres?sslmode=require`
   - Used for: Schema migrations (`python manage.py migrate`), data imports, long-lived background jobs.
   - Pool settings: `CONN_MAX_AGE = 600`, prepared statements enabled.

2. **Transaction Pooler (Port 6543 / Supavisor / PgBouncer)**:
   - URL: `postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres?sslmode=require`
   - Used for: High-concurrency web traffic and container autoscaling.
   - Pool settings: `DB_IS_POOLER=True`, `CONN_MAX_AGE = 0`, `DISABLE_SERVER_SIDE_CURSORS = True`.

### 8.3 Migration Tooling Suite (`scripts/`)
- `scripts/backup_mysql.py`: Non-destructive backup of source database into versioned JSON fixture format.
- `scripts/migrate_mysql_to_supabase.py`: Schema construction, data import, and primary key sequence alignment (`setval`).
- `scripts/verify_database_migration.py`: 4-tier audit tool checking tables, record counts, auth hashes, tenant isolation, and aggregations.