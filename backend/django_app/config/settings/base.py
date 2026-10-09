"""
Base Django settings for the Business Inventory Management System.

All environment-specific settings (development, production, testing) inherit
from this module. Environment variables are loaded from the .env file.

Do NOT add secrets or environment-specific values here.
"""
import os
from pathlib import Path
from urllib.parse import quote_plus

import environ

# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------
# BASE_DIR points to backend/django_app/ (the directory containing manage.py)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# REPO_ROOT points to business_new/ (the project root)
REPO_ROOT = BASE_DIR.parent.parent

# Ensure backend directory (domain, services, core) is on sys.path
import sys
_BACKEND_DIR = str(BASE_DIR.parent)
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)


# ---------------------------------------------------------------------------
# Environment variables
# ---------------------------------------------------------------------------
env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
)
# Load .env from project root (business_new/.env) if present
environ.Env.read_env(REPO_ROOT / ".env", overwrite=False)

# ---------------------------------------------------------------------------
# Core Django settings
# ---------------------------------------------------------------------------
SECRET_KEY = env("DJANGO_SECRET_KEY", default="change-this-in-production")
DEBUG = env("DEBUG", default=False)
ALLOWED_HOSTS = env("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

# ---------------------------------------------------------------------------
# Installed applications
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Site URL (used for canonical URLs, sitemap, and SEO metadata)
# ---------------------------------------------------------------------------
SITE_URL = env("SITE_URL", default="http://localhost:8000")

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
]

THIRD_PARTY_APPS = [
    "crispy_forms",
    "crispy_bootstrap5",
]

LOCAL_APPS = [
    # Custom User model must come first so AUTH_USER_MODEL resolves correctly.
    "apps.accounts",
    "apps.companies",
    "apps.inventory",
    "apps.sales",
    "apps.purchases",
    "apps.accounting",
    "apps.reports",
    "apps.audit",
    "apps.core_app",
    "apps.dashboard",
    "apps.credit",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ---------------------------------------------------------------------------
# Custom User model
# ---------------------------------------------------------------------------
AUTH_USER_MODEL = "accounts.User"

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "apps.core_app.middleware.SecurityHeadersMiddleware",
    "apps.core_app.middleware.PerformanceTimingMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "apps.accounts.middleware.UserActivityMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# Configurable user online activity threshold (minutes)
USER_ONLINE_TIMEOUT_MINUTES = env.int("USER_ONLINE_TIMEOUT_MINUTES", default=15)


# ---------------------------------------------------------------------------
# URL routing
# ---------------------------------------------------------------------------
ROOT_URLCONF = "config.urls"

# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                # Inject active company into every template (migrated from Flask context processor)
                "apps.core_app.context_processors.active_company",
            ],
        },
    },
]

# ---------------------------------------------------------------------------
# WSGI / ASGI
# ---------------------------------------------------------------------------
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
# Priority: DATABASE_URL env var > individual POSTGRES_* / MYSQL_* vars > SQLite fallback
_db_url = env("DATABASE_URL", default=None)

if not _db_url:
    pg_user = env("POSTGRES_USER", default=None)
    if pg_user:
        pg_password = env("POSTGRES_PASSWORD", default="")
        pg_host = env("POSTGRES_HOST", default="localhost")
        pg_port = env("POSTGRES_PORT", default="5432")
        pg_db = env("POSTGRES_DB", default="inventory_db")
        _db_url = f"postgresql://{pg_user}:{quote_plus(pg_password)}@{pg_host}:{pg_port}/{pg_db}"

if not _db_url:
    mysql_user = env("MYSQL_USER", default=None)
    if mysql_user:
        mysql_password = env("MYSQL_PASSWORD", default="")
        mysql_host = env("MYSQL_HOST", default="localhost")
        mysql_port = env("MYSQL_PORT", default="3306")
        mysql_database = env("MYSQL_DATABASE", default="inventory_db")
        _db_url = f"mysql://{mysql_user}:{quote_plus(mysql_password)}@{mysql_host}:{mysql_port}/{mysql_database}"

if _db_url:
    _cleaned_url = _db_url.replace("mysql+mysqlconnector://", "mysql://")
    _parsed = environ.Env.db_url_config(_cleaned_url)
    if "mysql" in _parsed.get("ENGINE", ""):
        _parsed.setdefault("OPTIONS", {})["charset"] = "utf8mb4"
    DATABASES = {"default": _parsed}
