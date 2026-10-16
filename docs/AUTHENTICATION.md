# BizFlow Authentication Architecture & Supabase Integration Guide

> **Authoritative guide on authentication, identity synchronization, session lifecycle, and token verification across Django SSR and FastAPI.**

---

## 1. Authentication Architecture Overview

BizFlow supports a resilient, hybrid authentication mechanism:
1. **Django SSR Web UI**: Standard HTTP-only, secure Django session cookies (`sessionid`), powered by `django.contrib.auth` and styled Django forms.
2. **FastAPI REST API (`/api/v1/`)**: Bearer JWT token authentication in the `Authorization: Bearer <token>` header.
3. **Supabase Auth (Cloud Identity Provider)**: Optional external authentication provider via Supabase GoTrue REST API.
4. **Google OAuth 2.0**: Optional social single sign-on.
5. **Local Offline Fallback**: Complete, zero-dependency authentication using local Argon2/PBKDF2 hashes whenever Supabase credentials are absent.

```text
 ┌────────────────────────────────────────────────────────────────────────┐
 │                              AUTH FLOWS                                │
 └────────────────────────────────────────────────────────────────────────┘

 [ Cashier / User ] (Web Browser)
        │
        ▼
   [ Django SSR: /auth/login/ ]
        │
        ├──> Is SUPABASE_URL configured?
        │       ├── YES: Authenticate via Supabase GoTrue REST API
        │       │        Sync identity to accounts.User (link supabase_uid)
        │       │        Store supabase_access_token in request.session
        │       │
        │       └── NO:  Authenticate against local accounts.User password
        │
        ▼
   [ Issue Django session cookie (HttpOnly, SameSite=Lax, Secure in Prod) ]
        │
        ▼
   [ Access Web Dashboard, Invoices, Inventory ]


 [ Mobile / Desktop / External Client ]
        │
        ▼
   [ FastAPI: /api/v1/auth/login or Bearer Token ]
        │
        ├── Internal JWT: decoded with JWT_SECRET_KEY
        │   └── Resolves user by sub (numeric user.id)
        │
        └── Supabase JWT: decoded with SUPABASE_JWT_SECRET or verified via GoTrue
            └── Resolves user by sub (supabase_uid UUID) or email
            └── Validates active status and enforces require_role(...)
```

---

## 2. Supabase Auth Integration

### 2.1 Configuration
Configure the following variables in `.env` or cloud dashboard:

```env
SUPABASE_URL=https://[your-project-ref].supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_JWT_SECRET=your-supabase-jwt-secret
```

If these environment variables are empty or not configured, the application **automatically runs in offline local mode**, preserving 100% of standard operations without throwing configuration errors.

### 2.2 Client Implementation (`backend/integrations/supabase_client.py`)
BizFlow integrates directly with the Supabase GoTrue REST API using standard `requests` and `python-jose`/`PyJWT`, deliberately avoiding heavy external SDKs:
- `sign_in_with_password(email, password)`: Authenticates user against GoTrue, returning tokens and metadata.
- `sign_up(email, password, metadata)`: Provisions new cloud identity with email and roles.
- `sign_out(access_token)`: Invalidates the cloud session upon web or API logout.
- `verify_jwt(token)`: Offline cryptographic HMAC-SHA256 verification using `SUPABASE_JWT_SECRET` with fallback to online GoTrue `/user` endpoint.
- `sync_to_django_user(supabase_user_data)`: Reconciles cloud identity with local `accounts.User`.

### 2.3 User Identity Synchronization
The local `accounts.User` model contains an indexed `supabase_uid` field (`VARCHAR(64)`):

1. **Resolution Priority**:
   - Match by `supabase_uid`
   - Match by `email` (links `supabase_uid` to existing account seamlessly)
   - Provision new local `User` with a randomized unusable password, assigned company, and `Role.ROLE_STAFF` (or role parsed from metadata).
2. **Multi-Tenancy Scoping**:
   - The synchronized user is assigned to their tenant's active `Company`.
   - All subsequent queries are strictly scoped by `user.active_company_id`.

---

## 3. Web UI Session Lifecycle

1. **Login (`/auth/login/`)**:
   - User submits email and password.
   - `AuthService.authenticate()` verifies credentials against Supabase (if active) or local database.
   - Upon success, `django.contrib.auth.login(request, user)` issues an authenticated session.
   - If Supabase returned an access token, it is securely stored in `request.session["supabase_access_token"]`.
2. **Session Persistence**:
   - Session data is stored in the database (`django_session`).
   - Cookies are protected with `SESSION_COOKIE_HTTPONLY=True` and `SESSION_COOKIE_SECURE=True` in production.
3. **Logout (`/auth/logout/`)**:
   - Retrieves `supabase_access_token` from session and notifies Supabase to invalidate.
   - Flushes Django session via `django.contrib.auth.logout(request)`.

---

## 4. FastAPI REST API Token Authentication (`/api/v1/`)

FastAPI routes protected by `Depends(get_current_user)` or `require_role(...)` accept Bearer tokens in the `Authorization` header:

1. **Internal Token Flow**:
   - Client sends token issued by `/api/v1/auth/login`.
   - Verified against `JWT_SECRET_KEY`.
   - Checked against database token revocation blacklist (`RevokedToken`).
2. **Supabase Token Flow**:
   - Client sends Supabase GoTrue JWT.
   - Verified via `SupabaseAuthClient.verify_jwt(token)`.
   - User resolved via `supabase_uid` or auto-provisioned.
3. **Role-Based Access Control**:
   - Endpoint decorators (e.g. `require_role("admin", "manager")`) check `user.role.name`.
   - Superusers and admins retain unrestricted access across all endpoints.
