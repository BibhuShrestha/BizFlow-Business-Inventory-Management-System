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

import django
from django.apps import apps
if not apps.ready:
    django.setup()

from backend.api.main import app as fastapi_app

# Vercel static AST parser looks for top-level module assigns 'app' or 'application'
app = fastapi_app
application = app
