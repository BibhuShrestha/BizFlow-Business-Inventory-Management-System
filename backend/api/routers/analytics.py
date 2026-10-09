"""
FastAPI REST router for Business Analytics and AI Decision Support.
Prefix: /api/v1/analytics
"""
from typing import Any
from fastapi import APIRouter, Depends, Query, status

from api.deps import get_current_user
from api.schemas.analytics import (
    BusinessAnalyticsResponse,
    RefreshAIInsightsRequest,
    AIInsightsSchema,
)
from domain.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Business Analytics & AI"])


@router.get("/summary", response_model=BusinessAnalyticsResponse, summary="Get Business Analytics & Insights")
def get_analytics_summary(
    days: int = Query(30, ge=1, le=365, description="Analysis lookback window in days"),
    include_ai: bool = Query(True, description="Whether to include AI / Decision support recommendations"),
    force_refresh: bool = Query(False, description="Bypass cache and force refresh AI insights"),
    current_user: Any = Depends(get_current_user),
):
    """
    Retrieve comprehensive multi-tenant business KPIs, margins, inventory velocity,
    cashflow outlook, and AI-driven decision support recommendations.
    """
    company_id = getattr(current_user.active_company, "id", None)
    analytics = AnalyticsService.get_business_analytics(
        company_id=company_id,
        days=days,
        include_ai=include_ai,
        force_ai_refresh=force_refresh,
        user_id=getattr(current_user, "id", None),
    )
    return analytics


@router.post("/insights/refresh", response_model=AIInsightsSchema, summary="Refresh AI Decision Support Insights")
def refresh_ai_insights(
    payload: RefreshAIInsightsRequest,
    current_user: Any = Depends(get_current_user),
):
    """
    Force-refresh AI decision support insights for the active company.
    Employs caching and per-user hourly quota controls.
    """
    company_id = getattr(current_user.active_company, "id", None)
    analytics = AnalyticsService.get_business_analytics(
        company_id=company_id,
        days=payload.days,
        include_ai=True,
        force_ai_refresh=payload.force_refresh,
        user_id=getattr(current_user, "id", None),
    )
    return analytics.get("ai_insights", {})
