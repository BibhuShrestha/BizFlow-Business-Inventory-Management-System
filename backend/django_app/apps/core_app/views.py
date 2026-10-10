"""
Custom HTTP Error Views and Central Import/Export Views.
"""
import json
from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse, JsonResponse

from apps.accounts.permissions import login_required_custom, staff_required, manager_required
from apps.core_app.exports import parse_uploaded_file
from domain.services.import_export_service import ImportExportService


def error_404(request: HttpRequest, exception=None) -> HttpResponse:
    """Render friendly, accessible 404 Not Found page."""
    return render(request, "errors/404.html", status=404)


def error_500(request: HttpRequest) -> HttpResponse:
    """Render secure, friendly 500 Server Error page without exposing stack traces."""
    return render(request, "errors/500.html", status=500)


def error_403(request: HttpRequest, exception=None) -> HttpResponse:
    """Render 403 Forbidden page."""
    return render(request, "errors/403.html", status=403)


def error_400(request: HttpRequest, exception=None) -> HttpResponse:
    """Render 400 Bad Request page."""
    return render(request, "errors/400.html", status=400)


@login_required_custom
@manager_required
def import_export_hub(request: HttpRequest) -> HttpResponse:
    """
    Central hub for importing and exporting data across:
    - Products, Customers, Suppliers, Sales, Purchases, Payments, Receivables, Payables, Cheques, Stock
    Supports Excel (.xlsx), CSV (.csv), and JSON (.json).
    """
    modules = [
        {"id": "products", "name": "Products & Catalog", "icon": "📦"},
        {"id": "customers", "name": "Customers", "icon": "👥"},
        {"id": "suppliers", "name": "Suppliers", "icon": "🏢"},
        {"id": "sales", "name": "Sales Invoices", "icon": "🧾"},
        {"id": "purchases", "name": "Purchase Bills", "icon": "🛍️"},
        {"id": "payments", "name": "Payment Vouchers", "icon": "💵"},
        {"id": "receivables", "name": "Receivables (Credit Given)", "icon": "💰"},
        {"id": "payables", "name": "Payables (Credit Taken)", "icon": "💸"},
        {"id": "cheques", "name": "Cheques (Given & Received)", "icon": "📑"},
        {"id": "stock", "name": "Stock Inventory & Valuation", "icon": "📊"},
    ]
    formats = [
        {"id": "xlsx", "name": "Excel (.xlsx)", "badge": "Spreadsheet"},
        {"id": "csv", "name": "CSV (.csv)", "badge": "Plain Text"},
        {"id": "json", "name": "JSON (.json)", "badge": "Structured Data"},
    ]
    return render(request, "core_app/import_export.html", {
        "modules": modules,
        "formats": formats,
    })


@login_required_custom
@manager_required
def export_dataset(request: HttpRequest) -> HttpResponse:
    """Trigger multi-format export with filters."""
    module = request.GET.get("module", "products").lower().strip()
    export_format = request.GET.get("format", "csv").lower().strip()
    company_id = getattr(request.user.active_company, "id", None) if getattr(request.user, "active_company", None) else None

    filters = {
        "search": request.GET.get("search", "").strip(),
        "start_date": request.GET.get("start_date", "").strip() or None,
        "end_date": request.GET.get("end_date", "").strip() or None,
        "status": request.GET.get("status", "").strip(),
        "stock_status": request.GET.get("stock_status", "").strip(),
    }

    return ImportExportService.export_data(
        module=module,
        export_format=export_format,
        filters=filters,
        company_id=company_id,
        user=request.user,
    )


@login_required_custom
@manager_required
def import_dataset(request: HttpRequest) -> HttpResponse:
    """
    Handle two-step import:
    Step 1: Upload & Validate (Preview)
    Step 2: Confirm & Import into Database atomically
    """
    company_id = getattr(request.user.active_company, "id", None) if getattr(request.user, "active_company", None) else None

    if request.method == "POST":
        action = request.POST.get("action", "preview")
        module = request.POST.get("module", "products").lower().strip()

        if action == "preview":
            uploaded_file = request.FILES.get("file")
            if not uploaded_file:
                messages.error(request, "Please select a file (.csv, .xlsx, or .json) to upload.")
                return redirect("core_app:import_export_hub")

            validation = ImportExportService.validate_and_preview_import(
                uploaded_file=uploaded_file,
                module=module,
                company_id=company_id,
            )

            if not validation.get("valid"):
                messages.error(request, validation.get("error", "Invalid file format or missing columns."))
                return redirect("core_app:import_export_hub")

            # Parse full file rows for confirm step
            # Store in session (up to 500 records safely)
            _, all_rows, _ = parse_uploaded_file(uploaded_file)
            request.session["pending_import_rows"] = all_rows[:1000]
            request.session["pending_import_module"] = module

            return render(request, "core_app/import_preview.html", {
                "module": module,
                "headers": validation.get("headers", []),
                "preview_rows": validation.get("preview_rows", []),
                "total_records": validation.get("total_records", 0),
            })

        elif action == "confirm":
            rows = request.session.pop("pending_import_rows", None)
            saved_module = request.session.pop("pending_import_module", module)

            if not rows:
                messages.error(request, "No pending import data found. Please upload again.")
                return redirect("core_app:import_export_hub")

            result = ImportExportService.execute_import(
                module=saved_module,
                rows=rows,
                company_id=company_id,
                user=request.user,
            )

            if result.get("success"):
                imported = result.get("imported", 0)
                skipped = result.get("skipped", 0)
                errs = result.get("errors", [])
                if errs:
                    messages.warning(
                        request,
                        f"Import completed with warnings: {imported} imported, {skipped} skipped duplicates, {len(errs)} errors: {'; '.join(errs[:3])}"
                    )
                else:
                    messages.success(
                        request,
                        f"Successfully imported {imported} records into {saved_module.capitalize()}! ({skipped} duplicates skipped)."
                    )
            else:
                messages.error(request, "Failed to import records.")

            return redirect("core_app:import_export_hub")

    return redirect("core_app:import_export_hub")
