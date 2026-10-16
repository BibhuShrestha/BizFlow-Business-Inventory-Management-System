"""Views for Sales transactions, invoices, and printing."""
from decimal import Decimal
import uuid

from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.accounts.permissions import login_required_custom, staff_required, manager_required
from apps.sales.forms import SaleForm
from apps.sales.models import Sale, SaleItem, Customer
from apps.inventory.models import Product, StockMovement
from apps.companies.models import Company
from apps.core_app.pagination import paginate_queryset
from apps.core_app.exports import generate_csv_response, generate_excel_response
from domain.services.sale_service import SaleService
from domain.services.stock_service import StockService


@login_required_custom
@staff_required
def sale_list(request: HttpRequest) -> HttpResponse:
    """List sales invoices with search, status filtering, and pagination."""
    search = request.GET.get("q", request.GET.get("search", "")).strip()
    status_filter = request.GET.get("status", "")
    date_from = request.GET.get("date_from", "").strip()
    date_to = request.GET.get("date_to", "").strip()

    query = Sale.objects.select_related("customer", "company").filter(is_active=True)
    if hasattr(request.user, "active_company") and request.user.active_company:
        query = query.filter(company=request.user.active_company)

    if search:
        query = query.filter(
            Q(invoice_number__icontains=search) |
            Q(bill_number__icontains=search) |
            Q(customer__name__icontains=search)
        )

    if status_filter:
        query = query.filter(payment_status=status_filter)

    if date_from:
        query = query.filter(sale_date__date__gte=date_from)
    if date_to:
        query = query.filter(sale_date__date__lte=date_to)

    page_obj = paginate_queryset(request, query.order_by("-sale_date"), per_page=15)
    return render(request, "sales/sale_list.html", {
        "page_obj": page_obj,
        "search_query": search,
        "search": search,
        "status_filter": status_filter,
        "date_from": date_from,
        "date_to": date_to,
    })


@login_required_custom
@staff_required
def export_csv(request: HttpRequest) -> HttpResponse:
    """Export all sales invoices to CSV."""
    query = Sale.objects.select_related("customer", "company").filter(is_active=True)
    if hasattr(request.user, "active_company") and request.user.active_company:
        query = query.filter(company=request.user.active_company)
    sales = query.order_by("-sale_date")
    headers = ["Invoice #", "Bill #", "Date", "Customer", "Subtotal", "Discount", "Tax", "Total", "Payment Status", "Payment Method"]
    rows = [
        [
            s.invoice_number,
            s.bill_number or "",
            s.sale_date.strftime("%Y-%m-%d %H:%M") if s.sale_date else "",
            s.customer.name if s.customer else "Walk-in Customer",
            str(s.subtotal),
            str(s.discount),
            str(s.tax),
            str(s.total),
            s.payment_status,
            s.payment_method or "",
        ]
        for s in sales
    ]
    return generate_csv_response(headers, rows, "sales_invoices")


@login_required_custom
@staff_required
def export_excel(request: HttpRequest) -> HttpResponse:
    """Export all sales invoices to Excel (.xlsx)."""
    query = Sale.objects.select_related("customer", "company").filter(is_active=True)
    if hasattr(request.user, "active_company") and request.user.active_company:
        query = query.filter(company=request.user.active_company)
    sales = query.order_by("-sale_date")
    headers = ["Invoice #", "Bill #", "Date", "Customer", "Subtotal", "Discount", "Tax", "Total", "Payment Status", "Payment Method"]
    rows = [
        [
            s.invoice_number,
            s.bill_number or "",
            s.sale_date.strftime("%Y-%m-%d %H:%M") if s.sale_date else "",
            s.customer.name if s.customer else "Walk-in Customer",
            float(s.subtotal),
            float(s.discount),
            float(s.tax),
            float(s.total),
            s.payment_status,
            s.payment_method or "",
        ]
        for s in sales
    ]
    return generate_excel_response("Sales Invoices", headers, rows, "sales_invoices")


