"""Views for Expense management, filtering, and tracking."""
from django.contrib import messages
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.accounts.permissions import login_required_custom, staff_required, manager_required
from apps.accounting.forms import ExpenseForm
from apps.accounting.models import Expense
from apps.core_app.pagination import paginate_queryset


@login_required_custom
@staff_required
def expense_list(request: HttpRequest) -> HttpResponse:
    """List operational expenses with search, category filtering, and pagination."""
    search = request.GET.get("search", "").strip()
    category = request.GET.get("category", "").strip()

    query = Expense.objects.all()
    company = getattr(request.user, "active_company", None)
    if company:
        query = query.filter(company=company)

    if search:
        query = query.filter(
            Q(category__icontains=search) |
            Q(description__icontains=search) |
            Q(reference__icontains=search)
        )

    if category:
        query = query.filter(category__iexact=category)

    page_obj = paginate_queryset(request, query.order_by("-expense_date"), per_page=15)
    categories = query.values_list("category", flat=True).distinct()
    return render(request, "accounting/expense_list.html", {
        "page_obj": page_obj,
        "search": search,
        "selected_category": category,
        "categories": categories,
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
        expense.save()
        messages.success(request, f"Expense recorded: {expense.category} (Rs. {expense.amount}).")
        return redirect("expenses:list")
    return render(request, "accounting/expense_form.html", {"form": form, "title": "Record Expense"})


@login_required_custom
@staff_required
def expense_edit(request: HttpRequest, pk: int) -> HttpResponse:
    """Edit an existing expense."""
    kwargs = {"pk": pk}
    if hasattr(request.user, "active_company") and request.user.active_company and not request.user.is_admin:
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
    if hasattr(request.user, "active_company") and request.user.active_company and not request.user.is_admin:
        kwargs["company"] = request.user.active_company
    expense = get_object_or_404(Expense, **kwargs)
    expense.delete()
    messages.success(request, "Expense deleted successfully.")
    return redirect("expenses:list")
