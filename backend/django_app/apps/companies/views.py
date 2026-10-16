"""Views for Company management, multi-tenancy, and exports."""
from django.contrib import messages
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from django.views.decorators.http import require_POST
from apps.accounts.permissions import login_required_custom, manager_required
from apps.companies.forms import CompanyForm
from apps.companies.models import Company
from apps.core_app.exports import generate_csv_response, generate_excel_response
from apps.core_app.pagination import paginate_queryset
from apps.core_app.security_utils import get_safe_redirect_url


@login_required_custom
@manager_required
def company_list(request: HttpRequest) -> HttpResponse:
    """List all companies with search and pagination."""
    search = request.GET.get("q", "").strip() or request.GET.get("search", "").strip()
    query = Company.objects.all()

    if search:
        query = query.filter(
            Q(company_name__icontains=search) |
            Q(vat_pan_number__icontains=search) |
            Q(company_phone__icontains=search)
        )

    sort = request.GET.get("sort", "company_name")
    if sort in ("company_name", "-company_name", "created_at", "-created_at"):
        query = query.order_by(sort)

    page_obj = paginate_queryset(request, query, per_page=15)
    return render(request, "companies/list.html", {
        "page_obj": page_obj,
        "companies": page_obj,
        "search_query": search,
        "search": search,
        "sort": sort,
    })


from django.http import HttpRequest, HttpResponse, JsonResponse


@login_required_custom
@manager_required
def company_create(request: HttpRequest) -> HttpResponse:
    """Create a new company profile with AJAX and return_to redirect support."""
    form = CompanyForm(request.POST or None)
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest" or request.content_type == "application/json"

    if request.method == "POST":
        if form.is_valid():
            company = form.save()
            # If current session has no active company, switch to this new company automatically
            if not request.session.get("active_company_id") or not getattr(request.user, "active_company", None):
                request.session["active_company_id"] = company.id
                if hasattr(request.user, "active_company"):
                    request.user.active_company = company
                    request.user.save(update_fields=["active_company"])

            if is_ajax:
                return JsonResponse({
                    "success": True,
                    "id": company.id,
                    "name": company.company_name,
                    "phone": company.company_phone or "",
                    "vat_pan": company.vat_pan_number or "",
                    "message": f'Company "{company.company_name}" created successfully.',
                })

            messages.success(request, f'Company "{company.company_name}" created successfully.')
            raw_next = request.GET.get("next") or request.POST.get("next") or request.GET.get("return_to") or request.POST.get("return_to")
            if raw_next:
                safe_next = get_safe_redirect_url(raw_next, request, default="")
                if safe_next:
                    sep = "&" if "?" in safe_next else "?"
                    return redirect(f"{safe_next}{sep}company_id={company.id}")
            return redirect("companies:list")
        elif is_ajax:
            return JsonResponse({"success": False, "errors": form.errors}, status=400)

    return render(request, "companies/form.html", {
        "form": form,
        "title": "Create Company",
        "return_to": request.GET.get("return_to") or request.GET.get("next") or "",
    })


@login_required_custom
@manager_required
def company_edit(request: HttpRequest, pk: int) -> HttpResponse:
    """Edit an existing company."""
    company = get_object_or_404(Company, pk=pk)
    form = CompanyForm(request.POST or None, instance=company)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f'Company "{company.company_name}" updated successfully.')
        return redirect("companies:list")
    return render(request, "companies/form.html", {"form": form, "company": company, "title": "Edit Company"})


@require_POST
@login_required_custom
@manager_required
def company_delete(request: HttpRequest, pk: int) -> HttpResponse:
    """Delete a company."""
    company = get_object_or_404(Company, pk=pk)
    name = company.company_name
    company.delete()
    messages.success(request, f'Company "{name}" deleted successfully.')
    return redirect("companies:list")


@login_required_custom
def set_active_company(request: HttpRequest, pk: int) -> HttpResponse:
    """Set active company context for current user/session."""
    company = get_object_or_404(Company, pk=pk)
    request.session["active_company_id"] = company.id
    if hasattr(request.user, "active_company"):
        request.user.active_company = company
        request.user.save(update_fields=["active_company"])
    messages.success(request, f'Switched active company to "{company.company_name}".')
    safe_next = get_safe_redirect_url(request.META.get("HTTP_REFERER"), request, default="/dashboard/")
    return redirect(safe_next)



@login_required_custom
def export_csv(request: HttpRequest) -> HttpResponse:
    """Export all companies to CSV."""
    companies = Company.objects.all().order_by("company_name")
    headers = ["ID", "Company Name", "Phone", "VAT / PAN Number", "Address", "Created At"]
    rows = [
        [c.id, c.company_name, c.company_phone, c.vat_pan_number, c.address, c.created_at.strftime("%Y-%m-%d")]
        for c in companies
    ]
    return generate_csv_response(headers, rows, "companies_export")


@login_required_custom
def export_excel(request: HttpRequest) -> HttpResponse:
    """Export all companies to Excel (.xlsx)."""
    companies = Company.objects.all().order_by("company_name")
    headers = ["ID", "Company Name", "Phone", "VAT / PAN Number", "Address", "Created At"]
    rows = [
        [c.id, c.company_name, c.company_phone, c.vat_pan_number, c.address, c.created_at.strftime("%Y-%m-%d")]
        for c in companies
    ]
    return generate_excel_response("Companies", headers, rows, "companies_export")
