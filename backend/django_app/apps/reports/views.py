"""Reports and Daybook transaction ledger views."""
from datetime import date, datetime
from decimal import Decimal

from django.contrib import messages
from django.db.models import Sum
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone

from apps.accounts.permissions import login_required_custom, manager_required
from apps.sales.models import Sale
from apps.purchases.models import Purchase
from apps.accounting.models import Expense
from apps.inventory.models import Product, StockMovement
from apps.core_app.exports import generate_csv_response
from domain.services.report_service import ReportService
from domain.services.analytics_service import AnalyticsService
from services.nepali_date import NepaliDateService


@login_required_custom
@manager_required
def index(request: HttpRequest) -> HttpResponse:
    """Display overall business financial summary and inventory valuation."""
    company_id = getattr(request.user.active_company, "id", None)
    metrics = ReportService.get_dashboard_metrics(company_id=company_id)
    return render(request, "reports/index.html", {
        "metrics": metrics,
        "total_sales": metrics.total_sales,
        "total_purchases": metrics.total_purchases,
        "total_expenses": metrics.total_expenses,
        "net_profit": metrics.gross_profit,
        "product_count": metrics.total_products,
        "sales_count": metrics.total_customers,
        "purchases_count": 0,
    })


@login_required_custom
@manager_required
def analytics_view(request: HttpRequest) -> HttpResponse:
    """Business Intelligence, KPIs, Inventory Velocity, and AI Decision Support."""
    company_id = getattr(request.user.active_company, "id", None)
    period = request.GET.get("period", "").strip().lower()
    date_from = request.GET.get("date_from", "").strip()
    date_to = request.GET.get("date_to", "").strip()
    days_str = request.GET.get("days", "30").strip()

    days = 30
    if days_str:
        try:
            days = int(days_str)
        except ValueError:
            days = 30

    force_refresh = request.GET.get("refresh_ai", "0") in ("1", "true")
    focus_options = {
        "overview", "sales", "payments", "receivables", "purchases", "payables",
        "expenses", "profitability", "inventory", "customers", "users",
    }
    selected_focus = request.GET.get("focus", "sales").strip().lower()
    if selected_focus not in focus_options:
        selected_focus = "sales"

    analytics_data = AnalyticsService.get_business_analytics(
        company_id=company_id,
        days=days if not period and not (date_from and date_to) else None,
        period=period or None,
        date_from=date_from or None,
        date_to=date_to or None,
        include_ai=True,
        force_ai_refresh=force_refresh,
        user_id=request.user.id,
    )

    return render(request, "reports/analytics.html", {
        "analytics": analytics_data,
        "selected_days": analytics_data.get("period_days", days),
        "selected_period": analytics_data.get("period_label", f"{days}d"),
        "selected_focus": selected_focus,
        "date_from": date_from,
        "date_to": date_to,
    })


@login_required_custom
@manager_required
def analytics_ai_refresh(request: HttpRequest) -> HttpResponse:
    """Explicitly trigger on-demand AI decision support refresh."""
    company_id = getattr(request.user.active_company, "id", None)
    period = request.POST.get("period", request.GET.get("period", "")).strip()
    date_from = request.POST.get("date_from", request.GET.get("date_from", "")).strip()
    date_to = request.POST.get("date_to", request.GET.get("date_to", "")).strip()
    days_str = request.POST.get("days", request.GET.get("days", "30")).strip()
    try:
        days = int(days_str)
    except ValueError:
        days = 30

    AnalyticsService.get_business_analytics(
        company_id=company_id,
        days=days if not period and not (date_from and date_to) else None,
        period=period or None,
        date_from=date_from or None,
        date_to=date_to or None,
        include_ai=True,
        force_ai_refresh=True,
        user_id=request.user.id,
    )
    messages.success(request, "AI Decision Support recommendations refreshed successfully.")

    if request.headers.get("accept") == "application/json":
        return JsonResponse({"status": "success", "message": "Refreshed"})

    params = []
    if period:
        params.append(f"period={period}")
    elif date_from and date_to:
        params.append(f"date_from={date_from}&date_to={date_to}")
    else:
        params.append(f"days={days}")

    query_str = f"?{'&'.join(params)}" if params else ""
    return redirect(f"/reports/analytics/{query_str}")