else:
    # Default: SQLite (development / CI)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "inventory.db",
        }
    }

# ---------------------------------------------------------------------------
# Password validation
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Password hashers (Django default PBKDF2 + Flask Werkzeug compatibility)
# ---------------------------------------------------------------------------
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    "apps.accounts.hashers.WerkzeugPasswordHasher",
    "apps.accounts.hashers.WerkzeugScryptPasswordHasher",
    "apps.accounts.hashers.WerkzeugPbkdf2_260000Hasher",
    "apps.accounts.hashers.WerkzeugPbkdf2_600000Hasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------
LOGIN_URL = "/auth/login/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/auth/login/"

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
REMEMBER_COOKIE_HTTPONLY = True

# ---------------------------------------------------------------------------
# Internationalisation
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kathmandu"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "static" / "collected"

# ---------------------------------------------------------------------------
# Media files (user uploads — company logos, etc.)
# ---------------------------------------------------------------------------
MEDIA_URL = env("MEDIA_URL", default="/media/")
MEDIA_ROOT = env("MEDIA_ROOT", default=str(BASE_DIR / "media"))

# ---------------------------------------------------------------------------
# Default primary key field type
# ---------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Email configuration
# ---------------------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("MAIL_SERVER", default="smtp.gmail.com")
EMAIL_PORT = env.int("MAIL_PORT", default=587)
EMAIL_HOST_USER = env("MAIL_USERNAME", default="")
EMAIL_HOST_PASSWORD = env("MAIL_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("MAIL_USE_TLS", default=True)
DEFAULT_FROM_EMAIL = env("MAIL_DEFAULT_SENDER", default="noreply@inventory.com")

# ---------------------------------------------------------------------------
# Google OAuth
# ---------------------------------------------------------------------------
GOOGLE_CLIENT_ID = env("GOOGLE_CLIENT_ID", default="")
GOOGLE_CLIENT_SECRET = env("GOOGLE_CLIENT_SECRET", default="")
GOOGLE_REDIRECT_URI = env("GOOGLE_REDIRECT_URI", default="")

# ---------------------------------------------------------------------------
# JWT (FastAPI uses these; stored in settings so both apps share config)
# ---------------------------------------------------------------------------
JWT_SECRET_KEY = env("JWT_SECRET_KEY", default="change-this-jwt-secret")
JWT_ALGORITHM = env("JWT_ALGORITHM", default="HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = env.int("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", default=60)
JWT_REFRESH_TOKEN_EXPIRE_DAYS = env.int("JWT_REFRESH_TOKEN_EXPIRE_DAYS", default=14)

# ---------------------------------------------------------------------------
# AI Integration (placeholder)
# ---------------------------------------------------------------------------
AI_API_KEY = env("AI_API_KEY", default="")

# ---------------------------------------------------------------------------
# Third-party app configuration
# ---------------------------------------------------------------------------
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# ---------------------------------------------------------------------------
# Security headers (production values; overridden in development)
# ---------------------------------------------------------------------------
X_FRAME_OPTIONS = "SAMEORIGIN"
SECURE_CONTENT_TYPE_NOSNIFF = True

# ---------------------------------------------------------------------------
# Caching (Part 14 Performance)
# ---------------------------------------------------------------------------
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "bizflow_default_cache",
        "TIMEOUT": 300,
        "OPTIONS": {
            "MAX_ENTRIES": 1000
        }
    }
}

# ---------------------------------------------------------------------------
# Logging (Part 14 Structured Logging & Data Redaction)
# ---------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "sensitive_data_filter": {
            "()": "apps.core_app.logging_filters.SensitiveDataFilter",
        },
    },
    "formatters": {
        "verbose": {
            "format": "[%(asctime)s] %(levelname)-8s [%(name)s:%(lineno)d] %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "simple": {
            "format": "%(levelname)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
            "filters": ["sensitive_data_filter"],
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO" if DEBUG else "WARNING",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "bizflow": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "bizflow.auth": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "bizflow.performance": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO" if DEBUG else "WARNING",
    },
}


# ---------------------------------------------------------------------------
# Security & Cookie Hardening (Part 14)
# ---------------------------------------------------------------------------
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
