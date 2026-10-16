# BizFlow: Authoritative Feature Map & Core Value Kernel

**Document Version:** 1.0.0  
**Scope:** Complete feature-to-implementation mapping, dependency graph, core value identification, and complexity reduction plan.

---

## 1. Executive Definition: The Smallest Core Value Kernel

BizFlow's fundamental mission is: **"Enable a business owner or cashier to track products, intake inventory from suppliers, sell to customers with instant stock deductions, track Udhaar (credit) debts/settlements, and view daily financial performance with total data isolation."**

### Core vs. Auxiliary Classification

```
┌────────────────────────────────────────────────────────────────────────┐
│                   THE CORE VALUE KERNEL (Must-Have)                    │
│                                                                        │
│  [1. Auth & Company Context] ──► [2. Product & Stock Ledger]           │
│             │                               │                          │
│             ▼                               ▼                          │
│  [3. Purchases & Procurement] ──► [4. Sales Checkout & Invoicing]      │
│             │                               │                          │
│             ▼                               ▼                          │
│  [5. Receivables/Payables (Udhaar)] ──► [6. Daybook & Cash Summary]     │
└────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                  SUPPORTING & AUXILIARY SUBSYSTEMS                     │
│                                                                        │
│  • Inline Quick-Add Modals & Entity Resolvers                          │
│  • Operational Expense Logging                                         │
│  • Cheque Clearance & Date Alerts                                     │
│  • CSV/Excel Central Export & Import                                   │
│  • Activity & Audit Trail Logging                                      │
│  • Google OAuth2 Social Login & Granular RBAC Overrides                │
│  • AI Business Analytics & Decision Support Suite                      │
│  • External SMS Reminders & Notification Bell Center                   │
└────────────────────────────────────────────────────────────────────────┘
```

The application's **minimum viable commercial product** is delivered entirely by the 6 core pillars. The supporting modules provide operational ergonomics and advanced capabilities, but must not introduce architectural fragility to the core loop.

---

## 2. Feature-to-Implementation Map

### Feature 1: Multi-Tenant Authentication & Active Company Scoping
- **Purpose:** Secure system access and ensure total isolation so that users only see and manipulate data belonging to their assigned company.
- **User Workflow:**
  1. User visits `/auth/login/` (or API `/api/v1/auth/login`).
  2. Enters email and password. System checks PBKDF2 hash (or auto-upgrades legacy hash).
  3. Session is established and `request.user.active_company` is loaded into request context.
  4. User can switch active company via `/companies/<id>/select/` if granted multi-company access.
- **Implementation Files:**
  - **Models:** `apps.accounts.models.User`, `Role`, `apps.companies.models.Company`
  - **Views / Routers:** `apps.accounts.views` (`login_view`, `logout_view`), `apps.companies.views` (`company_select`), `api.routers.auth`
  - **Forms / Schemas:** `apps.accounts.forms.LoginForm`, `api.schemas.auth`
  - **Domain Services:** `backend/domain/services/auth_service.py`
  - **Templates:** `templates/accounts/login.html`, `templates/base/navbar.html`
  - **Tests:** `tests/test_auth_and_permissions.py`, `tests/test_multi_tenant_isolation.py`
- **Dependencies:** `django.contrib.auth`, `django.contrib.sessions`, `core.security.security_utils`.
- **Classification:** **CORE KERNEL**.

---

### Feature 2: Product Catalog & Stock Inventory
- **Purpose:** Maintain inventory master data (SKU, barcode, purchase price, selling price, units, categories) and track stock counts in real-time.
- **User Workflow:**
  1. Cashier/Manager visits `/products/` to see stock levels, search by name/SKU, or filter by category.
  2. Manager visits `/products/new/` to add an item with initial stock or opening quantity.
  3. Low stock indicators visually warn when stock is below `min_stock`.
  4. Manual stock adjustments are recorded at `/inventory/adjust/` with audit reasoning.
- **Implementation Files:**
  - **Models:** `apps.inventory.models.Product`, `Category`, `StockMovement`
  - **Views / Routers:** `apps.inventory.views` (`product_list`, `product_create`, `product_edit`), `apps.inventory.stock_views` (`stock_movements`, `stock_adjust`)
  - **Forms:** `apps.inventory.forms.ProductForm`, `StockAdjustmentForm`
  - **Domain Services:** `backend/domain/services/stock_service.py` (`StockService.add`, `StockService.deduct`, `StockService.adjust`)
  - **Templates:** `templates/inventory/product_list.html`, `product_form.html`, `stock_movements.html`, `stock_adjust.html`
  - **Tests:** `tests/test_shared_business_logic.py`, `tests/test_quick_add_and_forms.py`, `tests/test_multi_tenant_isolation.py`
