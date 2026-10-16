# BizFlow Production Deployment & Operations Guide

> **Complete operational reference for deploying BizFlow (Django SSR + FastAPI) to Supabase PostgreSQL and production cloud platforms.**

---

## 1. Production Architecture Overview

BizFlow utilizes a lightweight, high-performance hybrid architecture designed for minimal footprint and maximum reliability:

```text
                           INTERNET
                              │
               ┌──────────────┴──────────────┐
               ▼                             ▼
      ┌─────────────────┐           ┌─────────────────┐
      │   Django SSR    │           │  FastAPI /api/  │
      │   Web Portal    │           │    REST API     │
      │ (Gunicorn+Wait) │           │    (Uvicorn)    │
      └────────┬────────┘           └────────┬────────┘
               │                             │
               │   Django ORM / psycopg2     │
               └──────────────┬──────────────┘
                              ▼
                     ┌─────────────────┐
                     │    Supabase     │
                     │   PostgreSQL    │
                     └─────────────────┘
```

- **Frontend**: Django Server-Side Rendered (SSR) HTML templates with custom Vanilla CSS and Vanilla JavaScript.
- **Backend**: Django 5.1+ / 6.0 engine handling session authentication, admin, and views.
- **API**: FastAPI (`/api/v1/`) with JWT authentication for desktop and mobile clients.
- **Database**: PostgreSQL hosted on Supabase (with direct session and transaction pooling modes).
- **Static Assets**: Served directly and efficiently via WhiteNoise with compression and cache-busting manifests.

---

## 2. Environment Configuration

Create a production `.env` file or define these variables in your hosting dashboard (e.g. Render, Railway, Fly.io, Heroku):

```env
# --- Application Mode ---
DJANGO_SETTINGS_MODULE=config.settings.production
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<generate-a-strong-50+-character-random-string>

# --- Supabase PostgreSQL Connection ---
# Option 1: Direct connection (Port 5432 - Recommended for persistent servers & migrations)
DATABASE_URL=postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres?sslmode=require
DB_IS_POOLER=False
DB_SSL_REQUIRE=True

# Option 2: Transaction pooler (Port 6543 - Recommended for serverless/auto-scaled containers)
# DATABASE_URL=postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres?sslmode=require
# DB_IS_POOLER=True

# --- Domains & Network Security ---
DJANGO_ALLOWED_HOSTS=bizflow.yourdomain.com,api.bizflow.yourdomain.com
CSRF_TRUSTED_ORIGINS=https://bizflow.yourdomain.com
CORS_ALLOWED_ORIGINS=https://bizflow.yourdomain.com,app://desktop,app://mobile

# --- FastAPI JWT Auth ---
JWT_SECRET_KEY=<generate-a-strong-random-jwt-key>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=14

# --- Storage & Canonical Site URL ---
SITE_URL=https://bizflow.yourdomain.com
MEDIA_ROOT=media
MEDIA_URL=/media/
```

---

## 3. Deployment Steps

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Database Migration & Verification
```bash
# 1. Run migrations against Supabase PostgreSQL
python backend/django_app/manage.py migrate

# 2. (Optional) Migrate legacy MySQL data and align sequences
python scripts/migrate_mysql_to_supabase.py --fixture backups/bizflow_backup.json

# 3. Verify database integrity
python scripts/verify_database_migration.py
```

### Step 3: Collect Static Files
```bash
python backend/django_app/manage.py collectstatic --noinput
```
Assets are compressed and hashed into `backend/django_app/staticfiles/` and served via WhiteNoise.

### Step 4: Validate Production Security
```bash
python backend/django_app/manage.py check --deploy
```
Ensure **0 issues** are reported.

---

## 4. Running Production Servers

### Option A: Vercel Serverless Deployment
BizFlow provides first-class support for Vercel deployment via `vercel.json` and root WSGI/ASGI entrypoints.

#### 1. Architecture on Vercel
- **Django SSR Web UI**: Routed to `api/index.py` using `@vercel/python` (WSGI).
- **FastAPI REST API**: Routed from `/api/v1/(.*)` to `api/fastapi_entrypoint.py` (ASGI).
- **Static Assets**: Edge-cached directly via Vercel route `/static/(.*)` pointing to `backend/django_app/staticfiles/$1` (generated via `collectstatic`).

#### 2. Vercel Configuration (`vercel.json`)
```json
{
  "version": 2,
  "builds": [
    { "src": "api/index.py", "use": "@vercel/python", "config": { "maxDuration": 60 } },
    { "src": "api/fastapi_entrypoint.py", "use": "@vercel/python", "config": { "maxDuration": 60 } }
  ],
  "routes": [
    { "src": "/static/(.*)", "dest": "/backend/django_app/staticfiles/$1" },
    { "src": "/api/v1/(.*)", "dest": "api/fastapi_entrypoint.py" },
    { "src": "/(.*)", "dest": "api/index.py" }
  ]
}
```

#### 3. Honest Evaluation of Vercel Serverless Constraints
While Vercel offers zero-devops scaling, note these architectural trade-offs:
- **Connection Pooling is Required**: Serverless lambda instances spin up and down concurrently. **Always** use Supabase Transaction Pooler (port `6543`) with `DB_IS_POOLER=True` and `CONN_MAX_AGE=0` to prevent exhausting PostgreSQL connection limits.
- **Read-Only Filesystem**: Serverless runtimes have ephemeral, read-only file systems (except `/tmp`). Persistent media uploads (e.g. logos, attachments) must be directed to Supabase Storage or AWS S3.
- **Execution Timeouts**: Hobby plan functions have a 10s timeout (Pro allows up to 60s). Batch report generations or extensive PDF builds must complete within this window or run asynchronously.
- **Database Migrations**: Do **NOT** run `manage.py migrate` in Vercel build steps. Always run migrations via CLI or CI/CD against the direct connection (port `5432`).

---

### Option B: Containerized / PaaS Deployment (Render / Railway / Fly.io / Heroku)
For persistent servers without serverless execution limits, deploy using the included `Procfile`:
```procfile
web: gunicorn --chdir backend/django_app config.wsgi:application --bind 0.0.0.0:$PORT --workers 3
api: uvicorn api.main:app --app-dir backend --host 0.0.0.0 --port 8001 --workers 2
```

### Option C: Cross-Platform Single Server Runner
```bash
python scripts/run_production.py
```

---

## 5. Health Checks & Monitoring

Both services expose dedicated health-check endpoints for load balancers and uptime monitors:
- **Django SSR Web UI**: `GET https://bizflow.yourdomain.com/health/`
  - Returns: `200 OK` + `{"status": "healthy", "database": "connected"}`
- **FastAPI REST API**: `GET https://api.bizflow.yourdomain.com/api/v1/health`
  - Returns: `200 OK` + `{"status": "healthy", "database": "connected", "api": "fastapi"}`

---

## 6. Backup & Recovery Strategy

1. **Automated Supabase Backups**:
   - Supabase automatically performs daily physical backups and point-in-time recovery (PITR) for Pro tiers.
2. **Application-Level Non-Destructive Backups**:
   - Run `python scripts/backup_mysql.py` to generate an isolated, model-validated JSON backup fixture into `backups/`.
3. **Disaster Recovery**:
   - In the event of primary database replacement, execute:
     ```bash
     python scripts/migrate_mysql_to_supabase.py --target-url "<NEW_DATABASE_URL>" --fixture backups/<BACKUP_FILE>.json
     ```

