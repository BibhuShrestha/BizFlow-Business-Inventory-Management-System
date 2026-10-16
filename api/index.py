"""
Vercel Serverless WSGI entrypoint for BizFlow Django SSR application.
"""
import os
import sys
from pathlib import Path

# Add backend/django_app, backend, and project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "backend" / "django_app"))
sys.path.insert(0, str(BASE_DIR / "backend"))
sys.path.append(str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

import traceback

_django_app = None
_init_error = None

try:
    import django
    from django.apps import apps
    if not apps.ready:
        django.setup()

    from django.core.wsgi import get_wsgi_application
    _django_app = get_wsgi_application()
except Exception:
    _init_error = traceback.format_exc()


def wsgi_handler(environ, start_response):
    global _django_app, _init_error
    if _init_error:
        start_response("500 Internal Server Error", [("Content-Type", "text/plain; charset=utf-8")])
        return [f"Django Startup Error:\n\n{_init_error}".encode("utf-8")]

    # Guarantee HTTPS and forwarded proto for Vercel Serverless
    environ["wsgi.url_scheme"] = "https"
    environ["HTTP_X_FORWARDED_PROTO"] = "https"

    try:
        return _django_app(environ, start_response)
    except Exception:
        err = traceback.format_exc()
        start_response("500 Internal Server Error", [("Content-Type", "text/plain; charset=utf-8")])
        return [f"Django Request Error:\n\n{err}".encode("utf-8")]


# Vercel static AST parser looks for module-level 'app' or 'application'
app = wsgi_handler
application = app

