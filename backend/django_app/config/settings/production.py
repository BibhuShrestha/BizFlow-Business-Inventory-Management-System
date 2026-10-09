"""Production settings -- DEBUG off, HTTPS enforced, strict security."""
import warnings
from .base import *  # noqa: F401, F403

DEBUG = False
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
PREFERRED_URL_SCHEME = "https"

from django.core.exceptions import ImproperlyConfigured

if SECRET_KEY == "change-this-in-production":  # noqa: F405
    raise ImproperlyConfigured(
        "DJANGO_SECRET_KEY is using an insecure placeholder value! "
        "A strong, unique SECRET_KEY must be configured in environment variables for production."
    )