@login_required_custom
@staff_required
def sale_create(request: HttpRequest) -> HttpResponse:
    """Record a new sale invoice and deduct inventory stock atomically."""
    # Ensure default customer exists if database is fresh
    if not Customer.objects.filter(is_active=True).exists():
        Customer.objects.create(name="Walk-in Customer", phone="9800000000", is_active=True)

    form = SaleForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        customer = form.cleaned_data["customer"]
        product = form.cleaned_data["product"]
        qty = form.cleaned_data["quantity"]
        unit_price = form.cleaned_data["unit_price"] or product.selling_price
        discount = form.cleaned_data["discount"] or Decimal("0.00")
        bill_number = form.cleaned_data["bill_number"]
        payment_status = form.cleaned_data["payment_status"]
        payment_method = form.cleaned_data["payment_method"]
        cheque_number = form.cleaned_data["cheque_number"]
        cheque_date = form.cleaned_data["cheque_date"]
        sale_date_input = form.cleaned_data.get("sale_date")
        if sale_date_input:
            import datetime
            now_time = timezone.now().time()
            combined = datetime.datetime.combine(sale_date_input, now_time)
            sale_date = timezone.make_aware(combined) if timezone.is_naive(combined) else combined
        else:
            sale_date = timezone.now()
        due_date = form.cleaned_data.get("due_date")
        notes = form.cleaned_data["notes"]

        if product.current_stock < qty:
            messages.error(request, f'Insufficient stock for "{product.name}". Available: {product.current_stock}, Requested: {qty}.')
            return render(request, "sales/sale_form.html", {"form": form})

        try:
            with transaction.atomic():
                subtotal = Decimal(qty) * unit_price
                tax = (subtotal - discount) * (Decimal(str(product.tax_rate or 0)) / Decimal("100"))
                total = subtotal - discount + tax
                inv_num = f"INV-{uuid.uuid4().hex[:8].upper()}"

                active_company = (
                    form.cleaned_data.get("company")
                    or getattr(request.user, "active_company", None)
                    or getattr(product, "company", None)
                    or Company.objects.first()
                )

                sale = Sale.objects.create(
                    invoice_number=inv_num,
                    bill_number=bill_number,
                    customer=customer,
                    company=active_company,
                    sale_date=sale_date,
                    due_date=due_date,
                    discount=discount,
                    tax=tax,
                    total=total,
                    payment_status=payment_status,
                    payment_method=payment_method,
                    cheque_number=cheque_number,
                    cheque_date=cheque_date,
                    notes=notes,
                )

                SaleItem.objects.create(
                    sale=sale,
                    product=product,
                    quantity=qty,
                    unit_price=unit_price,
                    tax_rate=product.tax_rate or 0,
                    discount=discount,
                    total=total,
                )

                # Deduct stock via StockService
                StockService.deduct(
                    product_id=product.id,
                    quantity=qty,
                    reference_type=StockMovement.REFERENCE_SALE,
                    reference_id=sale.id,
                    description=f"Sale Invoice #{sale.invoice_number}",
                )

            messages.success(request, f"Sale Invoice {sale.invoice_number} recorded successfully!")
            return redirect("sales:detail", pk=sale.id)

        except Exception as exc:
            messages.error(request, f"Failed to record sale: {str(exc)}")

    companies = Company.objects.all().order_by("company_name")
    return render(request, "sales/sale_form.html", {
        "form": form,
        "title": "Create Sales Invoice",
        "companies": companies,
        "companies_exist": companies.exists(),
        "products_exist": Product.objects.filter(is_active=True).exists(),
    })


@login_required_custom
@staff_required
def sale_detail(request: HttpRequest, pk: int) -> HttpResponse:
    """View sale invoice details with print-ready formatting."""
    kwargs = {"pk": pk}
    if hasattr(request.user, "active_company") and request.user.active_company:
        kwargs["company"] = request.user.active_company
    sale = get_object_or_404(Sale.objects.select_related("customer", "company").prefetch_related("items__product"), **kwargs)
    return render(request, "sales/sale_detail.html", {"sale": sale})


@require_POST
@login_required_custom
@manager_required
def sale_delete(request: HttpRequest, pk: int) -> HttpResponse:
    """Cancel/delete a sale invoice and restore stock atomically."""
    kwargs = {"pk": pk}
    if hasattr(request.user, "active_company") and request.user.active_company:
        kwargs["company"] = request.user.active_company
    sale = get_object_or_404(Sale.objects.prefetch_related("items__product"), **kwargs)
    inv_num = sale.bill_number or sale.invoice_number

    with transaction.atomic():
        for item in sale.items.all():
            StockService.add(
                product_id=item.product.id,
                quantity=item.quantity,
                reference_type=StockMovement.REFERENCE_SALE_CANCEL,
                reference_id=sale.id,
                description=f"Cancelled/Deleted Sale Invoice #{inv_num}",
            )
        sale.delete()

    messages.success(request, f'Sale Invoice "{inv_num}" deleted and stock restored.')
    return redirect("sales:list")
