"""Development settings -- DEBUG on, relaxed security, SQLite default."""
from .base import *  # noqa: F401, F403

DEBUG = True
ALLOWED_HOSTS = ["*"]

# Insecure cookies are fine on localhost
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "https://*.pinggy.link",
    "https://*.trycloudflare.com",
    "https://*.lhr.life",
    "https://*.ngrok-free.app",
    "https://*.serveousercontent.com",
]

# Use real SMTP if credentials are configured in .env; otherwise fallback to console
_mail_user = env("MAIL_USERNAME", default="").strip()
_mail_pass = env("MAIL_PASSWORD", default="").strip()
if _mail_user and _mail_pass and "your_email" not in _mail_user:
    EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend")
else:
    EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")

# Disable browser-side caching during development
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}
