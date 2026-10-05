# FastAPI REST API Endpoints Specification

> **Base URL**: `http://localhost:8001/api/v1/`  
> **Interactive Documentation**: `http://localhost:8001/api/docs` (Swagger UI) / `http://localhost:8001/api/redoc` (ReDoc)

---

## 1. System & Health (`/api/v1/health`)

### `GET /api/v1/health`
Checks API readiness and database connectivity.
- **Auth**: None (Public)
- **Response `200 OK`**:
```json
{
  "status": "healthy",
  "database": "connected",
  "api": "fastapi"
}
```

---

## 2. Authentication (`/api/v1/auth/`)

### `POST /api/v1/auth/login`
Authenticate user with email/password and obtain JWT access & refresh tokens.
- **Request Body**:
```json
{
  "email": "cashier@bizflow.com",
  "password": "Password123!"
}
```
- **Response `200 OK`**:
```json
{
  "access_token": "eyJhbGciOi...",
  "refresh_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": 1,
    "email": "cashier@bizflow.com",
    "role": "cashier",
    "company_id": 1
  }
}
```

### `POST /api/v1/auth/refresh`
Rotate expired access token using valid refresh token.
- **Request Body**: `{"refresh_token": "..."}`
- **Response `200 OK`**: `{"access_token": "...", "expires_in": 3600}`

### `POST /api/v1/auth/logout`
Revoke active token and add to `accounts.RevokedToken`.
- **Headers**: `Authorization: Bearer <access_token>`
- **Response `200 OK`**: `{"message": "Logged out successfully"}`

---

## 3. Receivables & Payables (Credit) (`/api/v1/credit/`)

### `GET /api/v1/credit/summary`
Retrieve aggregate credit KPIs for active company.
- **Headers**: `Authorization: Bearer <token>`
- **Response `200 OK`**:
```json
{
  "total_credit_given": "150000.00",
  "total_credit_received": "85000.00",
  "customer_dues": "65000.00",
  "total_credit_taken": "200000.00",
  "supplier_paid": "120000.00",
  "supplier_dues": "80000.00",
  "net_credit_balance": "-15000.00"
}
```

### `GET /api/v1/credit/customers-dues`
List customers with outstanding receivable balances.
- **Headers**: `Authorization: Bearer <token>`
- **Response `200 OK`**:
```json
[
  {
    "customer_id": 12,
    "customer_name": "ABC Enterprises",
    "phone": "9841234567",
    "total_credit": "50000.00",
    "total_paid": "20000.00",
    "remaining_balance": "30000.00",
    "invoice_count": 3
  }
]
```

### `GET /api/v1/credit/ledger/customer/{id}`
Chronological debit/credit transaction ledger with running balance.
- **Headers**: `Authorization: Bearer <token>`
- **Response `200 OK`**:
```json
{
  "customer_id": 12,
  "customer_name": "ABC Enterprises",
  "opening_balance": "0.00",
  "closing_balance": "30000.00",
  "entries": [
    {
      "date": "2026-10-01T10:30:00Z",
      "type": "SALE",
      "reference": "INV-2026-0001",
      "debit": "50000.00",
      "credit": "0.00",
      "running_balance": "50000.00"
    },
    {
      "date": "2026-10-02T14:15:00Z",
      "type": "PAYMENT",
      "reference": "PAY-101",
      "debit": "0.00",
      "credit": "20000.00",
      "running_balance": "30000.00"
    }
  ]
}
```

### `POST /api/v1/credit/payments`
Submit partial or full payment voucher.
- **Request Body**:
```json
{
  "sale_id": 1,
  "amount": "10000.00",
  "payment_method": "Cash",
  "payment_date": "2026-10-03T14:00:00Z",
  "notes": "Partial settlement"
}
```
- **Response `201 Created`**:
```json
{
  "payment_id": 45,
  "amount": "10000.00",
  "remaining_amount": "20000.00",
  "status": "Completed"
}
```
