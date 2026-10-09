"""
AnalyticsService -- Resource-efficient Business Analytics & Decision Support.

Performs deterministic multi-tenant financial, inventory, cash flow, and working capital
calculations using single-pass database aggregation and bounded date intervals.
"""
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

from django.conf import settings
from django.db.models import Count, F, Q, Sum
from django.db.models.functions import TruncDate, TruncMonth, TruncWeek
from django.utils import timezone

from apps.accounting.models import Expense
from apps.credit.models import Cheque
from apps.inventory.models import Product
from apps.purchases.models import Purchase, Supplier
from apps.sales.models import Sale, SaleItem, Payment, Customer
from apps.accounts.models import User
from domain.services.credit_service import CreditService
from domain.services.stock_service import StockService
from integrations.ai_analytics import AIAnalyticsService, LocalDeterministicAdvisor


class AnalyticsService:
    """Computes comprehensive, resource-efficient business analytics and intelligence."""

    @classmethod
    def resolve_date_range(
        cls,
        days: int | None = None,
        period: str | None = None,
        date_from: date | str | None = None,
        date_to: date | str | None = None,
    ) -> tuple[datetime, datetime, datetime, datetime, int, str]:
        """
        Determines current and prior period datetime boundaries.
        Returns: (start_date, end_date, prior_start_date, prior_end_date, delta_days, resolved_period)
        """
        now = timezone.now()
        today = timezone.localdate()

        # 1. Custom date range
        if date_from and date_to:
            if isinstance(date_from, str):
                date_from = datetime.strptime(date_from.strip(), "%Y-%m-%d").date()
            if isinstance(date_to, str):
                date_to = datetime.strptime(date_to.strip(), "%Y-%m-%d").date()

            start_date = timezone.make_aware(datetime.combine(date_from, datetime.min.time()))
            end_date = timezone.make_aware(datetime.combine(date_to, datetime.max.time()))
            delta_days = max(1, (date_to - date_from).days + 1)
            prior_start_date = start_date - timedelta(days=delta_days)
            prior_end_date = start_date
            return start_date, end_date, prior_start_date, prior_end_date, delta_days, "custom"

        # 2. Named period or days count
        p = (period or "").strip().lower()
        if p == "today":
            start_date = timezone.make_aware(datetime.combine(today, datetime.min.time()))
            end_date = now
            delta_days = 1
            prior_start_date = start_date - timedelta(days=1)
            prior_end_date = start_date
            return start_date, end_date, prior_start_date, prior_end_date, delta_days, "today"

        if p == "yesterday":
            yesterday = today - timedelta(days=1)
            start_date = timezone.make_aware(datetime.combine(yesterday, datetime.min.time()))
            end_date = timezone.make_aware(datetime.combine(yesterday, datetime.max.time()))
            delta_days = 1
            prior_start_date = start_date - timedelta(days=1)
            prior_end_date = start_date
            return start_date, end_date, prior_start_date, prior_end_date, delta_days, "yesterday"

        if p in ("this_week", "7d") or days == 7:
            delta_days = 7
            start_date = now - timedelta(days=7)
            end_date = now
            prior_start_date = start_date - timedelta(days=7)
            prior_end_date = start_date
            return start_date, end_date, prior_start_date, prior_end_date, delta_days, "7d"

        if p in ("this_quarter", "90d") or days == 90:
            delta_days = 90
            start_date = now - timedelta(days=90)
            end_date = now
            prior_start_date = start_date - timedelta(days=90)
            prior_end_date = start_date
            return start_date, end_date, prior_start_date, prior_end_date, delta_days, "90d"

        if p in ("this_year", "365d") or days == 365:
            delta_days = 365
            start_date = now - timedelta(days=365)
            end_date = now
            prior_start_date = start_date - timedelta(days=365)
            prior_end_date = start_date
            return start_date, end_date, prior_start_date, prior_end_date, delta_days, "365d"

        if p == "previous_year":
            prev_year = today.year - 1
            start_date = timezone.make_aware(datetime.combine(date(prev_year, 1, 1), datetime.min.time()))
            end_date = timezone.make_aware(datetime.combine(date(prev_year, 12, 31), datetime.max.time()))
            delta_days = 365
            prior_start_date = timezone.make_aware(datetime.combine(date(prev_year - 1, 1, 1), datetime.min.time()))
            prior_end_date = start_date
            return start_date, end_date, prior_start_date, prior_end_date, delta_days, "previous_year"

        # Default: 30 days
        resolved_days = int(days) if days else 30
        delta_days = resolved_days
        start_date = now - timedelta(days=resolved_days)
        end_date = now
        prior_start_date = start_date - timedelta(days=resolved_days)
        prior_end_date = start_date
        return start_date, end_date, prior_start_date, prior_end_date, delta_days, f"{resolved_days}d"

    @classmethod
    def get_business_analytics(
        cls,
        company_id: int | None = None,
        days: int | None = None,
        period: str | None = None,
        date_from: date | str | None = None,
        date_to: date | str | None = None,
        include_ai: bool = False,
        force_ai_refresh: bool = False,
        user_id: int | None = None,
    ) -> dict[str, Any]:
        """
        Aggregate complete, authoritative business KPIs for the given period.
        Uses single-query database aggregations, strict accounting consistency, and multi-tenant scoping.
        """
        now = timezone.now()
        today = timezone.localdate()

        start_date, end_date, prior_start_date, prior_end_date, period_days, period_label = (
            cls.resolve_date_range(days=days, period=period, date_from=date_from, date_to=date_to)
        )

        # ---------------------------------------------------------------------
        # 1. Base Querysets Scoped by Active Company
        # ---------------------------------------------------------------------
        sales_qs = Sale.objects.filter(is_active=True)
        purch_qs = Purchase.objects.filter(is_active=True)
        exp_qs = Expense.objects.all()
        prod_qs = Product.objects.filter(is_active=True)
        cust_qs = Customer.objects.filter(is_active=True)
        supp_qs = Supplier.objects.filter(is_active=True)
        pay_qs = Payment.objects.filter(status__iexact="Completed")

        if company_id is not None:
            sales_qs = sales_qs.filter(company_id=company_id)
            purch_qs = purch_qs.filter(company_id=company_id)
            exp_qs = exp_qs.filter(company_id=company_id)
            prod_qs = prod_qs.filter(company_id=company_id)
            cust_qs = cust_qs.filter(company_id=company_id)
            supp_qs = supp_qs.filter(company_id=company_id)
            pay_qs = pay_qs.filter(Q(sale__company_id=company_id) | Q(purchase__company_id=company_id) | Q(customer__company_id=company_id) | Q(supplier__company_id=company_id))

        # ---------------------------------------------------------------------
        # 2. Sales Analytics & Revenue
        # ---------------------------------------------------------------------
        curr_sales = sales_qs.filter(sale_date__gte=start_date, sale_date__lte=end_date)
        sales_agg = curr_sales.aggregate(
            total=Sum("total"),
            discount=Sum("discount"),
            tax=Sum("tax"),
            count=Count("id"),
        )
        revenue = sales_agg["total"] or Decimal("0.00")
        sales_discount = sales_agg["discount"] or Decimal("0.00")
        sales_tax = sales_agg["tax"] or Decimal("0.00")
        sales_count = sales_agg["count"] or 0
        avg_order_value = (revenue / sales_count) if sales_count > 0 else Decimal("0.00")

        # Period-over-period growth velocity
        prior_sales = sales_qs.filter(sale_date__gte=prior_start_date, sale_date__lt=prior_end_date)
        prior_rev = prior_sales.aggregate(total=Sum("total"))["total"] or Decimal("0.00")
        if prior_rev > 0:
            growth_pct = float(((revenue - prior_rev) / prior_rev) * 100)
        else:
            growth_pct = 100.0 if revenue > 0 else 0.0

        # Snapshot sales metrics for top summary cards
        today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
        sales_today = sales_qs.filter(sale_date__gte=today_start).aggregate(t=Sum("total"))["t"] or Decimal("0.00")
        week_start = now - timedelta(days=7)
        sales_week = sales_qs.filter(sale_date__gte=week_start).aggregate(t=Sum("total"))["t"] or Decimal("0.00")
        month_start = timezone.make_aware(datetime.combine(date(today.year, today.month, 1), datetime.min.time()))
        sales_month = sales_qs.filter(sale_date__gte=month_start).aggregate(t=Sum("total"))["t"] or Decimal("0.00")
        year_start = timezone.make_aware(datetime.combine(date(today.year, 1, 1), datetime.min.time()))
        sales_year = sales_qs.filter(sale_date__gte=year_start).aggregate(t=Sum("total"))["t"] or Decimal("0.00")

        # Sales by payment method (Cash, Bank, Cheque, QR)
        sales_by_method_raw = (
            curr_sales.values("payment_method")
            .annotate(total=Sum("total"), count=Count("id"))
            .order_by("-total")
        )
        total_rev_float = float(revenue) if revenue > 0 else 1.0
        sales_by_payment_method = [
            {
                "method": m["payment_method"] or "Cash",
                "total": m["total"] or Decimal("0.00"),
                "count": m["count"] or 0,
                "percentage": round((float(m["total"] or 0) / total_rev_float) * 100, 1),
            }
            for m in sales_by_method_raw
        ]

        # ---------------------------------------------------------------------
        # 3. Received Payments vs Outstanding Receivables (Strict Cash Accounting)
        # ---------------------------------------------------------------------
        curr_cust_payments = pay_qs.filter(
            payment_date__gte=start_date,
            payment_date__lte=end_date,
        ).filter(Q(sale__isnull=False) | Q(customer__isnull=False))

        cash_received = curr_cust_payments.aggregate(t=Sum("amount"))["t"] or Decimal("0.00")

        # Snapshot received payments
        payments_today = pay_qs.filter(
            payment_date__gte=today_start
        ).filter(Q(sale__isnull=False) | Q(customer__isnull=False)).aggregate(t=Sum("amount"))["t"] or Decimal("0.00")

        payments_month = pay_qs.filter(
            payment_date__gte=month_start
        ).filter(Q(sale__isnull=False) | Q(customer__isnull=False)).aggregate(t=Sum("amount"))["t"] or Decimal("0.00")

        payments_year = pay_qs.filter(
            payment_date__gte=year_start
        ).filter(Q(sale__isnull=False) | Q(customer__isnull=False)).aggregate(t=Sum("amount"))["t"] or Decimal("0.00")

        collection_rate_pct = float((cash_received / revenue) * 100) if revenue > 0 else 0.0

        collections_by_method_raw = (
            curr_cust_payments.values("payment_method")
            .annotate(total=Sum("amount"), count=Count("id"))
            .order_by("-total")
        )
        cash_float = float(cash_received) if cash_received > 0 else 1.0
        collections_by_method = [
            {
                "method": m["payment_method"] or "Cash",
                "total": m["total"] or Decimal("0.00"),
                "count": m["count"] or 0,
                "percentage": round((float(m["total"] or 0) / cash_float) * 100, 1),
            }
            for m in collections_by_method_raw
        ]

        # ---------------------------------------------------------------------
        # 4. Purchases, Operating Expenses, COGS & Profitability
        # ---------------------------------------------------------------------
        curr_purch = purch_qs.filter(purchase_date__gte=start_date, purchase_date__lte=end_date)
        purch_agg = curr_purch.aggregate(total=Sum("total"), count=Count("id"))
        purchases = purch_agg["total"] or Decimal("0.00")
        purchase_count = purch_agg["count"] or 0

        curr_exp = exp_qs.filter(expense_date__gte=start_date, expense_date__lte=end_date)
        exp_agg = curr_exp.aggregate(total=Sum("amount"), count=Count("id"))
        expenses = exp_agg["total"] or Decimal("0.00")
        expense_count = exp_agg["count"] or 0

        # Snapshot expenses
        expenses_today = exp_qs.filter(expense_date__gte=today_start).aggregate(t=Sum("amount"))["t"] or Decimal("0.00")
        expenses_month = exp_qs.filter(expense_date__gte=month_start).aggregate(t=Sum("amount"))["t"] or Decimal("0.00")
        expenses_year = exp_qs.filter(expense_date__gte=year_start).aggregate(t=Sum("amount"))["t"] or Decimal("0.00")

        # Expense categories breakdown
        exp_by_category = (
            curr_exp.values("category")
            .annotate(total=Sum("amount"))
            .order_by("-total")[:6]
        )
        total_exp_float = float(expenses) if expenses > 0 else 1.0
        top_expense_categories = [
            {
                "category": item["category"] or "General",
                "amount": item["total"] or Decimal("0.00"),
                "percentage": round((float(item["total"] or 0) / total_exp_float) * 100, 1),
            }
            for item in exp_by_category
        ]

        # Cost of Goods Sold (COGS) calculated from line items of sold products
        cogs_items = SaleItem.objects.filter(sale__in=curr_sales).aggregate(
            cogs=Sum(F("quantity") * F("product__purchase_price"))
        )["cogs"]

        # If items have reliable purchase prices, use exact COGS; otherwise fall back to period purchase bills
        cogs = cogs_items if (cogs_items is not None and cogs_items > Decimal("0.00")) else purchases
        gross_profit = revenue - cogs
        net_profit = gross_profit - expenses
        gross_margin_pct = float((gross_profit / revenue) * 100) if revenue > 0 else 0.0
        net_margin_pct = float((net_profit / revenue) * 100) if revenue > 0 else 0.0

        # Cash Out & Net Cash Flow
        curr_supp_payments = pay_qs.filter(
            payment_date__gte=start_date,
            payment_date__lte=end_date,
        ).filter(Q(purchase__isnull=False) | Q(supplier__isnull=False))
        cash_paid_suppliers = curr_supp_payments.aggregate(t=Sum("amount"))["t"] or Decimal("0.00")
        total_cash_out = cash_paid_suppliers + expenses
        net_cash_flow = cash_received - total_cash_out

        # ---------------------------------------------------------------------
        # 5. Inventory Valuation, Velocity & Reorder Suggestions
        # ---------------------------------------------------------------------
        total_products = prod_qs.count()
        val_agg = prod_qs.aggregate(
            cost_valuation=Sum(F("current_stock") * F("purchase_price")),
            retail_valuation=Sum(F("current_stock") * F("selling_price")),
            total_stock_units=Sum("current_stock"),
        )
        inventory_valuation = val_agg["cost_valuation"] or Decimal("0.00")
        retail_valuation = val_agg["retail_valuation"] or Decimal("0.00")
        total_stock_units = val_agg["total_stock_units"] or 0

        low_stock_count = StockService.low_stock_products(company_id=company_id).count()
        out_of_stock_count = StockService.out_of_stock_products(company_id=company_id).count()

        # Fast-moving products in current period
        fast_moving_raw = (
            SaleItem.objects.filter(sale__in=curr_sales)
            .values("product__id", "product__name", "product__sku")
            .annotate(sold_qty=Sum("quantity"), sold_rev=Sum("total"))
            .order_by("-sold_qty")[:6]
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

        # Slow-moving / Stagnant stock (products in stock with 0 sales in period)
        sold_prod_ids = curr_sales.values_list("items__product_id", flat=True).distinct()
        slow_moving_raw = (
            prod_qs.filter(current_stock__gt=0)
            .exclude(id__in=sold_prod_ids)
            .annotate(stock_val=F("current_stock") * F("purchase_price"))
            .order_by("-stock_val")[:6]
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

        # Intelligent Reorder Suggestions based on minimum stock threshold
        reorder_candidates = (
            prod_qs.filter(current_stock__lte=F("minimum_stock"))
            .order_by("current_stock")[:8]
        )
        reorder_suggestions = [
            {
                "id": p.id,
                "name": p.name,
                "sku": p.sku,
                "current_stock": p.current_stock,
                "minimum_stock": p.minimum_stock,
                "suggested_order_qty": max(5, (p.minimum_stock * 2) - p.current_stock),
                "unit_cost": p.purchase_price,
                "estimated_cost": max(5, (p.minimum_stock * 2) - p.current_stock) * p.purchase_price,
            }
            for p in reorder_candidates
        ]

        # ---------------------------------------------------------------------
        # 6. Customer & Supplier Balances (Receivables & Payables)
        # ---------------------------------------------------------------------
        credit_summary = CreditService.get_credit_summary(company_id=company_id)
        receivables_total = credit_summary.get("customer_due", Decimal("0.00"))
        receivables_overdue = credit_summary.get("overdue_given_amount", Decimal("0.00"))
        payables_total = credit_summary.get("supplier_due", Decimal("0.00"))
        payables_overdue = credit_summary.get("overdue_taken_amount", Decimal("0.00"))
        working_capital_net = receivables_total - payables_total

        # Top customers by period sales
        top_customers_raw = (
            curr_sales.filter(customer__isnull=False)
            .values("customer__id", "customer__name")
            .annotate(total_spent=Sum("total"), orders_count=Count("id"))
            .order_by("-total_spent")[:5]
        )
        top_customers = [
            {
                "id": c["customer__id"],
                "name": c["customer__name"],
                "total_spent": c["total_spent"] or Decimal("0.00"),
                "orders_count": c["orders_count"] or 0,
            }
            for c in top_customers_raw
        ]

        # Debtors with outstanding balance
        debtors_raw = CreditService.get_customers_dues(company_id=company_id)[:5]
        top_debtors = [
            {
                "id": d["customer"].id,
                "name": d["customer"].name,
                "total_due": d.get("remaining_due", Decimal("0.00")),
            }
            for d in debtors_raw
        ]

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
        # 7. User Activity & System Overview
        # ---------------------------------------------------------------------
        timeout_minutes = getattr(settings, "USER_ONLINE_TIMEOUT_MINUTES", 15)
        online_threshold = now - timedelta(minutes=timeout_minutes)
        total_users = User.objects.count()
        online_users = User.objects.filter(last_activity__gte=online_threshold).count()
        offline_users = max(0, total_users - online_users)
        active_accounts = User.objects.filter(is_active=True).count()
        disabled_accounts = User.objects.filter(is_active=False).count()

        # ---------------------------------------------------------------------
        # 8. Period Trend Grouping for Interactive Visualizations
        # ---------------------------------------------------------------------
        if period_days <= 30:
            truncation = TruncDate
            cursor = start_date.date()
            last_bucket = end_date.date()
            step = "day"
        elif period_days <= 90:
            truncation = TruncWeek
            cursor = start_date.date() - timedelta(days=start_date.date().weekday())
            last_bucket = end_date.date() - timedelta(days=end_date.date().weekday())
            step = "week"
        else:
            truncation = TruncMonth
            cursor = date(start_date.year, start_date.month, 1)
            last_bucket = date(end_date.year, end_date.month, 1)
            step = "month"

        bucket_dates = []
        # Prevent runaway loops in custom long ranges
        max_buckets = 60
        b_count = 0
        while cursor <= last_bucket and b_count < max_buckets:
            bucket_dates.append(cursor)
            b_count += 1
            if step == "day":
                cursor += timedelta(days=1)
            elif step == "week":
                cursor += timedelta(weeks=1)
            else:
                cursor = date(cursor.year + (cursor.month // 12), (cursor.month % 12) + 1, 1)

        def totals_by_period(queryset, date_field: str, amount_field: str) -> dict[date, Decimal]:
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
        cash_by_period = totals_by_period(curr_cust_payments, "payment_date", "amount")

        period_trend = []
        for bucket in bucket_dates:
            label = bucket.strftime("%b %Y" if step == "month" else "%b %d")
            period_trend.append({
                "date": label,
                "sales": sales_by_period.get(bucket, Decimal("0.00")),
                "purchases": purchases_by_period.get(bucket, Decimal("0.00")),
                "expenses": expenses_by_period.get(bucket, Decimal("0.00")),
                "cash_received": cash_by_period.get(bucket, Decimal("0.00")),
            })

        # Backward-compatible 15-day daily sales trend
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
        # 9. Deterministic Business Health Score (0 - 100)
        # ---------------------------------------------------------------------
        score = 80
        if net_margin_pct >= 25.0:
            score += 15
        elif net_margin_pct >= 15.0:
            score += 10
        elif net_margin_pct < 0.0:
            score -= 20
        elif net_margin_pct < 5.0:
            score -= 10

        if out_of_stock_count > 3:
            score -= 15
        elif out_of_stock_count > 0:
            score -= 8

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
            # Period boundaries
            "period_days": period_days,
            "period_label": period_label,
            "start_date": start_date,
            "end_date": end_date,
            # Sales & Orders
            "revenue": revenue,
            "sales_count": sales_count,
            "sales_discount": sales_discount,
            "sales_tax": sales_tax,
            "average_order_value": avg_order_value,
            "growth_pct": round(growth_pct, 1),
            "sales_today": sales_today,
            "sales_week": sales_week,
            "sales_month": sales_month,
            "sales_year": sales_year,
            "sales_by_payment_method": sales_by_payment_method,
            # Cash vs Sales distinction
            "cash_received": cash_received,
            "payments_today": payments_today,
            "payments_month": payments_month,
            "payments_year": payments_year,
            "collection_rate_pct": round(collection_rate_pct, 1),
            "collections_by_method": collections_by_method,
            # Purchases, Expenses & Cash Out
            "purchases": purchases,
            "purchase_count": purchase_count,
            "expenses": expenses,
            "expense_count": expense_count,
            "expenses_today": expenses_today,
            "expenses_month": expenses_month,
            "expenses_year": expenses_year,
            "top_expense_categories": top_expense_categories,
            "cash_paid_suppliers": cash_paid_suppliers,
            "total_cash_out": total_cash_out,
            "net_cash_flow": net_cash_flow,
            # Profitability & Margins
            "cogs": cogs,
            "gross_profit": gross_profit,
            "net_profit": net_profit,
            "gross_margin_pct": round(gross_margin_pct, 1),
            "net_margin_pct": round(net_margin_pct, 1),
            # Inventory & Reorder
            "total_products": total_products,
            "total_stock_units": total_stock_units,
            "inventory_valuation": inventory_valuation,
            "retail_valuation": retail_valuation,
            "low_stock_count": low_stock_count,
            "out_of_stock_count": out_of_stock_count,
            "fast_moving_products": fast_moving_products,
            "slow_moving_products": slow_moving_products,
            "reorder_suggestions": reorder_suggestions,
            # Working Capital & Debtors/Creditors
            "receivables_total": receivables_total,
            "receivables_overdue": receivables_overdue,
            "payables_total": payables_total,
            "payables_overdue": payables_overdue,
            "working_capital_net": working_capital_net,
            "top_customers": top_customers,
            "top_debtors": top_debtors,
            "cheques_due_7d": cheques_due_7d,
            "cheques_due_amount": cheques_due_amount,
            # User & System Overview
            "total_users": total_users,
            "online_users": online_users,
            "offline_users": offline_users,
            "active_accounts": active_accounts,
            "disabled_accounts": disabled_accounts,
            # Visual Trends & Health
            "daily_trend": daily_trend,
            "period_trend": period_trend,
            "health_score": health_score,
            "health_grade": health_grade,
        }

        # ---------------------------------------------------------------------
        # 10. AI or Deterministic Decision Advisor
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
            analytics_data["ai_insights"] = LocalDeterministicAdvisor.generate_insights(analytics_data)

        return analytics_data
