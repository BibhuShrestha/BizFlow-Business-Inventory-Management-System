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

import logging
import traceback

_logger = logging.getLogger("vercel.asgi")

try:
    import django
    from django.apps import apps
    if not apps.ready:
        django.setup()

    from backend.api.main import app as fastapi_app
    app = fastapi_app
except Exception:
    err_trace = traceback.format_exc()
    _logger.error("FastAPI Startup Error:\n%s", err_trace)
    from fastapi import FastAPI
    from fastapi.responses import PlainTextResponse

    app = FastAPI(title="BizFlow API Error Gateway")

    @app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
    async def _startup_error_fallback(path_name: str):
        return PlainTextResponse("Internal Server Error: Application failed to initialize.", status_code=500)

application = app


