"""
Vercel Serverless ASGI entrypoint for BizFlow FastAPI REST API (/api/v1/).
"""
import os
import sys
from pathlib import Path

# Add root, backend and backend/django_app to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))
sys.path.insert(0, str(BASE_DIR / "backend" / "django_app"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

import django
if not django.apps.apps.ready:
    django.setup()

from backend.api.main import app
