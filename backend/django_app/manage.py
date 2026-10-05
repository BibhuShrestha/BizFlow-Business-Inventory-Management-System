#!/usr/bin/env python
"""Django command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path


def main():
    """Run administrative tasks."""
    # Ensure backend and django_app directories are on sys.path
    backend_dir = str(Path(__file__).resolve().parent.parent)
    django_app_dir = str(Path(__file__).resolve().parent)
    for p in [django_app_dir, backend_dir]:
        if p not in sys.path:
            sys.path.insert(0, p)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Could not import Django. Make sure it is installed and available on your "
            "PYTHONPATH. Did you forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()