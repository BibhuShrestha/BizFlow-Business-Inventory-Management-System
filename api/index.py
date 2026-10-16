"""
Vercel Serverless WSGI entrypoint for BizFlow Django SSR application.
"""
import os
import sys
from pathlib import Path

# Add root, backend and backend/django_app to sys.path so settings and apps are resolved
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))
sys.path.insert(0, str(BASE_DIR / "backend" / "django_app"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

try:
    import django
    if not django.apps.apps.ready:
        django.setup()

    from django.core.wsgi import get_wsgi_application
    _wsgi_app = get_wsgi_application()

    def app(environ, start_response):
        return _wsgi_app(environ, start_response)
except Exception:
    import traceback
    _error_trace = traceback.format_exc()
    traceback.print_exc()

    def app(environ, start_response):
        status = "500 Internal Server Error"
        response_headers = [("Content-type", "text/html; charset=utf-8")]
        start_response(status, response_headers)
        html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Startup Error - BizFlow</title></head>
        <body style="font-family:system-ui,sans-serif;padding:30px;background:#f8fafc;color:#1e293b;">
            <h1 style="color:#dc2626;">BizFlow Serverless Startup Error</h1>
            <p>An exception occurred while initializing Django on Vercel:</p>
            <pre style="background:#fee2e2;color:#991b1b;padding:16px;border-radius:8px;overflow-x:auto;font-size:13px;line-height:1.5;">{_error_trace}</pre>
        </body>
        </html>
        """
        return [html.encode("utf-8")]
