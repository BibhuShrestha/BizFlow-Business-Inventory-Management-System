"""
ReportService -- Dashboard KPIs and financial summary aggregation.
"""
from decimal import Decimal
from django.db.models import Sum, Count, F
from django.utils import timezone
from datetime import timedelta
from domain.models import DashboardMetrics
from apps.sales.models import Sale
from apps.purchases.models import Purchase
from apps.accounting.models import Expense
from apps.inventory.models import Product
from apps.sales.models import Customer


class ReportService:
    """Computes aggregated metrics for reports and dashboard displays."""

    @staticmethod
    def get_dashboard_metrics(company_id: int | None = None) -> DashboardMetrics:
        """Calculate high-level KPI metrics for the active company or global."""
        sales_qs = Sale.objects.filter(is_active=True)
        purch_qs = Purchase.objects.filter(is_active=True)
        exp_qs = Expense.objects.all()
        prod_qs = Product.objects.filter(is_active=True)
        cust_qs = Customer.objects.filter(is_active=True)

        if company_id is not None:
            sales_qs = sales_qs.filter(company_id=company_id)
            purch_qs = purch_qs.filter(company_id=company_id)
            exp_qs = exp_qs.filter(company_id=company_id)
            prod_qs = prod_qs.filter(company_id=company_id)
            cust_qs = cust_qs.filter(company_id=company_id)

        total_sales = sales_qs.aggregate(s=Sum("total"))["s"] or Decimal("0.00")
        total_purch = purch_qs.aggregate(p=Sum("total"))["p"] or Decimal("0.00")
        total_expenses = exp_qs.aggregate(e=Sum("amount"))["e"] or Decimal("0.00")
        gross_profit = total_sales - total_purch - total_expenses

        low_stock_count = prod_qs.filter(current_stock__lte=F("minimum_stock")).count()

        return DashboardMetrics(
            total_sales=total_sales,
            total_purchases=total_purch,
            total_expenses=total_expenses,
            gross_profit=gross_profit,
            total_customers=cust_qs.count(),
            total_products=prod_qs.count(),
            low_stock_count=low_stock_count,
        )

    @staticmethod
    def get_sales_daily_summary(days: int = 7, company_id: int | None = None) -> list[dict]:
        """Return daily sales totals for the last N days."""
        since = timezone.now() - timedelta(days=days)
        qs = Sale.objects.filter(is_active=True, sale_date__gte=since)
        if company_id is not None:
            qs = qs.filter(company_id=company_id)

        # Aggregate by date
        results = []
        for d in range(days):
            day_start = since + timedelta(days=d)
            day_end = day_start + timedelta(days=1)
            day_sales = qs.filter(sale_date__gte=day_start, sale_date__lt=day_end)
            day_total = day_sales.aggregate(s=Sum("total"))["s"] or Decimal("0.00")
            results.append({
                "date": day_start.strftime("%Y-%m-%d"),
                "total": day_total,
                "count": day_sales.count(),
            })
        return results