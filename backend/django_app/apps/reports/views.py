"""Reports and Daybook transaction ledger views."""
from datetime import date, datetime
from decimal import Decimal

from django.contrib import messages
from django.db.models import Sum
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone

from apps.accounts.permissions import login_required_custom, manager_required
from apps.sales.models import Sale
from apps.purchases.models import Purchase
from apps.accounting.models import Expense
from apps.inventory.models import Product, StockMovement
from apps.core_app.exports import generate_csv_response
from domain.services.report_service import ReportService
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