- **Dependencies:** `apps.companies.models.Company`, `apps.companies.models.Seller`.
- **Classification:** **CORE KERNEL**.

---

### Feature 3: Sales Invoicing & POS Stock Decrements
- **Purpose:** Process customer sales, generate unique invoice numbers, calculate subtotal/discount/VAT, and atomically decrement stock counts.
- **User Workflow:**
  1. Cashier opens `/sales/create/` or POS checkout.
  2. Selects customer (or walks-in) and enters transaction date / due date.
  3. Adds product line items with quantities, selling prices, and item discounts.
  4. Selects payment method (Cash, Bank/QR, Cheque, Credit/Udhaar).
  5. Submits form: System validates stock availability, creates `Sale` and `SaleItem` rows, decrements product stock via `StockService`, and displays printable invoice `/sales/<id>/`.
- **Implementation Files:**
  - **Models:** `apps.sales.models.Sale`, `SaleItem`, `Customer`, `Payment`
  - **Views:** `apps.sales.views` (`sale_list`, `sale_create`, `sale_detail`, `sale_delete`)
  - **Forms:** `apps.sales.forms.SaleForm`, `SaleItemFormSet`
  - **Domain Services:** `backend/domain/services/sale_service.py`, `backend/domain/services/stock_service.py`
  - **Templates:** `templates/sales/sale_list.html`, `sale_form.html`, `sale_detail.html`
  - **Tests:** `tests/test_shared_business_logic.py`, `tests/test_quick_add_and_forms.py`, `tests/test_credit_management.py`
- **Dependencies:** `django.db.transaction.atomic`, `apps.inventory.models.Product`, `apps.inventory.models.StockMovement`.
- **Classification:** **CORE KERNEL**.

---

### Feature 4: Purchases & Procurement Stock Intake
- **Purpose:** Record vendor bills for inventory procurement and atomically increment product stock counts.
- **User Workflow:**
  1. Manager/Staff navigates to `/purchases/create/`.
  2. Selects Supplier and enters vendor bill/PO number and bill date.
  3. Enters purchased items, inward quantities, and cost prices.
  4. Selects payment method (Cash, Credit/Udhaar, Cheque).
  5. Submits bill: System records `Purchase` and `PurchaseItem` records, increments stock via `StockService`, and updates supplier debt.
- **Implementation Files:**
  - **Models:** `apps.purchases.models.Purchase`, `PurchaseItem`, `Supplier`
  - **Views:** `apps.purchases.views` (`purchase_list`, `purchase_create`, `purchase_detail`, `purchase_delete`)
  - **Forms:** `apps.purchases.forms.PurchaseForm`, `PurchaseItemFormSet`
  - **Domain Services:** `backend/domain/services/purchase_service.py`, `backend/domain/services/stock_service.py`
  - **Templates:** `templates/purchases/purchase_list.html`, `purchase_form.html`, `purchase_detail.html`
  - **Tests:** `tests/test_shared_business_logic.py`, `tests/test_quick_add_and_forms.py`
- **Dependencies:** `django.db.transaction.atomic`, `apps.inventory.models.Product`, `apps.inventory.models.StockMovement`.
- **Classification:** **CORE KERNEL**.

---

### Feature 5: Receivables, Payables & Party Ledgers (Udhaar Portal)
- **Purpose:** Track credit given to customers, credit taken from suppliers, outstanding balances, and partial settlement vouchers.
- **User Workflow:**
  1. Cashier views `/credit/customers-dues/` or `/credit/suppliers-dues/` to see who owes money and who is overdue.
  2. Customer arrives to make a partial payment: Cashier clicks `/credit/payments/add/`, inputs received amount, chooses Cash/Bank/Cheque, and links to the customer/sale.
  3. Cashier prints or views full chronological party ledger at `/credit/ledger/customer/<id>/` showing every invoice, payment, and running balance.
