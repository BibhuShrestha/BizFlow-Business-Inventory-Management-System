"""Views for Supplier management and purchase order history."""
from django.contrib import messages
from django.db.models import Q, Sum
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.permissions import login_required_custom, staff_required, manager_required
from apps.purchases.supplier_forms import SupplierForm
from apps.purchases.models import Supplier, Purchase
from apps.core_app.pagination import paginate_queryset


@login_required_custom
@staff_required
def supplier_list(request: HttpRequest) -> HttpResponse:
    """List suppliers with search and pagination."""
    search = request.GET.get("search", "").strip()
    query = Supplier.objects.filter(is_active=True)
    if getattr(request.user, "active_company", None):
        query = query.filter(company=request.user.active_company)

    if search:
        query = query.filter(
            Q(name__icontains=search) |
            Q(phone__icontains=search) |
            Q(email__icontains=search)
        )

    page_obj = paginate_queryset(request, query.order_by("name"), per_page=15)
    return render(request, "purchases/supplier_list.html", {
        "page_obj": page_obj,
        "search": search,
    })


from django.http import HttpRequest, HttpResponse, JsonResponse


@login_required_custom
@staff_required
def supplier_create(request: HttpRequest) -> HttpResponse:
    """Create a new supplier with AJAX and return_to redirect support."""
    form = SupplierForm(request.POST or None)
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest" or request.content_type == "application/json"

    if request.method == "POST":
        if form.is_valid():
            supplier = form.save(commit=False)
            if not supplier.company and hasattr(request.user, "active_company") and request.user.active_company:
                supplier.company = request.user.active_company
            supplier.save()

            if is_ajax:
                return JsonResponse({
                    "success": True,
                    "id": supplier.id,
                    "name": supplier.name,
                    "phone": supplier.phone or "",
                    "message": f'Supplier "{supplier.name}" created successfully.',
                })

            messages.success(request, f'Supplier "{supplier.name}" created successfully.')
            next_url = request.GET.get("next") or request.POST.get("next") or request.GET.get("return_to") or request.POST.get("return_to")
            if next_url:
                sep = "&" if "?" in next_url else "?"
                return redirect(f"{next_url}{sep}supplier_id={supplier.id}")
            return redirect("suppliers:list")
        elif is_ajax:
            return JsonResponse({"success": False, "errors": form.errors}, status=400)

    return render(request, "purchases/supplier_form.html", {
        "form": form,
        "title": "Add New Supplier",
        "return_to": request.GET.get("return_to") or request.GET.get("next") or "",
    })


@login_required_custom
@staff_required
def supplier_edit(request: HttpRequest, pk: int) -> HttpResponse:
    """Edit existing supplier."""
    supplier = get_object_or_404(Supplier, pk=pk)
    form = SupplierForm(request.POST or None, instance=supplier)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f'Supplier "{supplier.name}" updated successfully.')
        return redirect("suppliers:list")
    return render(request, "purchases/supplier_form.html", {"form": form, "supplier": supplier, "title": "Edit Supplier"})


@login_required_custom
@manager_required
def supplier_delete(request: HttpRequest, pk: int) -> HttpResponse:
    """Deactivate supplier."""
    supplier = get_object_or_404(Supplier, pk=pk)
    supplier.is_active = False
    supplier.save(update_fields=["is_active"])
    messages.success(request, f'Supplier "{supplier.name}" has been deactivated.')
    return redirect("suppliers:list")


@login_required_custom
@staff_required
def supplier_detail(request: HttpRequest, pk: int) -> HttpResponse:
    """View supplier purchase order history."""
    supplier = get_object_or_404(Supplier, pk=pk)
    purchases = supplier.purchases.filter(is_active=True).order_by("-purchase_date")
    total_purchases = purchases.aggregate(s=Sum("total"))["s"] or 0

    from domain.services.credit_service import CreditService
    ledger_data = CreditService.get_supplier_ledger(supplier.id)

    return render(request, "purchases/supplier_detail.html", {
        "supplier": supplier,
        "purchases": purchases,
        "total_purchases": total_purchases,
        "total_credit": ledger_data["total_credit_taken"],
        "total_paid": ledger_data["total_paid"],
        "remaining_payable": ledger_data["remaining_payable"],
        "overdue_amount": ledger_data["overdue_amount"],
    })
