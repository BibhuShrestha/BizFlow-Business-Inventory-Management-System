"""
Pydantic schemas for Business Analytics and AI Decision Support.
"""
from decimal import Decimal
from typing import Any, List, Optional
from pydantic import BaseModel, Field


class FastMovingProductSchema(BaseModel):
    id: int
    name: str
    sku: str
    sold_units: int
    revenue: Decimal


class SlowMovingProductSchema(BaseModel):
    id: int
    name: str
    sku: str
    stock: int
    tied_up_capital: Decimal


class ExpenseCategorySchema(BaseModel):
    category: str
    amount: Decimal
    percentage: float


class DailyTrendSchema(BaseModel):
    date: str
    total: float


class PeriodTrendSchema(BaseModel):
    date: str
    sales: Decimal
    purchases: Decimal
    expenses: Decimal


class ActionPlanItemSchema(BaseModel):
    category: str
    priority: str
    title: str
    detail: str


class AIInsightsSchema(BaseModel):
    source: str
    provider: str
    model: str
    health_score: int
    executive_summary: str
    action_plan: List[ActionPlanItemSchema] = []
    cashflow_outlook: str
    growth_opportunities: str
    timestamp: float
    rate_limited: Optional[bool] = False
    rate_limit_message: Optional[str] = None


class BusinessAnalyticsResponse(BaseModel):
    period_days: int
    revenue: Decimal
    purchases: Decimal
    purchase_count: int
    expenses: Decimal
    expense_count: int
    gross_profit: Decimal
    net_profit: Decimal
    net_margin_pct: float
    gross_margin_pct: float
    growth_pct: float
    sales_count: int
    average_order_value: Decimal
    total_products: int
    inventory_valuation: Decimal
    retail_valuation: Decimal
    low_stock_count: int
    out_of_stock_count: int
    fast_moving_products: List[FastMovingProductSchema] = []
    slow_moving_products: List[SlowMovingProductSchema] = []
    top_expense_categories: List[ExpenseCategorySchema] = []
    receivables_total: Decimal
    receivables_overdue: Decimal
    payables_total: Decimal
    payables_overdue: Decimal
    working_capital_net: Decimal
    cheques_due_7d: int
    cheques_due_amount: Decimal
    daily_trend: List[DailyTrendSchema] = []
    period_trend: List[PeriodTrendSchema] = []
    health_score: int
    health_grade: str
    ai_insights: Optional[AIInsightsSchema] = None


class RefreshAIInsightsRequest(BaseModel):
    days: int = Field(default=30, ge=1, le=365)
    force_refresh: bool = True
