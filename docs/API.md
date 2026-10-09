# API Documentation

## Base URL

```
Development: http://localhost:8001/api/v1/
Production:  https://yourdomain.com/api/v1/
```

## Interactive Documentation

```
Swagger UI:  http://localhost:8001/api/docs
ReDoc:       http://localhost:8001/api/redoc
OpenAPI:     http://localhost:8001/api/openapi.json
```

---

## Authentication

All endpoints (except login and register) require a Bearer token:

```
Authorization: Bearer <access_token>
```

### Obtain Tokens

```
POST /api/v1/auth/login
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "Password123!"
}
```

Response:
```json
{
    "success": true,
    "data": {
        "access_token": "eyJ...",
        "refresh_token": "eyJ...",
        "token_type": "bearer",
        "expires_in": 1800
    }
}
```

### Refresh Token

```
POST /api/v1/auth/refresh
Content-Type: application/json

{
    "refresh_token": "eyJ..."
}
```

---

## Standard Response Format

### Success
```json
{
    "success": true,
    "data": { ... }
}
```

### Success (List)
```json
{
    "success": true,
    "data": [ ... ],
    "pagination": {
        "page": 1,
        "page_size": 20,
        "total": 150,
        "total_pages": 8
    }
}
```

### Error
```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "The submitted data is invalid.",
        "details": { "field": ["error message"] }
    }
}
```

---

## HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK — Request succeeded |
| 201 | Created — Resource created |
| 204 | No Content — Deleted successfully |
| 400 | Bad Request — Validation error |
| 401 | Unauthorized — Missing or invalid token |
| 403 | Forbidden — Insufficient permissions |
| 404 | Not Found — Resource not found |
| 422 | Unprocessable Entity — Schema validation failed |
| 500 | Internal Server Error |

---

## Error Codes

| Code | Meaning |
|------|---------|
| AUTHENTICATION_FAILED | Invalid email or password |
| TOKEN_EXPIRED | Access token has expired |
| TOKEN_INVALID | Token is malformed or invalid |
| PERMISSION_DENIED | User lacks required role |
| NOT_FOUND | Requested resource does not exist |
| VALIDATION_ERROR | Request body failed validation |
| INSUFFICIENT_STOCK | Cannot complete sale — not enough stock |
| DUPLICATE_SKU | Product SKU already exists |
| EMAIL_ALREADY_REGISTERED | Email address already in use |

---

## Pagination

All list endpoints support:

```
GET /api/v1/products/?page=1&page_size=20
GET /api/v1/products/?page=2&page_size=50
```

Default: `page=1`, `page_size=20`. Maximum `page_size=100`.

---

## Filtering & Search

```
GET /api/v1/products/?search=laptop
GET /api/v1/products/?company_id=3
GET /api/v1/products/?seller_id=7
GET /api/v1/sales/?start_date=2081-01-01&end_date=2081-12-30
GET /api/v1/sales/?payment_status=Due
```

---

## Auth Endpoints

| Method | Endpoint | Auth | Permission | Description |
|--------|----------|------|------------|-------------|
| POST | /auth/login | No | — | Login, returns JWT tokens |
| POST | /auth/register | No | — | Register new account |
| POST | /auth/logout | Yes | Any | Logout (blacklist token) |
| POST | /auth/refresh | No | — | Refresh access token |
| GET | /auth/profile | Yes | Any | Get current user profile |
| PATCH | /auth/profile | Yes | Any | Update profile |
| POST | /auth/change-password | Yes | Any | Change password |
| POST | /auth/forgot-password | No | — | Request reset email |
| POST | /auth/reset-password | No | — | Reset with token |
| GET | /auth/verify-email/{token} | No | — | Verify email |
| POST | /auth/switch-company/{id} | Yes | Any | Switch active company |

---

## User Endpoints

