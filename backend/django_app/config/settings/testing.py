"""Testing settings -- in-memory SQLite, CSRF off, email suppressed."""
from .base import *  # noqa: F401, F403

DEBUG = False
TESTING = True

# In-memory SQLite is fast and self-contained for test runs
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Never actually send emails during tests
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Speed up password hashing in tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Disable CSRF checks in tests (test client handles this)
WTF_CSRF_ENABLED = False

ALLOWED_HOSTS = ["*"]
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
