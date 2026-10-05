# Database Migrations History & Guidelines

> **BizFlow Migration Ledger**  
> *Authoritative ledger of Django schema migrations, execution sequence, and zero-downtime rules.*

---

## 1. Migration Protocol & Best Practices

1. **Non-Destructive Schema Evolution**: Migrations must never drop production columns containing active customer financial records without staged deprecation.
2. **Reversible Operations**: Whenever possible, all custom migration operations must provide an explicit `reverse_code` or revert path.
3. **No Direct DDL**: Raw manual SQL `ALTER TABLE` commands in production environments are strictly forbidden. All schema changes run via `manage.py migrate`.

---

## 2. Migration Ledger by Application

| App | Migration File | Description | Impact |
|---|---|---|---|
| **`accounts`** | `0001_initial.py` | Initial custom `User` model, company linking, phone, and role. | Core user table |
| **`accounts`** | `0002_revokedtoken.py` | Adds `RevokedToken` table with token JTI and expiration timestamp. | JWT revocation |
| **`companies`** | `0001_initial.py` | Creates `Company` and `Seller` models for multi-tenant isolation. | Organization |
| **`inventory`** | `0001_initial.py` | Creates `Category`, `Product`, and `StockMovement` tables. | Products & Ledger |
| **`sales`** | `0001_initial.py` | Creates `Customer`, `Sale`, `SaleItem`, and `Payment` tables. | POS & Invoicing |
| **`sales`** | `0002_payment_created_by_payment_notes_sale_due_date.py` | Adds indexed `due_date` to `Sale`; adds `created_by` and `notes` to `Payment`. | Credit & Udhaar |
| **`purchases`** | `0001_initial.py` | Creates `Supplier`, `Purchase`, and `PurchaseItem` tables. | Vendor Bills |
| **`purchases`** | `0002_purchase_due_date.py` | Adds indexed `due_date` to `Purchase` for supplier credit tracking. | Credit & Udhaar |
| **`accounting`**| `0001_initial.py` | Creates `ExpenseCategory` and `Expense` tables. | Expenses |
| **`accounting`**| `0002_initial.py` | Creates `Account`, `JournalEntry`, and `JournalEntryItem`. | Double Entry |
| **`audit`** | `0001_initial.py` | Creates `AuditLog`, `Notification`, `EmailLog`, and `ExportLog`. | Audit & Alerts |
| **`transactions`**| `0001_initial.py` | Creates internal account transaction and cheque ledger. | Banking |
