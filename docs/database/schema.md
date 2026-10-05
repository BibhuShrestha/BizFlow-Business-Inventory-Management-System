# Database Schema Specification

> **BizFlow Relational Schema**  
> *Authoritative schema definition of all core tables, field types, constraints, and indexes.*

---

## 1. Core Entity Tables

### A. `users` (`apps.accounts.models.User`)
Custom user entity extending Django `AbstractUser`.

| Column | Type | Nullable | Constraints & Defaults | Description |
|---|---|---|---|---|
| `id` | BigAutoField | No | PK, Auto | Unique User ID |
| `email` | EmailField(255) | No | Unique, Indexed | User login email |
| `username` | CharField(150) | No | Unique | Username handle |
| `phone` | CharField(32) | Yes | Blank default `""` | User contact phone |
| `role` | CharField(32) | No | Default `"cashier"` | RBAC role (admin, manager, cashier, seller) |
| `active_company_id` | Integer | Yes | FK -> `companies` | Currently selected active company |
| `is_active` | BooleanField | No | Default `True` | Account active flag |
| `date_joined` | DateTimeField | No | Auto now add | Registration timestamp |

---

### B. `companies` (`apps.companies.models.Company`)
Multi-tenant organizational unit.

| Column | Type | Nullable | Constraints & Defaults | Description |
|---|---|---|---|---|
| `id` | BigAutoField | No | PK, Auto | Unique Company ID |
| `name` | CharField(255) | No | Indexed | Legal business name |
| `code` | CharField(32) | No | Unique, Indexed | Short tenant identifier |
| `pan_vat_number`| CharField(64) | Yes | Blank default `""` | Tax registration number |
| `email` | EmailField(255) | Yes | Nullable | Contact email |
| `phone` | CharField(32) | Yes | Blank default `""` | Contact phone |
| `address` | TextField | Yes | Blank default `""` | Physical address |
| `is_active` | BooleanField | No | Default `True` | Company active status |

---

### C. `products` (`apps.inventory.models.Product`)
Inventory master record.

| Column | Type | Nullable | Constraints & Defaults | Description |
|---|---|---|---|---|
| `id` | BigAutoField | No | PK, Auto | Unique Product ID |
| `sku` | CharField(64) | No | Unique, Indexed | Alphanumeric stock keeping unit |
| `name` | CharField(255) | No | Indexed | Product name |
| `category_id` | BigInteger | No | FK -> `categories` | Product category |
| `company_id` | BigInteger | Yes | FK -> `companies` | Owning tenant company |
| `seller_id` | BigInteger | Yes | FK -> `sellers` | Linked seller profile |
| `unit` | CharField(32) | No | Default `"pcs"` | Measurement unit (pcs, kg, ltr, box) |
| `purchase_price`| Decimal(12,2) | No | Default `0.00` | Cost / wholesale procurement price |
| `selling_price` | Decimal(12,2) | No | Default `0.00` | Retail selling price |
| `tax_rate` | Decimal(5,2) | No | Default `0.00` | Applicable VAT/Tax percentage |
| `minimum_stock` | Integer | No | Default `0` | Reorder alert threshold |
| `current_stock` | Integer | No | Default `0` | Cached stock count on hand |
| `is_active` | BooleanField | No | Default `True` | Active catalog flag |

---

### D. `stock_movements` (`apps.inventory.models.StockMovement`)
Immutable inventory movement audit ledger.

| Column | Type | Nullable | Constraints & Defaults | Description |
|---|---|---|---|---|
| `id` | BigAutoField | No | PK, Auto | Unique Movement ID |
| `product_id` | BigInteger | No | FK -> `products` | Affected product |
| `movement_type` | CharField(32) | No | Choices: `IN`, `OUT` | Movement direction |
| `quantity` | Integer | No | Default `0` | Number of units transferred |
| `reference_type`| CharField(64) | No | Default `"ADJUSTMENT"`| `SALE`, `PURCHASE`, `ADJUSTMENT` |
| `reference_id` | Integer | Yes | Nullable | ID of associated sale or purchase |
| `description` | TextField | Yes | Blank default `""` | Movement notes |
| `created_at` | DateTimeField | No | Auto now add, Indexed| Movement timestamp |

---

### E. `sales` (`apps.sales.models.Sale`)
Sales invoice header and receivables record.

| Column | Type | Nullable | Constraints & Defaults | Description |
|---|---|---|---|---|
| `id` | BigAutoField | No | PK, Auto | Unique Sale ID |
| `invoice_number`| CharField(64) | No | Unique, Indexed | Formatted invoice sequence # |
| `customer_id` | BigInteger | Yes | FK -> `customers` | Purchasing customer |
| `company_id` | BigInteger | Yes | FK -> `companies` | Multi-tenant company |
| `sale_date` | DateTimeField | No | Explicit DateTime | Transaction date and time |
| `discount` | Decimal(12,2) | No | Default `0.00` | Total discount amount |
| `tax` | Decimal(12,2) | No | Default `0.00` | Total VAT/Tax amount |
| `total` | Decimal(14,2) | No | Default `0.00` | Grand invoice total payable |
| `payment_status`| CharField(32) | No | Choices: `Due`, `Partial`, `Paid` | Settlement state |
| `payment_method`| CharField(32) | No | Default `"Cash"` | Cash, Card, QR, Cheque, Credit |
| `cheque_number` | CharField(64) | Yes | Blank default `""` | Cheque voucher # if applicable |
| `cheque_date` | DateField | Yes | Nullable | Cheque maturity date |
| `due_date` | DateField | Yes | Nullable, Indexed | Credit invoice maturity due date |
| `notes` | TextField | Yes | Blank default `""` | Invoice notes / customer memo |

---

### F. `payments` (`apps.sales.models.Payment`)
Settlement voucher ledger for sales, purchases, and party debts.

| Column | Type | Nullable | Constraints & Defaults | Description |
|---|---|---|---|---|
| `id` | BigAutoField | No | PK, Auto | Unique Payment ID |
| `payment_date` | DateTimeField | No | Explicit DateTime | Date payment occurred |
| `amount` | Decimal(14,2) | No | Default `0.00` | Monetary settlement sum |
| `payment_method`| CharField(32) | No | Default `"Cash"` | Cash, Cheque, Bank, QR |
| `status` | CharField(32) | No | Default `"Completed"` | Completed, Pending, Void |
| `sale_id` | BigInteger | Yes | FK -> `sales` | Settled sales invoice |
| `purchase_id` | BigInteger | Yes | FK -> `purchases` | Settled purchase bill |
| `customer_id` | BigInteger | Yes | FK -> `customers` | Settling customer |
| `supplier_id` | BigInteger | Yes | FK -> `suppliers` | Settled supplier |
| `cheque_number` | CharField(64) | Yes | Blank default `""` | Cheque number if applicable |
| `cheque_date` | DateTimeField | Yes | Nullable | Cheque clearing date |
| `bank_name` | CharField(128) | Yes | Blank default `""` | Issuing / receiving bank |
| `notes` | TextField | Yes | Blank default `""` | Settlement notes |
| `created_by_id` | BigInteger | Yes | FK -> `users` | User issuing voucher |
| `created_at` | DateTimeField | No | Auto now add | Record creation timestamp |
