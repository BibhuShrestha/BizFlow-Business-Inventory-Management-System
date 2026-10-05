"""
Shared Application Services.

Reusable, framework-agnostic business logic services consumed by:
  - Django Views (SSR UI & Admin)
  - FastAPI Routers (REST API layer)
  - Future Desktop & Mobile Clients
"""
from domain.services.auth_service import AuthService
from domain.services.stock_service import StockService
from domain.services.sale_service import SaleService
from domain.services.purchase_service import PurchaseService
from domain.services.report_service import ReportService
from services.nepali_date import NepaliDateService

__all__ = [
    "AuthService",
    "StockService",
    "SaleService",
    "PurchaseService",
    "ReportService",
    "NepaliDateService",
]