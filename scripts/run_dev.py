"""
Run both Django (port 8000) and FastAPI (port 8001) development servers simultaneously.
Usage:
    py scripts/run_dev.py
"""
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DJANGO_DIR = ROOT_DIR / "backend" / "django_app"
BACKEND_DIR = ROOT_DIR / "backend"

def main():
    print("=" * 60)
    print("Starting BizFlow Development Servers")
    print("=" * 60)
    print("Django Web UI:        http://127.0.0.1:8000")
    print("Django Admin:         http://127.0.0.1:8000/admin/")
    print("FastAPI REST API:     http://127.0.0.1:8001")
    print("FastAPI Docs (OpenAPI): http://127.0.0.1:8001/api/docs")
    print("Press Ctrl+C to stop all servers.")
    print("=" * 60)

    # Environment with backend on pythonpath
    env = os.environ.copy()
    current_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{DJANGO_DIR};{BACKEND_DIR};{current_pythonpath}"

    py_exe = sys.executable

    # 1. Django Runserver
    django_cmd = [py_exe, str(DJANGO_DIR / "manage.py"), "runserver", "127.0.0.1:8000"]
    django_proc = subprocess.Popen(django_cmd, cwd=str(DJANGO_DIR), env=env)

    # 2. FastAPI Uvicorn
    fastapi_cmd = [py_exe, "-m", "uvicorn", "api.main:app", "--host", "127.0.0.1", "--port", "8001", "--reload"]
    fastapi_proc = subprocess.Popen(fastapi_cmd, cwd=str(BACKEND_DIR), env=env)

    try:
        while True:
            time.sleep(1)
            if django_proc.poll() is not None:
                print("Django server stopped unexpectedly.")
                break
            if fastapi_proc.poll() is not None:
                print("FastAPI server stopped unexpectedly.")
                break
    except KeyboardInterrupt:
        print("\nStopping development servers...")
    finally:
        for p in (django_proc, fastapi_proc):
            if p and p.poll() is None:
                p.terminate()
                try:
                    p.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    p.kill()
        print("All servers stopped.")

if __name__ == "__main__":
    main()