@login_required_custom
@manager_required
def export_summary_csv(request: HttpRequest) -> HttpResponse:
    """Export high-level financial summary to CSV."""
    company_id = getattr(request.user.active_company, "id", None)
    metrics = ReportService.get_dashboard_metrics(company_id=company_id)
    headers = ["Metric", "Value"]
    rows = [
        ["Financial Summary Report", timezone.localdate().isoformat()],
        ["Total Revenue", str(metrics.total_sales)],
        ["Total Purchases", str(metrics.total_purchases)],
        ["Total Operational Expenses", str(metrics.total_expenses)],
        ["Net Margin / Profit", str(metrics.gross_profit)],
        ["Total Registered Products", str(metrics.total_products)],
        ["Low Stock Items", str(metrics.low_stock_count)],
    ]
    return generate_csv_response(headers, rows, f"financial_summary_{timezone.localdate()}")


@login_required_custom
@manager_required
def export_analytics_csv(request: HttpRequest) -> HttpResponse:
    """Export comprehensive business analytics data to CSV matching active filters."""
    company_id = getattr(request.user.active_company, "id", None)
    period = request.GET.get("period", "").strip()
    date_from = request.GET.get("date_from", "").strip()
    date_to = request.GET.get("date_to", "").strip()
    days_str = request.GET.get("days", "30").strip()
    try:
        days = int(days_str)
    except ValueError:
        days = 30

    data = AnalyticsService.get_business_analytics(
        company_id=company_id,
        days=days if not period and not (date_from and date_to) else None,
        period=period or None,
        date_from=date_from or None,
        date_to=date_to or None,
        include_ai=False,
    )

    headers = ["Report Section", "Metric / Indicator", "Amount / Value (NPR)", "Notes"]
    rows = [
        ["Period Overview", "Start Date", data["start_date"].strftime("%Y-%m-%d"), "Inclusive"],
        ["Period Overview", "End Date", data["end_date"].strftime("%Y-%m-%d"), "Inclusive"],
        ["Period Overview", "Period Duration", f"{data['period_days']} days", data["period_label"]],
        ["Period Overview", "Business Health Score", str(data["health_score"]), data["health_grade"]],
        ["Sales & Revenue", "Total Billed Revenue", str(data["revenue"]), "Gross sales invoices"],
        ["Sales & Revenue", "Sales Invoices Count", str(data["sales_count"]), "Transaction count"],
        ["Sales & Revenue", "Average Order Value", str(data["average_order_value"]), "Per invoice avg"],
        ["Sales & Revenue", "Period Growth Velocity", f"{data['growth_pct']}%", "vs prior period"],
        ["Sales & Revenue", "Sales Total Discounts", str(data["sales_discount"]), "Discounts given"],
        ["Cash Collections", "Cash Actually Received", str(data["cash_received"]), "From customer settlements"],
        ["Cash Collections", "Collection Rate", f"{data['collection_rate_pct']}%", "Cash received / Revenue"],
        ["Cash Collections", "Customer Dues (Receivables)", str(data["receivables_total"]), "Total unpaid credit"],
        ["Cash Collections", "Overdue Receivables", str(data["receivables_overdue"]), "Passed due date"],
        ["Procurement & Costs", "Purchase Bills", str(data["purchases"]), "Inward vendor stock"],
        ["Procurement & Costs", "Cost of Goods Sold (COGS)", str(data["cogs"]), "Cost of sold inventory"],
        ["Procurement & Costs", "Operating Expenses", str(data["expenses"]), "Rent, utilities, salaries, etc."],
        ["Procurement & Costs", "Cash Paid to Suppliers", str(data["cash_paid_suppliers"]), "Vendor settlements"],
        ["Procurement & Costs", "Supplier Dues (Payables)", str(data["payables_total"]), "Total owed to vendors"],
        ["Profitability", "Estimated Gross Profit", str(data["gross_profit"]), "Revenue - COGS"],
        ["Profitability", "Gross Profit Margin", f"{data['gross_margin_pct']}%", "Gross Profit / Revenue"],
        ["Profitability", "Estimated Net Profit", str(data["net_profit"]), "Gross Profit - Operating Expenses"],
        ["Profitability", "Net Profit Margin", f"{data['net_margin_pct']}%", "Net Profit / Revenue"],
        ["Cash Flow", "Total Cash In", str(data["cash_received"]), "Customer payments received"],
        ["Cash Flow", "Total Cash Out", str(data["total_cash_out"]), "Supplier payments + Expenses"],
        ["Cash Flow", "Net Cash Flow", str(data["net_cash_flow"]), "Cash In - Cash Out"],
        ["Working Capital", "Net Working Capital", str(data["working_capital_net"]), "Receivables - Payables"],
        ["Inventory Snapshot", "Active Products Count", str(data["total_products"]), "Catalog count"],
        ["Inventory Snapshot", "Total Stock Units", str(data["total_stock_units"]), "On-hand quantity"],
        ["Inventory Snapshot", "Stock Valuation (at Cost)", str(data["inventory_valuation"]), "Based on purchase price"],
        ["Inventory Snapshot", "Stock Valuation (at Retail)", str(data["retail_valuation"]), "Based on selling price"],
        ["Inventory Snapshot", "Low Stock Products", str(data["low_stock_count"]), "At or below alert level"],
        ["Inventory Snapshot", "Out of Stock Products", str(data["out_of_stock_count"]), "Zero stock available"],
        ["Cheque Portfolio", "Cheques Maturing (Next 7d)", str(data["cheques_due_7d"]), f"Value: Rs. {data['cheques_due_amount']}"],
    ]
    filename = f"business_analytics_{timezone.localdate()}_{data['period_label']}"
    return generate_csv_response(headers, rows, filename)