| Method | Endpoint | Auth | Permission | Description |
|--------|----------|------|------------|-------------|
| GET | /users/ | Yes | Admin | List all users |
| POST | /users/ | Yes | Admin | Create new user |
| GET | /users/{id} | Yes | Admin | Get user details |
| PATCH | /users/{id} | Yes | Admin | Update user |
| DELETE | /users/{id} | Yes | Admin | Delete user |
| POST | /users/{id}/toggle | Yes | Admin | Toggle active status |

---

## Company Endpoints

| Method | Endpoint | Auth | Permission | Description |
|--------|----------|------|------------|-------------|
| GET | /companies/ | Yes | Staff+ | List companies |
| POST | /companies/ | Yes | Manager+ | Create company |
| GET | /companies/{id} | Yes | Staff+ | Company details |
| PATCH | /companies/{id} | Yes | Manager+ | Update company |
| DELETE | /companies/{id} | Yes | Manager+ | Delete company |
| POST | /companies/{id}/logo | Yes | Manager+ | Upload logo |
| GET | /companies/export | Yes | Staff+ | Export CSV/Excel |
| POST | /companies/import | Yes | Manager+ | Import from file |

---

## Product Endpoints

| Method | Endpoint | Auth | Permission | Description |
|--------|----------|------|------------|-------------|
| GET | /products/ | Yes | Staff+ | List products |
| POST | /products/ | Yes | Staff+ | Create product |
| GET | /products/{id} | Yes | Staff+ | Product details |
| PATCH | /products/{id} | Yes | Staff+ | Update product |
| DELETE | /products/{id} | Yes | Manager+ | Deactivate product |
| GET | /products/export | Yes | Staff+ | Export CSV/Excel |
| POST | /products/import | Yes | Manager+ | Bulk import |

---

## Sale Endpoints

| Method | Endpoint | Auth | Permission | Description |
|--------|----------|------|------------|-------------|
| GET | /sales/ | Yes | Staff+ | List sales |
| POST | /sales/ | Yes | Staff+ | Create sale invoice |
| GET | /sales/{id} | Yes | Staff+ | Sale details |
| DELETE | /sales/{id} | Yes | Manager+ | Delete sale |
| POST | /sales/{id}/payments | Yes | Staff+ | Record payment |
| GET | /sales/{id}/payments | Yes | Staff+ | Sale payments |

---

## Purchase Endpoints

| Method | Endpoint | Auth | Permission | Description |
|--------|----------|------|------------|-------------|
| GET | /purchases/ | Yes | Staff+ | List purchases |
| POST | /purchases/ | Yes | Staff+ | Create purchase order |
| GET | /purchases/{id} | Yes | Staff+ | Purchase details |
| DELETE | /purchases/{id} | Yes | Manager+ | Delete purchase |
| POST | /purchases/{id}/payments | Yes | Staff+ | Record payment |

---

## Inventory Endpoints

| Method | Endpoint | Auth | Permission | Description |
|--------|----------|------|------------|-------------|
| GET | /inventory/movements | Yes | Staff+ | Stock movement history |
| POST | /inventory/adjust | Yes | Manager+ | Manual stock adjustment |
| GET | /inventory/low-stock | Yes | Staff+ | Products below minimum |
| GET | /inventory/out-of-stock | Yes | Staff+ | Products with 0 stock |

---

## Report Endpoints

| Method | Endpoint | Auth | Permission | Description |
|--------|----------|------|------------|-------------|
| GET | /reports/summary | Yes | Manager+ | Business summary |
| GET | /reports/daybook | Yes | Manager+ | Daily ledger |
| GET | /reports/profit | Yes | Manager+ | Net profit |
| GET | /reports/inventory-value | Yes | Manager+ | Total inventory value |

---

## Udhaar / Credit Endpoints (/api/v1/credit)

