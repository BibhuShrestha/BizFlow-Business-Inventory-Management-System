"""
Pytest configuration and shared fixtures for the new Django + FastAPI project.

pytest-django is configured via pyproject.toml:
    DJANGO_SETTINGS_MODULE = "config.settings.testing"
    pythonpath = ["backend/django_app", "backend"]
"""
import os
import sys
from pathlib import Path

import pytest

# Ensure both the django_app and backend directories are on sys.path.
_ROOT = Path(__file__).resolve().parent.parent
_DJANGO_APP = _ROOT / "backend" / "django_app"
_BACKEND = _ROOT / "backend"

for p in [str(_DJANGO_APP), str(_BACKEND)]:
    if p not in sys.path:
        sys.path.insert(0, p)