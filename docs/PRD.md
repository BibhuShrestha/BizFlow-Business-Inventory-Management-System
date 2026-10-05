# Product Requirements Document (PRD)

## Product Overview

**BizFlow** is a comprehensive multi-company business inventory, sales, purchase, and financial management system designed specifically for small and medium enterprises (SMEs) in Nepal. The application provides an integrated platform combining stock control, invoicing, vendor/customer party ledgers, expense tracking, and reporting with native Nepali Bikram Sambat (BS) calendar integration.

This project represents a staged migration from a legacy monolithic Flask application to a clean, modular **Django 5.1+ / 6.0 + FastAPI** architecture. Django provides the robust server-side rendered web UI, admin dashboard, ORM models, and session management, while FastAPI delivers a high-performance REST API layer for future desktop and mobile clients. All business logic is encapsulated in a pure, framework-agnostic domain services layer shared across both interfaces.

---

## Problem

Small businesses and wholesale/retail merchants frequently operate across fragmented, error-prone manual systems:
1. **Disconnected Record-Keeping**: Inventory maintained in spreadsheets, credit ledgers written in physical paper notebooks (*khata*), and invoices generated in separate offline software.
2. **Lack of Native Nepali Calendar**: International software forces Gregorian (AD) calendar usage, whereas statutory, commercial, and tax workflows in Nepal operate on Bikram Sambat (BS).
3. **Multi-Entity Inefficiency**: Business owners operating multiple shops, branches, or companies must log into separate databases or maintain separate software instances.
4. **Credit Risk & Party Ledger Errors**: Difficulty tracking real-time receivables and payables leads to bad debts, unpaid supplier balances, and cash-flow bottlenecks.
5. **No Cross-Platform API Readiness**: Legacy desktop-only or monolithic web apps cannot easily integrate with barcode scanners, mobile apps, or e-commerce endpoints.

---

## Target Users

| User Persona | Role | Key Responsibilities & Needs |
|---|---|---|
| **Business Owner / Super Admin** | Owner | Full access across all companies. Oversees financial reports, user access, company setup, and system configuration. |
| **Store Manager** | Manager | Day-to-day operations: stock adjustments, sales/purchase approvals, expense logging, supplier orders, customer credit limits. |
| **Sales Staff / Cashier** | Staff | Rapid creation of sales invoices, receipt generation, checking current product stock, registering new customers. |
| **Accountant** | Financial Staff | Reconciliation of party ledgers, expense categorization, profit & loss analysis, balance sheets, and tax reports. |
| **External Client / App** | API Client | Desktop cashier POS clients or future mobile apps querying stock, syncing offline invoices, and authenticating via JWT. |

---

## Goals

1. **Complete Functional Parity**: Retain 100% of all existing business workflows, calculations, and validations from the original Flask project.
2. **Unified Data Layer**: Maintain a single relational schema managed via Django ORM with Zero schema deviation.
3. **Shared Domain Service Layer**: Prevent code duplication by keeping business calculations (stock deductions, tax calculations, invoice numbers) in framework-agnostic services.
4. **Dual Interface Excellence**:
   - Provide a responsive, server-rendered Django Web UI with Bootstrap 5.
   - Provide an asynchronous, OpenAPI-documented FastAPI REST API (`/api/v1/`).
5. **Native Nepali Calendar**: Seamless conversion between AD (Gregorian) and BS (Bikram Sambat) dates for invoices, filters, and reports.
6. **Zero Regression**: Preserve original database integrity and verify no features are damaged or omitted.

---

## Non-Goals

- Building end-user native Android/iOS mobile binaries in this stage (architecture and API endpoints are built; client apps are slated for subsequent phases).
- Building desktop native client executables in this stage (API contracts are prepared).
- Public-facing multi-vendor e-commerce marketplace.
- Complex international multi-currency forex arbitrage (single base currency NPR with standard foreign currency receipt tracking).
- Automated banking API gateway integrations (manual reconciliation and bank ledger entries are used).

---

## Existing Features

The original Flask project provides the following core feature sets, all of which are preserved in the migration:

