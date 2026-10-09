"""
AnalyticsService -- Resource-efficient Business Analytics & Decision Support.

Performs deterministic multi-tenant financial, inventory, and working capital
calculations using single-pass database aggregation and bounded date intervals.
"""
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from django.db.models import Count, F, Q, Sum
from django.db.models.functions import TruncDate, TruncMonth, TruncWeek
from django.utils import timezone

from apps.accounting.models import Expense
from apps.credit.models import Cheque
from apps.inventory.models import Product
from apps.purchases.models import Purchase
from apps.sales.models import Sale, SaleItem
from domain.services.credit_service import CreditService
from domain.services.stock_service import StockService
from integrations.ai_analytics import AIAnalyticsService, LocalDeterministicAdvisor


class AnalyticsService:
    """Computes comprehensive, resource-efficient business analytics and intelligence."""

    @classmethod
    def get_business_analytics(
        cls,
        company_id: int | None = None,
        days: int = 30,
        include_ai: bool = False,
        force_ai_refresh: bool = False,
        user_id: int | None = None,
    ) -> dict[str, Any]:
        """
        Aggregate complete business KPIs for the given period (default 30 days).
        Uses single-query database aggregations and returns structured analytics.
        """
        now = timezone.now()
        start_date = now - timedelta(days=days)
        prior_start_date = start_date - timedelta(days=days)

        # ---------------------------------------------------------------------
        # 1. Base Querysets with Multi-Tenancy Scoping
        # ---------------------------------------------------------------------
        sales_qs = Sale.objects.filter(is_active=True)
        purch_qs = Purchase.objects.filter(is_active=True)
        exp_qs = Expense.objects.all()
        prod_qs = Product.objects.filter(is_active=True)

        if company_id is not None:
            sales_qs = sales_qs.filter(company_id=company_id)
            purch_qs = purch_qs.filter(company_id=company_id)
            exp_qs = exp_qs.filter(company_id=company_id)
            prod_qs = prod_qs.filter(company_id=company_id)

        # ---------------------------------------------------------------------
        # 2. Financial Metrics (Current Period vs Prior Period)
        # ---------------------------------------------------------------------
        curr_sales = sales_qs.filter(sale_date__gte=start_date, sale_date__lte=now)
        curr_purch = purch_qs.filter(purchase_date__gte=start_date, purchase_date__lte=now)
        curr_exp = exp_qs.filter(expense_date__gte=start_date, expense_date__lte=now)

        revenue_agg = curr_sales.aggregate(total=Sum("total"), count=Count("id"))
        revenue = revenue_agg["total"] or Decimal("0.00")
        sales_count = revenue_agg["count"] or 0

        purch_agg = curr_purch.aggregate(total=Sum("total"), count=Count("id"))
        purchases = purch_agg["total"] or Decimal("0.00")
        purchase_count = purch_agg["count"] or 0

        exp_agg = curr_exp.aggregate(total=Sum("amount"), count=Count("id"))
        expenses = exp_agg["total"] or Decimal("0.00")
        expense_count = exp_agg["count"] or 0

        # Estimated Gross and Net Profit
        gross_profit = revenue - purchases
        net_profit = gross_profit - expenses
        net_margin_pct = float((net_profit / revenue) * 100) if revenue > 0 else 0.0
        gross_margin_pct = float((gross_profit / revenue) * 100) if revenue > 0 else 0.0

        # Prior period comparison for growth percentage
        prior_sales = sales_qs.filter(sale_date__gte=prior_start_date, sale_date__lt=start_date)
        prior_rev = prior_sales.aggregate(total=Sum("total"))["total"] or Decimal("0.00")
        if prior_rev > 0:
            growth_pct = float(((revenue - prior_rev) / prior_rev) * 100)
        else:
            growth_pct = 100.0 if revenue > 0 else 0.0

        avg_order_value = (revenue / sales_count) if sales_count > 0 else Decimal("0.00")

        # ---------------------------------------------------------------------
        # 3. Expense Categorization Breakdown (Top categories)
        # ---------------------------------------------------------------------
        exp_by_category = (
            curr_exp.values("category")
            .annotate(total=Sum("amount"))
            .order_by("-total")[:5]
        )
        total_exp_float = float(expenses) if expenses > 0 else 1.0
        top_expense_categories = [
            {
                "category": item["category"],
                "amount": item["total"],
                "percentage": round((float(item["total"]) / total_exp_float) * 100, 1),
            }
            for item in exp_by_category
        ]

        # ---------------------------------------------------------------------
        # 4. Inventory Valuation & Velocity (Fast-moving & Stagnant items)
        # ---------------------------------------------------------------------
        total_products = prod_qs.count()
        val_agg = prod_qs.aggregate(
            cost_valuation=Sum(F("current_stock") * F("purchase_price")),
            retail_valuation=Sum(F("current_stock") * F("selling_price")),
        )
        inventory_valuation = val_agg["cost_valuation"] or Decimal("0.00")
        retail_valuation = val_agg["retail_valuation"] or Decimal("0.00")

        low_stock_count = StockService.low_stock_products(company_id=company_id).count()
        out_of_stock_count = StockService.out_of_stock_products(company_id=company_id).count()

        # Fast-moving products in current period
        fast_moving_raw = (
            SaleItem.objects.filter(sale__in=curr_sales)
            .values("product__id", "product__name", "product__sku")
            .annotate(sold_qty=Sum("quantity"), sold_rev=Sum("total"))
            .order_by("-sold_qty")[:5]
        )
        fast_moving_products = [
            {
                "id": p["product__id"],
                "name": p["product__name"],
                "sku": p["product__sku"],
                "sold_units": p["sold_qty"] or 0,
                "revenue": p["sold_rev"] or Decimal("0.00"),
            }
            for p in fast_moving_raw
        ]

        # Slow-moving / Stagnant stock: Products with stock > 0 but 0 sales in period
        sold_prod_ids = curr_sales.values_list("items__product_id", flat=True).distinct()
        slow_moving_raw = (
            prod_qs.filter(current_stock__gt=0)
            .exclude(id__in=sold_prod_ids)
            .annotate(stock_val=F("current_stock") * F("purchase_price"))
            .order_by("-stock_val")[:5]
        )
        slow_moving_products = [
            {
                "id": p.id,
                "name": p.name,
                "sku": p.sku,
                "stock": p.current_stock,
                "tied_up_capital": p.current_stock * p.purchase_price,
            }
            for p in slow_moving_raw
        ]

        # ---------------------------------------------------------------------
        # 5. Working Capital, Debtors & Creditors
        # ---------------------------------------------------------------------
        credit_summary = CreditService.get_credit_summary(company_id=company_id)
        receivables_total = credit_summary.get("customer_due", Decimal("0.00"))
        receivables_overdue = credit_summary.get("overdue_given_amount", Decimal("0.00"))
        payables_total = credit_summary.get("supplier_due", Decimal("0.00"))
        payables_overdue = credit_summary.get("overdue_taken_amount", Decimal("0.00"))
        working_capital_net = receivables_total - payables_total

        # Cheques maturing within next 7 days
        cheque_7d_date = (now + timedelta(days=7)).date()
        cheque_qs = Cheque.objects.filter(
            status=Cheque.STATUS_PENDING,
            cheque_date__gte=now.date(),
            cheque_date__lte=cheque_7d_date,
        )
        if company_id is not None:
            cheque_qs = cheque_qs.filter(company_id=company_id)
        cheques_due_7d = cheque_qs.count()
        cheques_due_amount = cheque_qs.aggregate(t=Sum("amount"))["t"] or Decimal("0.00")

        # ---------------------------------------------------------------------
        # 6. Transaction trends, grouped to keep charts useful at every period size.
        if days <= 30:
            truncation = TruncDate
            cursor = start_date.date()
            last_bucket = now.date()
            step = "day"
        elif days <= 90:
            truncation = TruncWeek
            cursor = start_date.date() - timedelta(days=start_date.date().weekday())
            last_bucket = now.date() - timedelta(days=now.date().weekday())
            step = "week"
        else:
            truncation = TruncMonth
            cursor = date(start_date.year, start_date.month, 1)
            last_bucket = date(now.year, now.month, 1)
            step = "month"

        bucket_dates = []
        while cursor <= last_bucket:
            bucket_dates.append(cursor)
            if step == "day":
                cursor += timedelta(days=1)
            elif step == "week":
                cursor += timedelta(weeks=1)
            else:
                cursor = date(cursor.year + (cursor.month // 12), (cursor.month % 12) + 1, 1)

        def totals_by_period(
            queryset, date_field: str, amount_field: str
        ) -> dict[date, Decimal]:
            rows = (
                queryset.annotate(bucket=truncation(date_field))
                .values("bucket")
                .annotate(total=Sum(amount_field))
                .order_by("bucket")
            )
            totals = {}
            for row in rows:
                bucket = row["bucket"]
                if hasattr(bucket, "date"):
                    bucket = bucket.date()
                totals[bucket] = row["total"] or Decimal("0.00")
            return totals

        sales_by_period = totals_by_period(curr_sales, "sale_date", "total")
        purchases_by_period = totals_by_period(curr_purch, "purchase_date", "total")
        expenses_by_period = totals_by_period(curr_exp, "expense_date", "amount")
        period_trend = []
        for bucket in bucket_dates:
            label = bucket.strftime("%b %Y" if step == "month" else "%b %d")
            period_trend.append({
                "date": label,
                "sales": sales_by_period.get(bucket, Decimal("0.00")),
                "purchases": purchases_by_period.get(bucket, Decimal("0.00")),
                "expenses": expenses_by_period.get(bucket, Decimal("0.00")),
            })

        # ---------------------------------------------------------------------
        # 7. Legacy 15-day daily sales trend retained for existing API clients.
        daily_trend = []
        for d in range(14, -1, -1):
            day_target = (now - timedelta(days=d)).date()
            day_sales = sales_qs.filter(sale_date__date=day_target)
            day_total = day_sales.aggregate(t=Sum("total"))["t"] or Decimal("0.00")
            daily_trend.append({
                "date": day_target.strftime("%b %d"),
                "total": float(day_total),
            })

        # ---------------------------------------------------------------------
        # 8. Deterministic Business Health Score (0 - 100)
        # ---------------------------------------------------------------------
        score = 80  # Base benchmark
        # Margin factor (+/- 15 pts)
        if net_margin_pct >= 25.0:
            score += 15
        elif net_margin_pct >= 15.0:
            score += 10
        elif net_margin_pct < 0.0:
            score -= 20
        elif net_margin_pct < 5.0:
            score -= 10

        # Stock availability factor (+/- 10 pts)
        if out_of_stock_count > 3:
            score -= 15
        elif out_of_stock_count > 0:
            score -= 8

        # Overdue debt factor (+/- 15 pts)
        if receivables_total > 0 and (receivables_overdue / receivables_total) > 0.4:
            score -= 15
        elif receivables_overdue > 0:
            score -= 5
        else:
            score += 5

        health_score = max(10, min(100, score))
        if health_score >= 85:
            health_grade = "Excellent"
        elif health_score >= 70:
            health_grade = "Healthy"
        elif health_score >= 50:
            health_grade = "Attention Needed"
        else:
            health_grade = "Critical Risk"

        analytics_data = {
            "period_days": days,
            "revenue": revenue,
            "purchases": purchases,
            "purchase_count": purchase_count,
            "expenses": expenses,
            "expense_count": expense_count,
            "gross_profit": gross_profit,
            "net_profit": net_profit,
            "net_margin_pct": round(net_margin_pct, 1),
            "gross_margin_pct": round(gross_margin_pct, 1),
            "growth_pct": round(growth_pct, 1),
            "sales_count": sales_count,
            "average_order_value": avg_order_value,
            "total_products": total_products,
            "inventory_valuation": inventory_valuation,
            "retail_valuation": retail_valuation,
            "low_stock_count": low_stock_count,
            "out_of_stock_count": out_of_stock_count,
            "fast_moving_products": fast_moving_products,
            "slow_moving_products": slow_moving_products,
            "top_expense_categories": top_expense_categories,
            "receivables_total": receivables_total,
            "receivables_overdue": receivables_overdue,
            "payables_total": payables_total,
            "payables_overdue": payables_overdue,
            "working_capital_net": working_capital_net,
            "cheques_due_7d": cheques_due_7d,
            "cheques_due_amount": cheques_due_amount,
            "daily_trend": daily_trend,
            "period_trend": period_trend,
            "health_score": health_score,
            "health_grade": health_grade,
        }

        # ---------------------------------------------------------------------
        # 9. Optional AI / Decision Support Insights
        # ---------------------------------------------------------------------
        if include_ai:
            ai_insights = AIAnalyticsService.get_insights(
                summary_data=analytics_data,
                company_id=company_id,
                force_refresh=force_ai_refresh,
                user_id=user_id,
            )
            analytics_data["ai_insights"] = ai_insights
        else:
            # Deterministic advisor recommendations generated instantly
            analytics_data["ai_insights"] = LocalDeterministicAdvisor.generate_insights(analytics_data)

        return analytics_data
