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

try:
    import django
    from django.apps import apps
    if not apps.ready:
        django.setup()

    from backend.api.main import app
    application = app
except Exception:
    import traceback
    traceback.print_exc()
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    app = FastAPI()
    _err = traceback.format_exc()

    @app.get("/{full_path:path}")
    async def error_catch(full_path: str):
        return JSONResponse(status_code=500, content={"error": "FastAPI Startup Error", "details": _err})
