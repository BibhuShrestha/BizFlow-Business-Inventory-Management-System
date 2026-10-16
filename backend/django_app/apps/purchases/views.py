"""Views for Purchases, vendor bills, and stock intake."""
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
from apps.purchases.forms import PurchaseForm
from apps.purchases.models import Purchase, PurchaseItem, Supplier
from apps.inventory.models import Product, StockMovement
from apps.companies.models import Company
from apps.core_app.pagination import paginate_queryset
from apps.core_app.exports import generate_csv_response, generate_excel_response
from domain.services.stock_service import StockService


@login_required_custom
@staff_required
def purchase_list(request: HttpRequest) -> HttpResponse:
    """List purchase bills with search, status filter, and pagination."""
    search = request.GET.get("q", request.GET.get("search", "")).strip()
    status_filter = request.GET.get("status", "")
    date_from = request.GET.get("date_from", "").strip()
    date_to = request.GET.get("date_to", "").strip()

    query = Purchase.objects.select_related("supplier", "company").filter(is_active=True)
    if hasattr(request.user, "active_company") and request.user.active_company:
        query = query.filter(company=request.user.active_company)

    if search:
        query = query.filter(
            Q(purchase_number__icontains=search) |
            Q(bill_number__icontains=search) |
            Q(supplier__name__icontains=search)
        )

    if status_filter:
        query = query.filter(payment_status=status_filter)

    if date_from:
        query = query.filter(purchase_date__date__gte=date_from)
    if date_to:
        query = query.filter(purchase_date__date__lte=date_to)

    page_obj = paginate_queryset(request, query.order_by("-purchase_date"), per_page=15)
    return render(request, "purchases/purchase_list.html", {
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
    """Export all purchase bills to CSV."""
    query = Purchase.objects.select_related("supplier", "company").filter(is_active=True)
    if hasattr(request.user, "active_company") and request.user.active_company:
        query = query.filter(company=request.user.active_company)
    purchases = query.order_by("-purchase_date")
    headers = ["PO Number", "Bill #", "Date", "Supplier", "Subtotal", "Discount", "Tax", "Total", "Payment Status", "Payment Method"]
    rows = [
        [
            p.purchase_number,
            p.bill_number or "",
            p.purchase_date.strftime("%Y-%m-%d %H:%M") if p.purchase_date else "",
            p.supplier.name if p.supplier else "General Supplier",
            str(p.subtotal),
            str(p.discount),
            str(p.tax),
            str(p.total),
            p.payment_status,
            p.payment_method or "",
        ]
        for p in purchases
    ]
    return generate_csv_response(headers, rows, "purchases")


@login_required_custom
@staff_required
def export_excel(request: HttpRequest) -> HttpResponse:
    """Export all purchase bills to Excel (.xlsx)."""
    query = Purchase.objects.select_related("supplier", "company").filter(is_active=True)
    if hasattr(request.user, "active_company") and request.user.active_company:
        query = query.filter(company=request.user.active_company)
    purchases = query.order_by("-purchase_date")
    headers = ["PO Number", "Bill #", "Date", "Supplier", "Subtotal", "Discount", "Tax", "Total", "Payment Status", "Payment Method"]
    rows = [
        [
            p.purchase_number,
            p.bill_number or "",
            p.purchase_date.strftime("%Y-%m-%d %H:%M") if p.purchase_date else "",
            p.supplier.name if p.supplier else "General Supplier",
            float(p.subtotal),
            float(p.discount),
            float(p.tax),
            float(p.total),
            p.payment_status,
            p.payment_method or "",
        ]
        for p in purchases
    ]
    return generate_excel_response("Purchase Bills", headers, rows, "purchases")


@login_required_custom
@staff_required
def purchase_create(request: HttpRequest) -> HttpResponse:
    """Create a new purchase order/bill and add inventory stock atomically."""
    # Ensure at least one supplier exists
    if not Supplier.objects.filter(is_active=True).exists():
        Supplier.objects.create(name="Default Vendor", phone="9800000000", is_active=True)

    form = PurchaseForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        supplier = form.cleaned_data["supplier"]
        product = form.cleaned_data["product"]
        qty = form.cleaned_data["quantity"]
        unit_price = form.cleaned_data["unit_price"] or product.purchase_price
        discount = form.cleaned_data["discount"] or Decimal("0.00")
        bill_number = form.cleaned_data["bill_number"]
        payment_status = form.cleaned_data["payment_status"]
        payment_method = form.cleaned_data["payment_method"]
        cheque_number = form.cleaned_data["cheque_number"]
        cheque_date = form.cleaned_data["cheque_date"]
        purchase_date_input = form.cleaned_data.get("purchase_date")
        if purchase_date_input:
            import datetime
            now_time = timezone.now().time()
            combined = datetime.datetime.combine(purchase_date_input, now_time)
            purchase_date = timezone.make_aware(combined) if timezone.is_naive(combined) else combined
        else:
            purchase_date = timezone.now()
        due_date = form.cleaned_data.get("due_date")
        notes = form.cleaned_data["notes"]

        try:
            with transaction.atomic():
                subtotal = Decimal(qty) * unit_price
                tax = (subtotal - discount) * (Decimal(str(product.tax_rate or 0)) / Decimal("100"))
                total = subtotal - discount + tax
                purch_num = f"PO-{uuid.uuid4().hex[:8].upper()}"

                active_company = (
                    form.cleaned_data.get("company")
                    or getattr(request.user, "active_company", None)
                    or getattr(product, "company", None)
                    or Company.objects.first()
                )

                purchase = Purchase.objects.create(
                    purchase_number=purch_num,
                    bill_number=bill_number,
                    supplier=supplier,
                    company=active_company,
                    purchase_date=purchase_date,
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

                PurchaseItem.objects.create(
                    purchase=purchase,
                    product=product,
                    quantity=qty,
                    unit_price=unit_price,
                    discount=discount,
                    tax_rate=product.tax_rate or 0,
                    total=total,
                )

                # Add stock via StockService
                StockService.add(
                    product_id=product.id,
                    quantity=qty,
                    reference_type=StockMovement.REFERENCE_PURCHASE,
                    reference_id=purchase.id,
                    description=f"Purchase Bill #{purchase.purchase_number}",
                )

            messages.success(request, f"Purchase Bill {purchase.purchase_number} recorded successfully!")
            return redirect("purchases:detail", pk=purchase.id)

        except Exception as exc:
            messages.error(request, f"Failed to record purchase: {str(exc)}")

    companies = Company.objects.all().order_by("company_name")
    return render(request, "purchases/purchase_form.html", {
        "form": form,
        "title": "Record Purchase Bill",
        "companies": companies,
        "companies_exist": companies.exists(),
        "products_exist": Product.objects.filter(is_active=True).exists(),
    })


@login_required_custom
@staff_required
def purchase_detail(request: HttpRequest, pk: int) -> HttpResponse:
    """View purchase bill details."""
    kwargs = {"pk": pk}
    if hasattr(request.user, "active_company") and request.user.active_company:
        kwargs["company"] = request.user.active_company
    purchase = get_object_or_404(Purchase.objects.select_related("supplier", "company").prefetch_related("items__product"), **kwargs)
    return render(request, "purchases/purchase_detail.html", {"purchase": purchase})


@require_POST
@login_required_custom
@manager_required
def purchase_delete(request: HttpRequest, pk: int) -> HttpResponse:
    """Cancel purchase bill and revert product stock atomically."""
    kwargs = {"pk": pk}
    if hasattr(request.user, "active_company") and request.user.active_company:
        kwargs["company"] = request.user.active_company
    purchase = get_object_or_404(Purchase.objects.prefetch_related("items__product"), **kwargs)
    purch_num = purchase.bill_number or purchase.purchase_number

    with transaction.atomic():
        for item in purchase.items.all():
            StockService.deduct(
                product_id=item.product.id,
                quantity=item.quantity,
                reference_type=StockMovement.REFERENCE_PURCHASE_CANCEL,
                reference_id=purchase.id,
                description=f"Cancelled/Deleted Purchase Bill #{purch_num}",
            )
        purchase.delete()

    messages.success(request, f'Purchase Bill "{purch_num}" deleted and stock reverted.')
    return redirect("purchases:list")
