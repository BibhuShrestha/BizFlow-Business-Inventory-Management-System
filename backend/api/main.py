"""
FastAPI application entry point.

Architecture:
- FastAPI handles the REST API layer (/api/v1/...).
- Django handles the Web UI (server-side rendered templates).
- Both apps share the same database via Django ORM.
- FastAPI initialises Django at startup so it can use Django models/ORM.

Start the API server:
    uvicorn api.main:app --reload --host 0.0.0.0 --port 8001
"""
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ---------------------------------------------------------------------------
# Bootstrap Django so FastAPI can use Django ORM and settings.
# Both django_app and backend directories must be on sys.path.
# ---------------------------------------------------------------------------
_DJANGO_APP_DIR = str(Path(__file__).resolve().parent.parent / "django_app")
_BACKEND_DIR = str(Path(__file__).resolve().parent.parent)
for _p in [_DJANGO_APP_DIR, _BACKEND_DIR]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

import django  # noqa: E402

django.setup()

# ---------------------------------------------------------------------------
# Import routers (added incrementally in Parts 13-16)
# ---------------------------------------------------------------------------
from api.routers import health, auth, credit, cheques, notifications  # noqa: E402

# from api.routers import auth, users, companies, sellers
# from api.routers import products, inventory, customers, suppliers
# from api.routers import sales, purchases, expenses, reports


# ---------------------------------------------------------------------------
# Lifespan handler (startup / shutdown hooks)
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup/shutdown tasks."""
    yield


# ---------------------------------------------------------------------------
# FastAPI application instance
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Business Inventory Management API",
    description=(
        "REST API for the Business Inventory Management System. "
        "Provides JSON endpoints for all business operations. "
        "Web UI is served by the Django application on port 8000."
    ),
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS middleware
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Register routers
# ---------------------------------------------------------------------------
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(auth.router, prefix="/api/v1")
app.include_router(credit.router, prefix="/api/v1")
app.include_router(cheques.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")