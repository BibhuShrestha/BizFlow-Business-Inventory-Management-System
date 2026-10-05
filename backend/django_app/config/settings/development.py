"""Development settings -- DEBUG on, relaxed security, SQLite default."""
from .base import *  # noqa: F401, F403

DEBUG = True
ALLOWED_HOSTS = ["*"]

# Insecure cookies are fine on localhost
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Show emails in the console instead of sending them
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Disable browser-side caching during development
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}
