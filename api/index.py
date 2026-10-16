"""
Vercel Serverless WSGI entrypoint for BizFlow Django SSR application.
"""
import os
import sys
from pathlib import Path

# Add backend and backend/django_app to sys.path so settings and apps are resolved
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "backend"))
sys.path.insert(0, str(BASE_DIR / "backend" / "django_app"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

import django
django.setup()

from django.core.wsgi import get_wsgi_application

# Vercel looks for 'app' or 'application'
app = get_wsgi_application()
