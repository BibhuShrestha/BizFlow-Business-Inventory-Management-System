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

import django
from django.apps import apps
if not apps.ready:
    django.setup()

from django.core.wsgi import get_wsgi_application

# Vercel static AST parser looks for module-level 'app' or 'application'
app = get_wsgi_application()
application = app