| Method | Endpoint | Auth | Permission | Description |
|--------|----------|------|------------|-------------|
| GET | /credit/summary | Yes | Staff+ | Credit KPI summary (given, received, customer due, taken, supplier paid, supplier due) |
| GET | /credit/given | Yes | Staff+ | List credit given records with filters (`status`, `customer_id`, `search`) |
| POST | /credit/given | Yes | Staff+ | Record credit given to customer (auto-decrements stock, records initial payment if any) |
| GET | /credit/given/{id} | Yes | Staff+ | Credit given details, item lines, and payment history |
| GET | /credit/taken | Yes | Staff+ | List credit taken records with filters (`status`, `supplier_id`, `search`) |
| POST | /credit/taken | Yes | Staff+ | Record credit taken from supplier (auto-increments stock, records initial payment if any) |
| GET | /credit/taken/{id} | Yes | Staff+ | Credit taken details, item lines, and payment history |
| POST | /credit/payments | Yes | Staff+ | Record payment settlement against a sale or purchase (does not alter stock) |
| GET | /credit/customers-dues | Yes | Staff+ | Summary of outstanding receivables grouped by customer |
| GET | /credit/suppliers-dues | Yes | Staff+ | Summary of outstanding payables grouped by supplier |
| GET | /credit/overdue | Yes | Staff+ | Overdue receivables and payables past due date |
| GET | /credit/ledger/customer/{id} | Yes | Staff+ | Customer chronological statement of account with running balance |
| GET | /credit/ledger/supplier/{id} | Yes | Staff+ | Supplier chronological statement of account with running balance |

### Sample Credit Given Request (`POST /api/v1/credit/given`):
```json
{
  "customer_id": 1,
  "transaction_date": "2026-10-03",
  "due_date": "2026-10-20",
  "bill_number": "BILL-1001",
  "items": [
    {
      "product_id": 1,
      "quantity": 5,
      "unit_price": "1000.00",
      "discount": "0.00",
      "tax_rate": "13.00"
    }
  ],
  "initial_paid_amount": "2000.00",
  "payment_method": "Cash",
  "notes": "Delivered to shop"
}
```

### Sample Payment Settlement Request (`POST /api/v1/credit/payments`):
```json
{
  "transaction_type": "given",
  "transaction_id": 1,
  "amount": "1500.00",
  "payment_method": "QR / Fonepay",
  "reference": "QR-984123",
  "payment_date": "2026-10-03",
  "notes": "Partial settlement"
}
```

---

## Cheque Management Endpoints

| Method | Endpoint | Auth | Permission | Description |
|--------|----------|------|------------|-------------|
| GET | /cheques/ | Yes | Staff+ | List cheques with filters (type: GIVEN/RECEIVED, status, search) |
| GET | /cheques/summary | Yes | Staff+ | Cheques KPI summary (total given/received, pending, cleared, bounced) |
| POST | /cheques/ | Yes | Staff+ | Create new cheque given to supplier or received from customer |
| GET | /cheques/{id} | Yes | Staff+ | Retrieve detailed cheque record |
| PATCH | /cheques/{id}/status | Yes | Staff+ | Update cheque status (PENDING, CLEARED, BOUNCED, CANCELLED) |

### Sample Cheque Create Request (`POST /api/v1/cheques/`):
```json
{
  "cheque_type": "RECEIVED",
  "cheque_number": "CHQ-11002",
  "bank_name": "Nabil Bank",
  "amount": "45000.00",
  "cheque_date": "2026-10-15",
  "customer_id": 1,
  "notes": "Advance for grocery order"
}
```

---

## Notifications & Business Alerts Endpoints

| Method | Endpoint | Auth | Permission | Description |
|--------|----------|------|------------|-------------|
| GET | /notifications/alerts-summary | Yes | Staff+ | Central Section 18 business alert counters |
| GET | /notifications/unread-count | Yes | Authenticated | Count of unread notifications for bell badge |
| GET | /notifications/popups | Yes | Authenticated | Active in-app popup notifications |
| GET | /notifications/ | Yes | Authenticated | List notifications with filters (unread_only, priority, module) |
| POST | /notifications/{id}/read | Yes | Authenticated | Mark notification as read |
| POST | /notifications/mark-all-read | Yes | Authenticated | Mark all notifications as read |
| POST | /notifications/{id}/dismiss-popup | Yes | Authenticated | Dismiss in-app popup alert |
| GET | /notifications/settings | Yes | Authenticated | Get user notification and SMS preferences |
| PATCH | /notifications/settings | Yes | Authenticated | Update notification toggles and SMS phone number |
| POST | /notifications/test-sms | Yes | Admin+ | Trigger a test SMS dispatch to verify gateway |