- **Implementation Files:**
  - **Models:** `apps.sales.models.Sale` (`due_date`), `apps.sales.models.Payment`, `apps.purchases.models.Purchase` (`due_date`)
  - **Views:** `apps.credit.views` (`dashboard`, `customers_dues`, `suppliers_dues`, `customer_ledger`, `supplier_ledger`, `add_payment`, `overdue_list`)
  - **Forms:** `apps.credit.forms.PaymentVoucherForm`
  - **Domain Services:** `backend/domain/services/credit_service.py`
  - **Templates:** `templates/credit/credit_dashboard.html`, `customer_dues.html`, `customer_ledger.html`, `payment_form.html`
  - **Tests:** `tests/test_credit_management.py`
- **Dependencies:** `apps.sales.models`, `apps.purchases.models`.
- **Classification:** **CORE KERNEL**.

---

### Feature 6: Daily Financial Summary & Daybook
- **Purpose:** Provide daily operational cash tracking: total sales, total purchases, operational expenses, gross profit, and cash balance for the day.
- **User Workflow:**
  1. Business owner opens `/dashboard/` or `/reports/daybook/`.
  2. Selects date range (defaults to Today).
  3. System tallies cash in, cash out, credit sales, and net balance.
- **Implementation Files:**
  - **Models:** `apps.sales.models.Sale`, `apps.purchases.models.Purchase`, `apps.accounting.models.Expense`
  - **Views:** `apps.dashboard.views.dashboard_view`, `apps.reports.views.daybook`
  - **Domain Services:** `backend/domain/services/report_service.py`
  - **Templates:** `templates/dashboard/index.html`, `templates/reports/daybook.html`
  - **Tests:** `tests/test_django_web_application.py`, `tests/test_analytics_and_ai.py`
- **Dependencies:** Sales, Purchases, Accounting models.
- **Classification:** **CORE KERNEL**.

---

### Feature 7: Operational Expense Management
- **Purpose:** Record non-inventory business expenses (Rent, Electricity, Tea, Staff Salary) scoped to company.
- **User Workflow:** Staff visits `/expenses/new/`, enters category, amount, description, and payment method.
- **Implementation Files:**
  - **Models:** `apps.accounting.models.Expense`, `ExpenseCategory`
  - **Views:** `apps.accounting.views` (`expense_list`, `expense_create`, `expense_edit`, `expense_delete`)
  - **Forms:** `apps.accounting.forms.ExpenseForm`
  - **Templates:** `templates/accounting/expense_list.html`, `expense_form.html`
- **Classification:** **Supporting / High Value**.

---

### Feature 8: Inline Quick-Add Modals & Form State Persistence
- **Purpose:** Prevent workflow interruption when creating an invoice by allowing quick creation of missing Customers, Suppliers, Products, or Categories without leaving the invoice form.
- **Implementation Files:**
  - **Views:** `apps.sales.customer_views.customer_create` (AJAX handler), `apps.companies.views.company_create` (AJAX handler), `apps.inventory.views.product_create` (AJAX handler)
  - **Static JS:** `backend/django_app/static/js/quick_add.js`
  - **Tests:** `tests/test_quick_add_and_forms.py`
- **Classification:** **Supporting / UX Ergonomics**.

---

### Feature 9: Cheque Management & Reminders
- **Purpose:** Track post-dated and clearance status of cheques (Pending, Cleared, Bounced) with dynamic 7/3/2/1/0-day notifications.
- **Implementation Files:**
  - **Models:** `apps.sales.models.Payment` (`cheque_number`, `cheque_date`, `cheque_bank`, `cheque_status`)
  - **Views / Routers:** `api.routers.cheques`, `apps.credit.views`
  - **Domain Services:** `backend/domain/services/credit_service.py`
  - **Templates:** `templates/credit/cheque_list.html`
- **Classification:** **Supporting / Extension**.

---

### Feature 10: Import & Export Suite (CSV & Styled Excel)
- **Purpose:** Export reports, inventory, sales, and purchases to CSV (with UTF-8 BOM) and Excel (.xlsx) via OpenPyXL, and bulk-import product catalogs with 10MB bounds.
- **Implementation Files:**
  - **Core Utility:** `apps.core_app.exports.generate_csv_response`, `generate_excel_response`, `parse_uploaded_file`
  - **Domain Services:** `backend/domain/services/import_export_service.py`
  - **Tests:** `tests/test_performance_and_security.py`
- **Classification:** **Supporting / Extension**.

---

### Feature 11: Multi-Channel Alerts, Notifications & SMS
- **Purpose:** In-app notification center bell, unread badge count, toast alerts for low stock and overdue credit, and SMS gateway stub for sending debtor reminders.
- **Implementation Files:**
  - **Models:** `apps.audit.models.Notification`
  - **Views / Routers:** `api.routers.notifications`, `apps.dashboard.views.notification_list`
  - **Domain Services:** `backend/domain/services/notification_service.py`, `sms_service.py`
