# Development Guide

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.11+ | Backend language |
| pip | Latest | Python package manager |
| Git | Latest | Version control |
| VS Code | Latest (recommended) | IDE |

---

## Setup

### 1. Clone the repository

```bash
git clone <repo-url>
cd business_new
```

### 2. Create virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
cp .env.example .env
# Edit .env with your local settings
```

Minimum .env for development:

```
DJANGO_SECRET_KEY=dev-secret-key-change-in-production
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
```

### 5. Run database migrations

```bash
cd backend/django_app
python manage.py migrate
```

### 6. Create admin user

```bash
python manage.py createsuperuser
```

### 7. Seed initial data (roles)

```bash
python manage.py seed_roles
```

### 8. Start development servers

Django (web):
```bash
cd backend/django_app
python manage.py runserver 8000
```

FastAPI (API):
```bash
cd backend
uvicorn api.main:app --reload --port 8001
```

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| DJANGO_SECRET_KEY | Yes | — | Django signing key (50+ chars) |
| DEBUG | No | False | Enable debug mode |
| DATABASE_URL | No | sqlite:///db.sqlite3 | DB connection string |
| ALLOWED_HOSTS | No | localhost,127.0.0.1 | Comma-separated allowed hosts |
| MAIL_SERVER | No | localhost | SMTP server |
| MAIL_PORT | No | 587 | SMTP port |
| MAIL_USERNAME | No | — | SMTP username |
| MAIL_PASSWORD | No | — | SMTP password |
| MAIL_DEFAULT_SENDER | No | — | Default from address |
| GOOGLE_CLIENT_ID | No | — | Google OAuth client ID |
| GOOGLE_CLIENT_SECRET | No | — | Google OAuth client secret |
| JWT_SECRET_KEY | No | Same as DJANGO_SECRET_KEY | JWT signing key |
| JWT_ACCESS_EXPIRE_MINUTES | No | 30 | Access token lifetime |
| JWT_REFRESH_EXPIRE_DAYS | No | 7 | Refresh token lifetime |
| AI_API_KEY | No | — | AI provider API key |
| MAX_UPLOAD_SIZE_MB | No | 5 | Maximum file upload size |

---

## Database

### Development (SQLite)

```
DATABASE_URL=sqlite:///db.sqlite3
```

SQLite database is stored at `backend/django_app/db.sqlite3`.

### Production (PostgreSQL)

```
DATABASE_URL=postgresql://bizflow:password@localhost:5432/bizflow_db
```

Install PostgreSQL adapter:
```bash
pip install psycopg2-binary
```

---

## Creating Migrations

When you change a model:

```bash
cd backend/django_app
python manage.py makemigrations <app_name>
python manage.py migrate
```

Never edit migrations manually. If a migration is wrong, roll it back and recreate.

---

## Running Tests

```bash
# All tests
pytest

# With coverage report
pytest --cov=backend --cov-report=html

# Only unit tests
pytest tests/unit/ -v

# Only API tests
pytest tests/api/ -v

# Specific file
pytest tests/unit/test_sale_service.py -v
```

Coverage report will be at `htmlcov/index.html`.

---

## Code Linting

```bash
# Check code style
ruff check .

# Auto-fix style issues
ruff check . --fix

# Format code
ruff format .
```

---

## API Documentation

When FastAPI is running:
- Swagger UI: http://localhost:8001/api/docs
- ReDoc: http://localhost:8001/api/redoc

---

## Django Admin

When Django is running:
- Admin panel: http://localhost:8000/admin/
- Login with the superuser credentials from step 6

---

## Project Layout

```
business_new/
├── AGENTS.md                     <- AI coding instructions
├── README.md                     <- Project overview
├── .env.example                  <- Environment template
├── .gitignore                    <- Git ignore file
├── requirements.txt              <- Python dependencies
├── pyproject.toml                <- Tool configuration (ruff, pytest)
│
├── docs/                         <- All documentation
│   ├── PRD.md
│   ├── ARCHITECTURE.md
│   ├── DATABASE.md
│   ├── API.md
│   ├── SECURITY.md
│   ├── CODE_STYLE.md
│   ├── DESIGN_SYSTEM.md
│   ├── TESTING.md
│   ├── DEVELOPMENT.md
│   ├── MIGRATION_MAP.md
│   └── MIGRATION_STATUS.md
│
├── backend/
│   ├── django_app/               <- Django web application
│   │   ├── manage.py
│   │   ├── config/               <- Settings, URLs, WSGI
│   │   ├── apps/                 <- Django applications
│   │   ├── templates/            <- HTML templates
│   │   └── static/               <- CSS, JS, images
│   │
│   ├── api/                      <- FastAPI application
│   │   ├── main.py               <- FastAPI app factory
│   │   ├── routers/              <- Route handlers
│   │   ├── schemas/              <- Pydantic schemas
│   │   ├── dependencies/         <- Depends() functions
│   │   └── middleware/           <- Custom middleware
│   │
│   ├── domain/                   <- Shared business logic
│   │   ├── services/             <- Business services
│   │   ├── validators/           <- Pure validation
│   │   └── repositories/        <- Optional data abstractions
│   │
│   └── core/                     <- Shared utilities
│       ├── config.py             <- App config
│       ├── email.py              <- Email service
│       ├── exports.py            <- CSV/Excel export
│       ├── imports.py            <- CSV/Excel import
│       ├── nepali_date.py        <- Nepali calendar
│       ├── exceptions.py         <- Custom exceptions
│       └── logging.py            <- Logging setup
│
├── tests/                        <- Test suite
│   ├── conftest.py
│   ├── factories.py
│   ├── unit/
│   ├── integration/
│   └── api/
│
├── scripts/                      <- Utility scripts
│   └── seed_data.py
│
├── mobile/                       <- Mobile app (future)
└── desktop/                      <- Desktop app (future)
```

---

## Useful Commands

```bash
# Django shell
python manage.py shell

# List all URL routes
python manage.py show_urls

# Check for Django issues
python manage.py check

# Collect static files (production)
python manage.py collectstatic
```

---

## Common Development Workflows

### Adding a new API endpoint

1. Create/update the service method in `backend/domain/services/`
2. Create Pydantic schema in `backend/api/schemas/`
3. Add route in `backend/api/routers/`
4. Register router in `backend/api/main.py`
5. Write tests in `tests/api/`
6. Update `docs/API.md`

### Adding a new Django view

1. Create/update the service method in `backend/domain/services/`
2. Add view function/class in `backend/django_app/apps/<app>/views.py`
3. Add URL pattern in `backend/django_app/apps/<app>/urls.py`
4. Create/update template in `backend/django_app/templates/<app>/`
5. Write tests in `tests/integration/`

### Adding a new model

1. Define model in `backend/django_app/apps/<app>/models.py`
2. Create migration: `python manage.py makemigrations <app>`
3. Apply migration: `python manage.py migrate`
4. Update `docs/DATABASE.md`
5. Update `docs/MIGRATION_MAP.md`