@login_required_custom
@manager_required
def daybook(request: HttpRequest) -> HttpResponse:
    """Daily transaction ledger (Day Book) for sales, purchases, expenses, and stock movements."""
    date_str = request.GET.get("date", "").strip()

    if date_str:
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            target_date = timezone.localdate()
    else:
        target_date = timezone.localdate()

    sales = Sale.objects.select_related("customer").filter(sale_date__date=target_date, is_active=True).order_by("-sale_date")
    purchases = Purchase.objects.select_related("supplier").filter(purchase_date__date=target_date, is_active=True).order_by("-purchase_date")
    expenses = Expense.objects.filter(expense_date__date=target_date).order_by("-expense_date")
    movements = StockMovement.objects.select_related("product").filter(created_at__date=target_date).order_by("-created_at")

    total_sales = sales.aggregate(t=Sum("total"))["t"] or Decimal("0.00")
    total_purchases = purchases.aggregate(t=Sum("total"))["t"] or Decimal("0.00")
    total_expenses = expenses.aggregate(t=Sum("amount"))["t"] or Decimal("0.00")
    net_day_balance = total_sales - total_purchases - total_expenses

    items_in = sum((m.quantity for m in movements if m.movement_type == "IN"), 0)
    items_out = sum((m.quantity for m in movements if m.movement_type == "OUT"), 0)

    try:
        formatted_bs = NepaliDateService.format_nepali_date(target_date)
    except Exception:
        formatted_bs = "N/A"

    return render(request, "reports/daybook.html", {
        "target_date": target_date,
        "formatted_bs": formatted_bs,
        "sales": sales,
        "purchases": purchases,
        "expenses": expenses,
        "stock_movements": movements,
        "total_sales": total_sales,
        "total_purchases": total_purchases,
        "total_expenses": total_expenses,
        "net_day_balance": net_day_balance,
        "items_in": items_in,
        "items_out": items_out,
    })


@login_required_custom
@manager_required
def export_daybook_csv(request: HttpRequest) -> HttpResponse:
    """Export daybook transactions to CSV."""
    date_str = request.GET.get("date", "").strip()
    target_date = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else timezone.localdate()

    sales = Sale.objects.select_related("customer").filter(sale_date__date=target_date, is_active=True)
    purchases = Purchase.objects.select_related("supplier").filter(purchase_date__date=target_date, is_active=True)
    expenses = Expense.objects.filter(expense_date__date=target_date)

    headers = ["Type", "Reference", "Party / Category", "Payment Method", "Amount", "Status"]
    rows = []

    for s in sales:
        rows.append(["Sale", s.invoice_number, s.customer.name if s.customer else "Walk-in", s.payment_method, str(s.total), s.payment_status])
    for p in purchases:
        rows.append(["Purchase", p.purchase_number, p.supplier.name if p.supplier else "Vendor", p.payment_method, str(p.total), p.payment_status])
    for e in expenses:
        rows.append(["Expense", e.reference or "-", e.category, e.payment_method, str(e.amount), "Completed"])

    return generate_csv_response(headers, rows, f"daybook_{target_date}")
