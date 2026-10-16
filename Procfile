web: gunicorn --chdir backend/django_app config.wsgi:application --bind 0.0.0.0:$PORT --workers 3
api: uvicorn api.main:app --app-dir backend --host 0.0.0.0 --port 8001 --workers 2