1. **Authentication & Identity**:
   - Email and username login with password hashing.
   - User registration and role assignments (`admin`, `manager`, `staff`).
   - Password reset via secure email tokens.
   - Email verification workflows.
   - Google OAuth 2.0 social login.
2. **Company Management**:
   - Multi-tenant data isolation by active company.
   - Company profile customization (logo, address, PAN/VAT number, contact details).
   - Seller representative profiles associated with companies.
3. **Inventory & Product Catalog**:
   - Product master records with SKU, barcode, unit of measure (pcs, kg, box, etc.).
   - Category management with hierarchical grouping.
   - Real-time stock quantity tracking across companies.
   - Low-stock threshold alerts on the dashboard.
   - Manual stock adjustments (damage, shrinkage, physical audit reconciliations).
4. **Sales Management**:
   - Sales invoice creation with auto-incrementing invoice numbers.
   - Line items with quantity, unit price, discount, and VAT calculation.
   - Immediate stock decrement upon invoice confirmation.
   - Payment method recording (Cash, Bank Transfer, Cheque, Credit/Esewa/Khalti).
   - Customer credit balance updates.
   - Professional PDF invoice printing and thermal receipt format.
5. **Purchase Management**:
   - Vendor purchase invoices and bills.
   - Line-item purchasing with automatic inventory incrementation.
   - Cost price updates and purchase price history tracking.
   - Supplier credit balance management.
6. **Party Ledger (Customers & Suppliers)**:
   - Comprehensive customer and supplier registries.
   - Opening balance tracking.
   - Running ledger balance calculation (debit/credit transaction history).
   - Payment receipt vouchers and supplier payment vouchers.
7. **Expense & Financial Management**:
   - Categorized operating expense recording.
   - Company expense allocations.
   - Payment mode reconciliation.
8. **Reports & Analytics**:
   - Daily sales summary and revenue metrics.
   - Profit and loss calculation (Gross Profit = Sales Revenue - Cost of Goods Sold).
   - Stock valuation reports (FIFO / Average Cost).
   - Party balance aging reports.
   - Export reports to Excel (.xlsx) and PDF.
9. **Audit & Activity Log**:
   - System audit trail recording user actions, IP addresses, and timestamps.

---

## New Features

The new Django + FastAPI architecture introduces the following modern capabilities:

1. **FastAPI REST API Layer (`/api/v1/`)**:
   - High-throughput REST API with automated interactive OpenAPI/Swagger documentation (`/api/docs`).
   - Strictly typed Pydantic request and response schemas.
2. **JWT Authentication & Token Revocation**:
   - OAuth2 password bearer flow with short-lived JWT access tokens and secure refresh tokens.
   - Token blacklisting on logout.
3. **Reusable Domain Services Architecture**:
   - Business calculations extracted into clean Python domain classes (`SaleService`, `PurchaseService`, `StockService`, `AuthService`).
   - Both Django views and FastAPI routers invoke the exact same domain services.
4. **Modern Design System & Responsive UI**:
   - Unified color tokens, typography, component library, and responsive data tables.
   - Intuitive keyboard shortcuts for rapid point-of-sale data entry.
5. **Enhanced Security Posture**:
   - Django SecurityMiddleware with Content Security Policy (CSP), Strict-Transport-Security (HSTS), X-Content-Type-Options, and CSRF protection.
   - Rate limiting on sensitive authentication and payment endpoints.
6. **Udhaar / Credit Management System (Receivables & Payables)**:
   - Dedicated bidirectional credit tracking: Credit Given (Customer Receivables) and Credit Taken (Supplier Payables).
   - Real-time automatic balance recalculation (`Remaining = Total - Total Paid`) and dynamic statuses (`Unpaid`, `Partially Paid`, `Paid`, `Overdue`).
   - Multiple line items per transaction with dynamic VAT and discount recalculation.
   - Multi-voucher partial settlements with detailed payment history without affecting inventory stock.
   - Comprehensive running ledger statements for both customers and suppliers.
   - Direct integration into main dashboard KPIs, customer profiles, supplier profiles, and dedicated export hubs (CSV/Print).

