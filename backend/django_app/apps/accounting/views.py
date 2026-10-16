"""Views for Expense management, filtering, and tracking."""
from decimal import Decimal
from django.contrib import messages
from django.db.models import Q, Sum
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.accounts.permissions import login_required_custom, staff_required, manager_required
from apps.accounting.forms import ExpenseForm
from apps.accounting.models import Expense
from apps.core_app.pagination import paginate_queryset
from apps.core_app.exports import generate_csv_response, generate_excel_response


@login_required_custom
@staff_required
def expense_list(request: HttpRequest) -> HttpResponse:
    """List operational expenses with search, category filtering, date range, KPIs, and pagination."""
    search = request.GET.get("q", request.GET.get("search", "")).strip()
    category = request.GET.get("category", "").strip()
    date_from = request.GET.get("date_from", "").strip()
    date_to = request.GET.get("date_to", "").strip()

    company = getattr(request.user, "active_company", None)
    base_query = Expense.objects.filter(company=company) if company else Expense.objects.all()

    # Aggregate KPI Metrics for this company
    now = timezone.localdate()
    month_start = now.replace(day=1)

    this_month_qs = base_query.filter(expense_date__date__gte=month_start, expense_date__date__lte=now)
    total_this_month = this_month_qs.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    count_this_month = this_month_qs.count()

    today_qs = base_query.filter(expense_date__date=now)
    total_today = today_qs.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    count_today = today_qs.count()

    top_cat_agg = this_month_qs.values("category").annotate(cat_total=Sum("amount")).order_by("-cat_total").first()
    top_category_name = top_cat_agg["category"] if top_cat_agg else "None"
    top_category_amount = top_cat_agg["cat_total"] if top_cat_agg else Decimal("0.00")

    cash_total = this_month_qs.filter(payment_method__icontains="Cash").aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    bank_online_total = total_this_month - cash_total

    # Filtered Query
    query = base_query
    if search:
        query = query.filter(
            Q(category__icontains=search) |
            Q(description__icontains=search) |
            Q(reference__icontains=search)
        )

    if category:
        query = query.filter(category__iexact=category)

    if date_from:
        query = query.filter(expense_date__date__gte=date_from)
    if date_to:
        query = query.filter(expense_date__date__lte=date_to)

    filtered_total = query.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    page_obj = paginate_queryset(request, query.order_by("-expense_date"), per_page=15)
    categories = sorted(list(set(base_query.values_list("category", flat=True).distinct())))

    return render(request, "accounting/expense_list.html", {
        "page_obj": page_obj,
        "search": search,
        "search_query": search,
        "selected_category": category,
        "category_filter": category,
        "categories": categories,
        "date_from": date_from,
        "date_to": date_to,
        "total_this_month": total_this_month,
        "count_this_month": count_this_month,
        "total_today": total_today,
        "count_today": count_today,
        "top_category_name": top_category_name,
        "top_category_amount": top_category_amount,
        "cash_total": cash_total,
        "bank_online_total": bank_online_total,
        "filtered_total": filtered_total,
    })


@login_required_custom
@staff_required
def expense_create(request: HttpRequest) -> HttpResponse:
    """Record an operational expense."""
    form = ExpenseForm(request.POST or None, initial={"expense_date": timezone.localdate()})
    if request.method == "POST" and form.is_valid():
        expense = form.save(commit=False)
        expense.user = request.user
        expense.company = getattr(request.user, "active_company", None)
        if expense.expense_date and timezone.is_naive(expense.expense_date):
            expense.expense_date = timezone.make_aware(expense.expense_date)
        expense.save()
        messages.success(request, f"Expense recorded: {expense.category} (Rs. {expense.amount:,.2f}).")
        return redirect("expenses:list")
    return render(request, "accounting/expense_form.html", {"form": form, "title": "Record Expense"})


@login_required_custom
@staff_required
def expense_edit(request: HttpRequest, pk: int) -> HttpResponse:
    """Edit an existing expense."""
    kwargs = {"pk": pk}
    if hasattr(request.user, "active_company") and request.user.active_company:
        kwargs["company"] = request.user.active_company
    expense = get_object_or_404(Expense, **kwargs)
    form = ExpenseForm(request.POST or None, instance=expense)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"Expense updated successfully.")
        return redirect("expenses:list")
    return render(request, "accounting/expense_form.html", {"form": form, "expense": expense, "title": "Edit Expense"})


@require_POST
@login_required_custom
@manager_required
def expense_delete(request: HttpRequest, pk: int) -> HttpResponse:
    """Delete an expense."""
    kwargs = {"pk": pk}
    if hasattr(request.user, "active_company") and request.user.active_company:
        kwargs["company"] = request.user.active_company
    expense = get_object_or_404(Expense, **kwargs)
    expense.delete()
    messages.success(request, "Expense deleted successfully.")
    return redirect("expenses:list")


@login_required_custom
@staff_required
def expense_export_csv(request: HttpRequest) -> HttpResponse:
    """Export operational expenses to CSV format."""
    company = getattr(request.user, "active_company", None)
    query = Expense.objects.filter(company=company).order_by("-expense_date") if company else Expense.objects.all().order_by("-expense_date")
    headers = ["ID", "Date", "Category", "Description", "Payee / Reference", "Payment Method", "Amount (Rs.)"]
    rows = [
        [
            e.id,
            e.expense_date.strftime("%Y-%m-%d %H:%M") if e.expense_date else "",
            e.category,
            e.description or "",
            e.reference or "",
            e.payment_method or "",
            str(e.amount),
        ]
        for e in query
    ]
    return generate_csv_response(headers, rows, "operational_expenses")


@login_required_custom
@staff_required
def expense_export_excel(request: HttpRequest) -> HttpResponse:
    """Export operational expenses to formatted Excel (.xlsx) format."""
    company = getattr(request.user, "active_company", None)
    query = Expense.objects.filter(company=company).order_by("-expense_date") if company else Expense.objects.all().order_by("-expense_date")
    headers = ["ID", "Date", "Category", "Description", "Payee / Reference", "Payment Method", "Amount (Rs.)"]
    rows = [
        [
            e.id,
            e.expense_date.strftime("%Y-%m-%d %H:%M") if e.expense_date else "",
            e.category,
            e.description or "",
            e.reference or "",
            e.payment_method or "",
            float(e.amount),
        ]
        for e in query
    ]
    return generate_excel_response("Operational Expenses", headers, rows, "operational_expenses")
