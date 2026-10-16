"""Production settings -- DEBUG off, HTTPS enforced, strict security."""
import warnings
from .base import *  # noqa: F401, F403

DEBUG = False
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
PREFERRED_URL_SCHEME = "https"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin-allow-popups"

if SECRET_KEY in ("change-this-in-production", "change-this-to-a-long-random-secret-key"):  # noqa: F405
    import secrets
    warnings.warn(
        "DJANGO_SECRET_KEY was not set in production environment variables! "
        "Generated an ephemeral SECRET_KEY for this runtime session. "
        "Please configure DJANGO_SECRET_KEY in Vercel settings.",
        RuntimeWarning,
    )
    SECRET_KEY = secrets.token_urlsafe(50)

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

WHITENOISE_MANIFEST_STRICT = False
WHITENOISE_USE_FINDERS = env.bool("WHITENOISE_USE_FINDERS", default=True)

# Structured console logging for production
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": env("DJANGO_LOG_LEVEL", default="INFO"),
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": env("DJANGO_LOG_LEVEL", default="INFO"),
            "propagate": False,
        },
        "django.security": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}