---

## Business Analytics & AI Decision Support Endpoints

| Method | Endpoint | Auth | Permission | Description |
|--------|----------|------|------------|-------------|
| GET | /analytics/summary | Yes | Staff+ | Comprehensive multi-tenant KPIs, margins, inventory velocity, health score, and AI insights |
| POST | /analytics/insights/refresh | Yes | Staff+ | Trigger on-demand AI decision support advice refresh |

### Example Analytics Request
```http
GET /api/v1/analytics/summary?days=30&include_ai=true
Authorization: Bearer <jwt-token>
```

### Example Analytics Response
```json
{
  "period_days": 30,
  "revenue": 145000.00,
  "purchases": 98000.00,
  "purchase_count": 58,
  "expenses": 12500.00,
  "expense_count": 12,
  "gross_profit": 47000.00,
  "net_profit": 34500.00,
  "net_margin_pct": 23.8,
  "gross_margin_pct": 32.4,
  "growth_pct": 14.5,
  "sales_count": 84,
  "average_order_value": 1726.19,
  "total_products": 120,
  "inventory_valuation": 412000.00,
  "retail_valuation": 560000.00,
  "low_stock_count": 3,
  "out_of_stock_count": 0,
  "fast_moving_products": [
    {"id": 1, "name": "Basmati Rice 25kg", "sku": "RICE-01", "sold_units": 45, "revenue": 112500.00}
  ],
  "slow_moving_products": [
    {"id": 4, "name": "Special Spice Mix", "sku": "SPICE-04", "stock": 15, "tied_up_capital": 3500.00}
  ],
  "top_expense_categories": [
    {"category": "Rent", "amount": 8000.00, "percentage": 64.0}
  ],
  "receivables_total": 24000.00,
  "receivables_overdue": 4500.00,
  "payables_total": 18000.00,
  "payables_overdue": 0.00,
  "working_capital_net": 6000.00,
  "cheques_due_7d": 2,
  "cheques_due_amount": 15000.00,
  "daily_trend": [
    {"date": "Oct 01", "total": 5200.0}
  ],
  "period_trend": [
    {"date": "Oct 01", "sales": 5200.00, "purchases": 1200.00, "expenses": 350.00}
  ],
  "health_score": 88,
  "health_grade": "Excellent",
  "ai_insights": {
    "source": "local_rules",
    "provider": "BizFlow Deterministic Engine",
    "model": "Rules-v2.1",
    "health_score": 88,
    "executive_summary": "Strong financial health (88/100) with robust 23.8% net margins and controlled customer credit risk.",
    "action_plan": [
      {
        "category": "Growth",
        "priority": "Low",
        "title": "Capitalize on high-margin product expansion",
        "detail": "Current financial and stock indicators are balanced. Explore volume purchase discounts with key suppliers."
      }
    ],
    "cashflow_outlook": "Positive working capital buffer of Rs. 6,000.00. Short-term obligations are covered by active trade receivables.",
    "growth_opportunities": "Boost stock allocation for 'Basmati Rice 25kg', which generated the highest sales velocity this period.",
    "timestamp": 1728475200.0
  }
}
```

---

### Selectable Chart Series

`GET /analytics/summary` also returns `purchase_count`, `expense_count`, and `period_trend`. The trend uses daily buckets for 7/30-day windows, weekly buckets for 90 days, and monthly buckets for 365 days. Each point contains `date`, `sales`, `purchases`, and `expenses`, with missing periods represented as zero. The existing `daily_trend` field remains available for compatibility.

## Versioning

Current version: `v1`

Future breaking changes will be released as `/api/v2/`. The `v1` API will remain supported for at least 12 months after `v2` launch.
