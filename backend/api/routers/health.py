"""Health-check router for the FastAPI application.

Mirrors the Flask /health endpoint and the Django health_check view.
"""
from django.db import connection
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    database: str
    api: str = "fastapi"


@router.get("/health", response_model=HealthResponse, summary="Application health check")
def health_check():
    """Return the application and database connectivity status."""
    try:
        connection.ensure_connection()
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    return HealthResponse(status="healthy", database=db_status)
