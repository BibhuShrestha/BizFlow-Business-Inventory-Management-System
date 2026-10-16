"""
Production Server Runner (Local Testing & Single-Server Deployment).

Starts:
    1. Django SSR Web Portal (Port 8000) using Waitress (Windows) or Gunicorn (Linux/macOS)
    2. FastAPI REST API (Port 8001) using Uvicorn

Usage:
    python scripts/run_production.py
"""
import os
import sys
import platform
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"
DJANGO_APP_DIR = BACKEND_DIR / "django_app"

for p in [str(DJANGO_APP_DIR), str(BACKEND_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")


def main():
    print("===================================================================")
    print("      BizFlow Production Server Launcher (Django SSR + FastAPI)    ")
    print("===================================================================")

    # 1. Collectstatic check
    print("[*] Running collectstatic...")
    try:
        subprocess.run(
            [sys.executable, str(DJANGO_APP_DIR / "manage.py"), "collectstatic", "--noinput"],
            check=True,
        )
    except Exception as e:
        print(f"[!] Warning during collectstatic: {e}")

    # 2. Start Servers
    is_windows = platform.system() == "Windows"
    print(f"[*] Detected Operating System: {platform.system()}")

    if is_windows:
        print("[*] Starting Django Web UI on http://127.0.0.1:8000 via Waitress...")
        django_cmd = (
            f'"{sys.executable}" -c '
            '"from waitress import serve; import config.wsgi; serve(config.wsgi.application, host=\'0.0.0.0\', port=8000)"'
        )
    else:
        print("[*] Starting Django Web UI on http://0.0.0.0:8000 via Gunicorn...")
        django_cmd = (
            f"gunicorn config.wsgi:application --chdir {DJANGO_APP_DIR} --bind 0.0.0.0:8000 --workers 3"
        )

    fastapi_cmd = (
        f'"{sys.executable}" -m uvicorn api.main:app --app-dir "{BACKEND_DIR}" --host 0.0.0.0 --port 8001'
    )

    print("[*] Starting FastAPI REST API on http://127.0.0.1:8001 via Uvicorn...")
    print("\nPress Ctrl+C to terminate both servers.\n")

    p_django = subprocess.Popen(django_cmd, shell=True, cwd=str(DJANGO_APP_DIR))
    p_fastapi = subprocess.Popen(fastapi_cmd, shell=True, cwd=str(BASE_DIR))

    try:
        p_django.wait()
        p_fastapi.wait()
    except KeyboardInterrupt:
        print("\n[*] Shutting down servers gracefully...")
        p_django.terminate()
        p_fastapi.terminate()
        print("[+] Servers stopped.")


if __name__ == "__main__":
    main()
