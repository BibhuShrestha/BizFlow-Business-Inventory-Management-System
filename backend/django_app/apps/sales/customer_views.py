"""Views for Customer management and transaction history."""
from django.contrib import messages
from django.db.models import Q, Sum
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.permissions import login_required_custom, staff_required, manager_required
from apps.sales.customer_forms import CustomerForm
from apps.sales.models import Customer, Sale
from apps.core_app.pagination import paginate_queryset


@login_required_custom
@staff_required
def customer_list(request: HttpRequest) -> HttpResponse:
    """List customers with search and pagination."""
    search = request.GET.get("search", "").strip()
    query = Customer.objects.filter(is_active=True)
    if getattr(request.user, "active_company", None):
        query = query.filter(company=request.user.active_company)

    if search:
        query = query.filter(
            Q(name__icontains=search) |
            Q(phone__icontains=search) |
            Q(email__icontains=search)
        )

    page_obj = paginate_queryset(request, query.order_by("name"), per_page=15)
    return render(request, "sales/customer_list.html", {
        "page_obj": page_obj,
        "search": search,
    })


@login_required_custom
@staff_required
def customer_create(request: HttpRequest) -> HttpResponse:
    """Create a new customer with AJAX and modal support."""
    form = CustomerForm(request.POST or None)
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest" or request.content_type == "application/json"

    if request.method == "POST":
        if form.is_valid():
            customer = form.save(commit=False)
            if not customer.company and hasattr(request.user, "active_company") and request.user.active_company:
                customer.company = request.user.active_company
            customer.save()

            if is_ajax:
                return JsonResponse({
                    "success": True,
                    "id": customer.id,
                    "name": customer.name,
                    "phone": customer.phone or "",
                    "message": f'Customer "{customer.name}" created successfully.',
                })

            messages.success(request, f'Customer "{customer.name}" created successfully.')
            next_url = request.GET.get("next") or request.POST.get("next")
            if next_url:
                sep = "&" if "?" in next_url else "?"
                return redirect(f"{next_url}{sep}customer_id={customer.id}")
            return redirect("customers:list")
        else:
            if is_ajax:
                return JsonResponse({
                    "success": False,
                    "errors": form.errors.get_json_data(),
                }, status=400)

    return render(request, "sales/customer_form.html", {"form": form, "title": "Add New Customer"})


@login_required_custom
@staff_required
def customer_edit(request: HttpRequest, pk: int) -> HttpResponse:
    """Edit existing customer."""
    customer = get_object_or_404(Customer, pk=pk)
    form = CustomerForm(request.POST or None, instance=customer)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f'Customer "{customer.name}" updated successfully.')
        return redirect("customers:list")
    return render(request, "sales/customer_form.html", {"form": form, "customer": customer, "title": "Edit Customer"})


@login_required_custom
@manager_required
def customer_delete(request: HttpRequest, pk: int) -> HttpResponse:
    """Deactivate customer."""
    customer = get_object_or_404(Customer, pk=pk)
    customer.is_active = False
    customer.save(update_fields=["is_active"])
    messages.success(request, f'Customer "{customer.name}" has been deactivated.')
    return redirect("customers:list")


@login_required_custom
@staff_required
def customer_detail(request: HttpRequest, pk: int) -> HttpResponse:
    """View customer ledger and invoice history."""
    customer = get_object_or_404(Customer, pk=pk)
    sales = customer.sales.filter(is_active=True).order_by("-sale_date")
    total_sales = sales.aggregate(s=Sum("total"))["s"] or 0

    from domain.services.credit_service import CreditService
    ledger_data = CreditService.get_customer_ledger(customer.id)

    return render(request, "sales/customer_detail.html", {
        "customer": customer,
        "sales": sales,
        "total_sales": total_sales,
        "total_credit": ledger_data["total_credit_given"],
        "total_paid": ledger_data["total_paid"],
        "remaining_due": ledger_data["remaining_due"],
        "overdue_amount": ledger_data["overdue_amount"],
    })
