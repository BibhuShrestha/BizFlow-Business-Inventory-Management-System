"""Views for Seller management and exports."""
from django.contrib import messages
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from django.views.decorators.http import require_POST
from apps.accounts.permissions import login_required_custom, manager_required
from apps.companies.forms import SellerForm
from apps.companies.models import Company, Seller
from apps.core_app.exports import generate_csv_response, generate_excel_response
from apps.core_app.pagination import paginate_queryset
from apps.core_app.security_utils import get_safe_redirect_url


@login_required_custom
@manager_required
def seller_list(request: HttpRequest) -> HttpResponse:
    """List sellers with search, company filtering, and pagination."""
    search = request.GET.get("search", "").strip()
    company_id = request.GET.get("company_id")

    query = Seller.objects.select_related("company").all()

    if company_id and company_id.isdigit():
        query = query.filter(company_id=int(company_id))

    if search:
        query = query.filter(
            Q(seller_name__icontains=search) |
            Q(seller_phone__icontains=search)
        )

    page_obj = paginate_queryset(request, query.order_by("seller_name"), per_page=15)
    companies = Company.objects.all().order_by("company_name")
    return render(request, "companies/sellers_list.html", {
        "page_obj": page_obj,
        "companies": companies,
        "selected_company_id": int(company_id) if company_id and company_id.isdigit() else None,
        "search": search,
    })


from django.http import HttpRequest, HttpResponse, JsonResponse


@login_required_custom
@manager_required
def seller_create(request: HttpRequest) -> HttpResponse:
    """Create a new seller with AJAX and return_to redirect support."""
    form = SellerForm(request.POST or None)
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest" or request.content_type == "application/json"

    if request.method == "POST":
        if form.is_valid():
            seller = form.save(commit=False)
            if not seller.company and hasattr(request.user, "active_company") and request.user.active_company:
                seller.company = request.user.active_company
            seller.save()

            if is_ajax:
                return JsonResponse({
                    "success": True,
                    "id": seller.id,
                    "name": str(seller),
                    "phone": seller.seller_phone or "",
                    "message": f'Seller "{seller.seller_name}" created successfully.',
                })

            messages.success(request, f'Seller "{seller.seller_name}" created successfully.')
            raw_next = request.GET.get("next") or request.POST.get("next") or request.GET.get("return_to") or request.POST.get("return_to")
            if raw_next:
                safe_next = get_safe_redirect_url(raw_next, request, default="")
                if safe_next:
                    sep = "&" if "?" in safe_next else "?"
                    return redirect(f"{safe_next}{sep}seller_id={seller.id}")
            return redirect("sellers:list")
        elif is_ajax:
            return JsonResponse({"success": False, "errors": form.errors}, status=400)

    return render(request, "companies/seller_form.html", {
        "form": form,
        "title": "Create Seller",
        "return_to": request.GET.get("return_to") or request.GET.get("next") or "",
    })


@login_required_custom
@manager_required
def seller_edit(request: HttpRequest, pk: int) -> HttpResponse:
    """Edit an existing seller."""
    seller = get_object_or_404(Seller, pk=pk)
    form = SellerForm(request.POST or None, instance=seller)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f'Seller "{seller.seller_name}" updated successfully.')
        return redirect("sellers:list")
    return render(request, "companies/seller_form.html", {"form": form, "seller": seller, "title": "Edit Seller"})


@require_POST
@login_required_custom
@manager_required
def seller_delete(request: HttpRequest, pk: int) -> HttpResponse:
    """Delete a seller."""
    seller = get_object_or_404(Seller, pk=pk)
    name = seller.seller_name
    seller.delete()
    messages.success(request, f'Seller "{name}" deleted successfully.')
    return redirect("sellers:list")


@login_required_custom
def export_sellers_csv(request: HttpRequest) -> HttpResponse:
    """Export all sellers to CSV."""
    sellers = Seller.objects.select_related("company").all().order_by("seller_name")
    headers = ["ID", "Seller Name", "Phone", "Company Name", "Created At"]
    rows = [
        [s.id, s.seller_name, s.seller_phone, s.company.company_name if s.company else "Unassigned", s.created_at.strftime("%Y-%m-%d")]
        for s in sellers
    ]
    return generate_csv_response(headers, rows, "sellers_export")


@login_required_custom
def export_sellers_excel(request: HttpRequest) -> HttpResponse:
    """Export all sellers to Excel."""
    sellers = Seller.objects.select_related("company").all().order_by("seller_name")
    headers = ["ID", "Seller Name", "Phone", "Company Name", "Created At"]
    rows = [
        [s.id, s.seller_name, s.seller_phone, s.company.company_name if s.company else "Unassigned", s.created_at.strftime("%Y-%m-%d")]
        for s in sellers
    ]
    return generate_excel_response("Sellers", headers, rows, "sellers_export")
