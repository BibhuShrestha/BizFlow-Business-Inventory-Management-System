"""
Vercel Serverless ASGI entrypoint for BizFlow FastAPI REST API (/api/v1/).
"""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "backend" / "django_app"))
sys.path.insert(0, str(BASE_DIR / "backend"))
sys.path.append(str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

import traceback

_fastapi_app = None
_init_error = None

try:
    import django
    from django.apps import apps
    if not apps.ready:
        django.setup()

    from backend.api.main import app as _inner_app
    _fastapi_app = _inner_app
except Exception:
    _init_error = traceback.format_exc()


async def asgi_handler(scope, receive, send):
    global _fastapi_app, _init_error
    if _init_error:
        body = f"FastAPI Startup Error:\n\n{_init_error}".encode("utf-8")
        await send({
            "type": "http.response.start",
            "status": 500,
            "headers": [
                [b"content-type", b"text/plain; charset=utf-8"],
                [b"content-length", str(len(body)).encode("ascii")],
            ],
        })
        await send({
            "type": "http.response.body",
            "body": body,
        })
        return

    try:
        await _fastapi_app(scope, receive, send)
    except Exception:
        err = traceback.format_exc()
        body = f"FastAPI Request Error:\n\n{err}".encode("utf-8")
        await send({
            "type": "http.response.start",
            "status": 500,
            "headers": [
                [b"content-type", b"text/plain; charset=utf-8"],
                [b"content-length", str(len(body)).encode("ascii")],
            ],
        })
        await send({
            "type": "http.response.body",
            "body": body,
        })


# Vercel static AST parser looks for top-level module assigns 'app' or 'application'
app = asgi_handler
application = app