---

## User Stories

### Authentication & Access Control

- As a user,  
  I want to log in securely with my email and password,  
  so that I can access my company's business data.

- As a user,  
  I want to sign in using my Google account,  
  so that I can quickly authenticate without managing another password.

- As a user,  
  I want to request a password reset link to my verified email,  
  so that I can regain access if I forget my credentials.

- As an admin,  
  I want to assign specific roles (Admin, Manager, Staff) to team members,  
  so that staff only have access to modules relevant to their job duties.

### Multi-Company Management

- As a business owner,  
  I want to switch between multiple business companies in the navigation bar,  
  so that I can manage several enterprises from a single user account.

- As an admin,  
  I want to upload my company logo and configure tax/PAN details,  
  so that my generated invoices reflect official company branding.

### Inventory Management

- As a manager,  
  I want to create products with categories, units, and minimum stock alerts,  
  so that items are organized and tracked accurately.

- As a staff member,  
  I want to see immediate low-stock notifications on the dashboard,  
  so that we can reorder inventory before running out of stock.

- As a manager,  
  I want to record manual stock adjustments with reason notes,  
  so that physical warehouse counts match system records.

### Sales & Invoicing

- As a cashier,  
  I want to quickly search products by name or barcode during checkout,  
  so that customer sales transactions can be processed without delay.

- As a cashier,  
  I want the system to calculate subtotal, discounts, and VAT automatically,  
  so that human mathematical errors are eliminated.

- As a customer,  
  I want to receive an itemized printed invoice with date and company details,  
  so that I have proof of purchase and tax documentation.

- As a manager,  
  I want canceling a mistaken invoice to automatically return items to stock,  
  so that inventory counts remain strictly balanced.

### Purchases & Supplier Operations

- As a store manager,  
  I want to record incoming purchase bills from suppliers,  
  so that product stock is increased and supplier balances are tracked.

- As an accountant,  
  I want to record partial payments against supplier invoices,  
  so that our remaining liability to suppliers is always clear.

### Party Ledgers & Accounting

- As an accountant,  
  I want to view a chronological statement of account for any customer or supplier,  
  so that I can reconcile discrepancies and resolve billing disputes.

- As an owner,  
  I want to view daily and monthly Profit & Loss statements,  
  so that I can assess the net profitability of each company.

- As an accountant,  
  I want to export sales and ledger reports to Microsoft Excel,  
  so that I can conduct offline audits and tax filings.

---

## Functional Requirements

### FR1: Authentication & Authorization
- FR1.1: System shall support secure password hashing via Argon2 or PBKDF2 with SHA-256.
- FR1.2: System shall provide role-based permissions preventing unauthorized URL or API endpoint access.
- FR1.3: Web UI shall use secure HTTP-only cookies with CSRF tokens; REST API shall use Bearer JWT headers.

### FR2: Tenant Isolation
- FR2.1: Every database transaction (Product, Sale, Purchase, Customer, Supplier, Expense) must store `company_id`.
- FR2.2: All queries executed in Django views and FastAPI routes must be scoped by the user's active company.

### FR3: Inventory Tracking & Invariants
- FR3.1: Inventory balance must update atomically within database transactions.
- FR3.2: Sales of out-of-stock items must be blocked unless negative stock override is explicitly granted by an Admin.
- FR3.3: Every stock adjustment must record timestamp, user ID, reason, quantity delta, and resulting balance.

### FR4: Sales & Billing
- FR4.1: Sales invoice numbers must follow sequential formats scoped per company and fiscal year.
- FR4.2: Total amounts, discounts, and VAT amounts must compute with precision decimal arithmetic (2 decimal places).
- FR4.3: Payments recorded against an invoice must decrement customer receivable balances.

### FR5: Purchases & Inventory Receipt
- FR5.1: Purchase entry must record supplier invoice number, date, line items, and payment mode.
- FR5.2: Unit purchase costs must update product purchase reference pricing.