- **Classification:** **Supporting / Extension**.

---

### Feature 12: AI Business Analytics & Decision Support
- **Purpose:** Exploratory analytics dashboard with sales trend graphs, margin forecasting, stock replenishment recommendations, and period comparisons.
- **Implementation Files:**
  - **Views / Routers:** `apps.reports.views.analytics_explorer`, `api.routers.analytics`
  - **Domain Services:** `backend/domain/services/analytics_service.py`
  - **Templates:** `templates/reports/analytics_explorer.html`
  - **Tests:** `tests/test_analytics_and_ai.py`
- **Classification:** **Supporting / Extension**.

---

### Feature 13: Multi-Company Workspace Quick-Switcher & Tenant Scoping
- **Purpose:** Seamlessly switch active company contexts in multi-company setups and enforce complete data segregation across transactions and user profiles.
- **Implementation Files:**
  - **Models:** `apps.companies.models.Company`, `apps.accounts.models.User.active_company`
  - **Views / Routers:** `apps.companies.views` (`set_active_company`, `company_list`), `apps.accounts.views` (`user_list` company filtering)
  - **Context Processors:** `apps.core_app.context_processors.active_company` (`user_companies`)
  - **Templates:** `templates/base/base.html` (`#company-dropdown-menu`), `templates/accounts/user_list.html`
  - **Tests:** `tests/test_multi_tenant_isolation.py`
- **Classification:** **Core Value Enabler**.

---

### Feature 14: Cashier & Global Keyboard Ergonomics
- **Purpose:** Accelerate repetitive cashier, clerk, and accountant data entry via standardized single-key shortcuts, form-saving hotkeys, and quick cheatsheet lookup.
- **Implementation Files:**
  - **CSS Design Tokens:** `<kbd>` styling in `main.css` and `base.html`
  - **Shortcuts Modal:** `templates/base/base.html` (`#bizflow-shortcuts-modal`)
  - **Keydown Manager:** Native event listener in `base.html` (<kbd>Ctrl+K</kbd>, <kbd>N</kbd>, <kbd>P</kbd>, <kbd>I</kbd>, <kbd>C</kbd>, <kbd>W</kbd>, <kbd>D</kbd>, <kbd>?</kbd>, <kbd>Ctrl+Enter</kbd>, <kbd>Esc</kbd>)
  - **Form Indicators:** Embedded tip badges in sales, purchases, inventory, party forms, and customer registers
- **Classification:** **Supporting / Operational Ergonomics**.

---

## 3. Complexity Reduction & Simplification Strategy

In strict adherence to the mandate: **"Prefer deleting complexity over adding more code"**, the following areas represent dead or duplicative complexity that should be streamlined:

| Target Area | Current State / Complexity | Proposed Simplification | Risk / Impact |
|---|---|---|---|
| **Orphaned Apps (`apps/parties`, `apps/transactions`)** | Two abandoned app folders from initial scaffolding; neither is in `INSTALLED_APPS` nor imported. | Archive or cleanly prune them so developers are not confused by non-functioning shadow models. | **Zero risk** (no code imports them). |
| **Dual Context Parameters** | Views pass both `"search"` and `"search_query"` to templates in multiple list views. | Standardize template context on single canonical key `"search"`. | **Zero risk**, cleans up templates. |
| **Unlinked FastAPI Routers** | `backend/api/main.py` has commented-out import stubs for 8 routers that duplicate Django views. | Keep only active, tested routers (`auth`, `credit`, `cheques`, `notifications`, `analytics`, `health`) and clean up commented legacy stubs. | **Zero risk**, clarifies API contract. |
| **Redundant Queryset Re-computation** | Certain dashboard cards re-query models that context processors or services already computed. | Use `report_service` and `credit_service` single-pass aggregations instead of scattershot ORM queries. | **Positive impact**, reduces DB round-trips. |

---

## 4. Phased Execution Protocol

Every modification adheres to the 3-step safety standard:
1. **Batch Changes:** Limit modifications to cohesive, self-contained functional groups.
2. **Document Diffs & Rationale:** Report exact files changed, why each was changed, and how complexity was reduced.
3. **Verify Green Status:** Run the full automated test suite (`py -m pytest tests/`) and confirm 0 failures before marking any step complete.