### FR6: Date Localization (Bikram Sambat BS)
- FR6.1: The system shall accept and display dates in both Bikram Sambat (BS: YYYY-MM-DD) and Gregorian (AD).
- FR6.2: Conversion between AD and BS must be deterministic and backed by the `nepali-datetime` library.

### FR7: Reporting & Exports
- FR7.1: Reports shall support date range filtering, customer/supplier filtering, and category filtering.
- FR7.2: PDF generation must render clean tabular layouts with company letterhead via ReportLab or WeasyPrint.
- FR7.3: Excel exports must format numerical columns with correct currency and quantity formats.

### FR8: Udhaar & Credit Management
- FR8.1: **Bidirectional Credit Tracking**: System shall support Credit Given (Customer Receivables) and Credit Taken (Supplier Payables) with multi-line product items.
- FR8.2: **Inventory Invariance**: Credit Given transactions shall immediately decrement inventory stock; Credit Taken transactions shall immediately increment stock. Payment vouchers shall never alter stock quantities.
- FR8.3: **Dynamic Status Calculation**: Statuses must automatically calculate:
  - `Unpaid`: `Paid Amount == 0`
  - `Partially Paid`: `Paid Amount > 0` and `Remaining Amount > 0`
  - `Paid`: `Remaining Amount == 0`
  - `Overdue`: `Remaining Amount > 0` and `Today > Due Date`
- FR8.4: **Partial & Multi-Payment Settlement**: Support incremental payment vouchers with payment method, reference, notes, and audit creator metadata. Validate and prevent overpayments exceeding remaining balance.
- FR8.5: **Running Balance Party Ledgers**: Generate chronological debit, credit, and running balance statements for any customer or supplier with custom date range filtering.
- FR8.6: **Unified Integration**: Credit summaries, dues, and overdue metrics must automatically reflect on the main dashboard, customer profile, and supplier profile.

---

## Non-Functional Requirements

### NFR1: Performance
- Web page response times shall be under 200ms for 95% of standard requests.
- FastAPI REST API endpoints shall respond in under 60ms under normal load.
- Database queries must be optimized with appropriate indexes on `company_id`, `created_at`, `status`, and foreign keys.

### NFR2: Security
- Passwords must enforce minimum strength: >= 8 characters, with lowercase, uppercase, number, and special character.
- Protection against OWASP Top 10 vulnerabilities: SQL Injection (Django ORM parameterized queries), XSS (Django template auto-escaping), CSRF tokens on all state-changing web requests.
- JWT access tokens shall expire in 60 minutes; refresh tokens shall expire in 14 days and be stored securely.

### NFR3: Reliability & Data Integrity
- All transactional workflows (invoicing, stock adjustments) must run within ACID database transactions (`transaction.atomic()`).
- Database backups must be supported via scheduled database dump routines.

### NFR4: Usability & Accessibility
- Clean, uncluttered UI built with modern CSS tokens, legible typography, and semantic HTML5.
- Fast tabular keyboard navigation for point-of-sale data entry.
- Fully responsive layout functioning seamlessly on desktops, tablets, and smartphones.

---

## Success Criteria

1. **100% Behavioral Parity**: All 54 original Flask test cases and workflows map to equivalent passing tests in the new system.
2. **Zero Database Drift**: The Django models faithfully represent all 20 legacy tables without loss of historical fields or relationships.
3. **Automated Test Coverage**: New test suite passes with zero failures across settings, domain services, views, and API routers.
4. **Dual Interface Verification**: Django Web UI serves interactive HTML pages while FastAPI serves matching JSON endpoints concurrently on designated ports.

---

## Future Features

- **PySide6 Native Desktop POS Client**: Offline-first cashier application syncing with the FastAPI backend.
- **Mobile POS & Inventory App (Flutter / React Native)**: Barcode scanning via phone camera and instant receipt printing via Bluetooth thermal printers.
- **Automated WhatsApp / SMS Receipts**: Dispatching invoice PDFs and payment reminders directly to customer mobile numbers.
- **AI Inventory Forecasting**: Automated purchase recommendations based on seasonal sales trends and stock velocity.