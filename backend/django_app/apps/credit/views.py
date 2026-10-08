"""
Views for Receivables & Payables Management.
"""
from datetime import datetime
from decimal import Decimal
import logging

from django.contrib import messages
from django.db.models import Q, Sum
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.accounts.permissions import login_required_custom, staff_required, manager_required
from apps.sales.models import Sale, Payment, Customer
from apps.purchases.models import Purchase, Supplier
from apps.inventory.models import Product
from apps.credit.models import Cheque
from apps.core_app.pagination import paginate_queryset
from apps.core_app.exports import generate_csv_response, generate_excel_response, generate_json_response
from apps.credit.forms import CreditEntryForm, PaymentAddForm, ChequeForm
from domain.services.credit_service import CreditService
from domain.services.import_export_service import ImportExportService
from domain.exceptions import InsufficientStockError, NotFoundError, ValidationError

logger = logging.getLogger(__name__)


@login_required_custom
@staff_required
def dashboard(request: HttpRequest) -> HttpResponse:
    """Receivables & Payables Dashboard overview with KPIs, quick actions, and recent activity."""
    company_id = getattr(request.user.active_company, "id", None)
    summary = CreditService.get_credit_summary(company_id=company_id)

    recent_given = Sale.objects.select_related("customer").filter(is_active=True).order_by("-sale_date")[:5]
    recent_taken = Purchase.objects.select_related("supplier").filter(is_active=True).order_by("-purchase_date")[:5]
    recent_payments = Payment.objects.select_related("customer", "supplier", "sale", "purchase", "created_by").order_by("-payment_date")[:6]

    return render(request, "credit/dashboard.html", {
        "summary": summary,
        "recent_given": recent_given,
        "recent_taken": recent_taken,
        "recent_payments": recent_payments,
    })


@login_required_custom
@staff_required
def credit_given_list(request: HttpRequest) -> HttpResponse:
    """List of Credit Given / Receivables (Sales invoices with credit)."""
    search = request.GET.get("q", request.GET.get("search", "")).strip()
    status_filter = request.GET.get("status", "")
    customer_id = request.GET.get("customer", "")

    query = Sale.objects.select_related("customer", "company").prefetch_related("payments").filter(is_active=True)

    if search:
        query = query.filter(
            Q(invoice_number__icontains=search) |
            Q(bill_number__icontains=search) |
            Q(customer__name__icontains=search) |
            Q(customer__phone__icontains=search)
        )

    company_id = getattr(request.user.active_company, "id", None) if getattr(request.user, "active_company", None) else None
    if company_id:
        query = query.filter(company_id=company_id)

    if customer_id:
        query = query.filter(customer_id=customer_id)

    # In-memory status filtering only when needed because status is dynamic based on payments and due date
    if status_filter:
        sales = [s for s in query.order_by("-sale_date") if s.calculated_status.lower() == status_filter.lower()]
        page_obj = paginate_queryset(request, sales, per_page=15)
    else:
        page_obj = paginate_queryset(request, query.order_by("-sale_date"), per_page=15)

    customers = Customer.objects.filter(is_active=True)
    if company_id:
        customers = customers.filter(company_id=company_id)
    customers = customers.order_by("name")

    return render(request, "credit/credit_given_list.html", {
        "page_obj": page_obj,
        "search": search,
        "status_filter": status_filter,
        "customer_filter": customer_id,
        "customers": customers,
    })


@login_required_custom
@staff_required
def credit_taken_list(request: HttpRequest) -> HttpResponse:
    """List of Credit Taken / Payables (Purchases from suppliers on credit)."""
    search = request.GET.get("q", request.GET.get("search", "")).strip()
    status_filter = request.GET.get("status", "")
    supplier_id = request.GET.get("supplier", "")

    query = Purchase.objects.select_related("supplier", "company").prefetch_related("payments").filter(is_active=True)
    company_id = getattr(request.user.active_company, "id", None) if getattr(request.user, "active_company", None) else None
    if company_id:
        query = query.filter(company_id=company_id)

    if search:
        query = query.filter(
            Q(purchase_number__icontains=search) |
            Q(bill_number__icontains=search) |
            Q(supplier__name__icontains=search) |
            Q(supplier__phone__icontains=search)
        )

    if supplier_id:
        query = query.filter(supplier_id=supplier_id)

    if status_filter:
        purchases = [p for p in query.order_by("-purchase_date") if p.calculated_status.lower() == status_filter.lower()]
        page_obj = paginate_queryset(request, purchases, per_page=15)
    else:
        page_obj = paginate_queryset(request, query.order_by("-purchase_date"), per_page=15)

    suppliers = Supplier.objects.filter(is_active=True)
    if company_id:
        suppliers = suppliers.filter(company_id=company_id)
    suppliers = suppliers.order_by("name")

    return render(request, "credit/credit_taken_list.html", {
        "page_obj": page_obj,
        "search": search,
        "status_filter": status_filter,
        "supplier_filter": supplier_id,
        "suppliers": suppliers,
    })


@login_required_custom
@staff_required
def credit_create(request: HttpRequest) -> HttpResponse:
    """Unified entry form for Credit Given and Credit Taken with multiple product line items."""
    products = Product.objects.filter(is_active=True).order_by("name")

    if request.method == "POST":
        form = CreditEntryForm(request.POST)
        if form.is_valid():
            credit_type = form.cleaned_data["credit_type"]
            customer = form.cleaned_data["customer"]
            supplier = form.cleaned_data["supplier"]
            txn_date = form.cleaned_data["transaction_date"]
            due_date = form.cleaned_data["due_date"]
            bill_number = form.cleaned_data["bill_number"]
            discount = form.cleaned_data["discount"] or Decimal("0.00")
            initial_paid = form.cleaned_data["initial_paid_amount"] or Decimal("0.00")
            payment_method = form.cleaned_data["payment_method"]
            notes = form.cleaned_data["notes"]

            # Parse multiple products from POST arrays
            product_ids = request.POST.getlist("product_id[]")
            quantities = request.POST.getlist("quantity[]")
            unit_prices = request.POST.getlist("unit_price[]")
            tax_rates = request.POST.getlist("tax_rate[]")
            discounts = request.POST.getlist("item_discount[]")

            items = []
            for i in range(len(product_ids)):
                p_id = product_ids[i].strip()
                if not p_id:
                    continue
                qty = int(quantities[i]) if i < len(quantities) and quantities[i].isdigit() else 1
                price = Decimal(str(unit_prices[i])) if i < len(unit_prices) and unit_prices[i] else None
                tax = Decimal(str(tax_rates[i])) if i < len(tax_rates) and tax_rates[i] else Decimal("0.00")
                item_disc = Decimal(str(discounts[i])) if i < len(discounts) and discounts[i] else Decimal("0.00")
                items.append({
                    "product_id": int(p_id),
                    "quantity": qty,
                    "unit_price": price,
                    "tax_rate": tax,
                    "discount": item_disc,
                })

            if not items:
                messages.error(request, "Please add at least one product line item.")
                return render(request, "credit/credit_form.html", {"form": form, "products": products})

            company_id = getattr(request.user.active_company, "id", None)

            try:
                if credit_type == "given":
                    sale = CreditService.create_credit_given(
                        customer_id=customer.id,
                        items=items,
                        due_date=due_date,
                        sale_date=datetime.combine(txn_date, datetime.min.time()),
                        bill_number=bill_number,
                        discount=discount,
                        initial_paid_amount=initial_paid,
                        payment_method=payment_method,
                        notes=notes,
                        company_id=company_id,
                        user=request.user,
                    )
                    messages.success(request, f"Credit Given recorded! Invoice #{sale.invoice_number} created.")
                    return redirect("credit:given_detail", pk=sale.id)

                else:
                    purchase = CreditService.create_credit_taken(
                        supplier_id=supplier.id,
                        items=items,
                        due_date=due_date,
                        purchase_date=datetime.combine(txn_date, datetime.min.time()),
                        bill_number=bill_number,
                        discount=discount,
                        initial_paid_amount=initial_paid,
                        payment_method=payment_method,
                        notes=notes,
                        company_id=company_id,
                        user=request.user,
                    )
                    messages.success(request, f"Credit Taken recorded! Purchase Order #{purchase.purchase_number} created.")
                    return redirect("credit:taken_detail", pk=purchase.id)

            except InsufficientStockError as exc:
                messages.error(request, f"Stock error: {str(exc)}")
            except ValidationError as exc:
                messages.error(request, f"Validation error: {str(exc)}")
            except Exception as exc:
                logger.exception("Error creating credit transaction")
                messages.error(request, f"Failed to record credit: {str(exc)}")
    else:
        # Prepopulate credit_type if passed in query param (?type=given or ?type=taken)
        initial_type = request.GET.get("type", "given")
        form = CreditEntryForm(initial={"credit_type": initial_type})

    return render(request, "credit/credit_form.html", {
        "form": form,
        "products": products,
    })


@login_required_custom
@staff_required
def credit_given_detail(request: HttpRequest, pk: int) -> HttpResponse:
    """Detail view for Credit Given invoice."""
    sale = get_object_or_404(
        Sale.objects.select_related("customer", "company").prefetch_related("items__product", "payments__created_by"),
        pk=pk,
    )
    payment_form = PaymentAddForm(initial={"amount": sale.remaining_amount})
    return render(request, "credit/credit_given_detail.html", {
        "sale": sale,
        "payment_form": payment_form,
    })


@login_required_custom
@staff_required
def credit_taken_detail(request: HttpRequest, pk: int) -> HttpResponse:
    """Detail view for Credit Taken purchase bill."""
    purchase = get_object_or_404(
        Purchase.objects.select_related("supplier", "company").prefetch_related("items__product", "payments__created_by"),
        pk=pk,
    )
    payment_form = PaymentAddForm(initial={"amount": purchase.remaining_amount})
    return render(request, "credit/credit_taken_detail.html", {
        "purchase": purchase,
        "payment_form": payment_form,
    })


@login_required_custom
@staff_required
def payment_add(request: HttpRequest) -> HttpResponse:
    """Record a partial or full payment against a credit transaction."""
    if request.method != "POST":
        return redirect("credit:dashboard")

    credit_type = request.POST.get("credit_type", "").strip().lower()
    transaction_id = request.POST.get("transaction_id", "").strip()

    if not transaction_id.isdigit():
        messages.error(request, "Invalid transaction identifier.")
        return redirect("credit:dashboard")

    t_id = int(transaction_id)
    form = PaymentAddForm(request.POST)

    if form.is_valid():
        amt = form.cleaned_data["amount"]
        p_date = form.cleaned_data["payment_date"]
        method = form.cleaned_data["payment_method"]
        ref = form.cleaned_data["reference"]
        notes = form.cleaned_data["notes"]

        try:
            payment = CreditService.add_payment(
                credit_type=credit_type,
                transaction_id=t_id,
                amount=amt,
                payment_method=method,
                payment_date=datetime.combine(p_date, datetime.min.time()),
                reference=ref,
                notes=notes,
                user=request.user,
            )
            messages.success(request, f"Payment of Rs. {payment.amount} recorded successfully!")
        except (ValidationError, NotFoundError) as exc:
            messages.error(request, str(exc))
        except Exception as exc:
            logger.exception("Failed to record payment")
            messages.error(request, f"Failed to record payment: {str(exc)}")

    else:
        messages.error(request, "Please correct the errors in the payment form.")

    if credit_type in ("given", "sale"):
        return redirect("credit:given_detail", pk=t_id)
    return redirect("credit:taken_detail", pk=t_id)


@login_required_custom
@staff_required
def payment_list(request: HttpRequest) -> HttpResponse:
    """Payment history ledger."""
    search = request.GET.get("q", "").strip()
    method_filter = request.GET.get("method", "")

    payments = Payment.objects.select_related("customer", "supplier", "sale", "purchase", "created_by").filter(
        status__iexact="Completed"
    )

    if search:
        payments = payments.filter(
            Q(reference__icontains=search) |
            Q(customer__name__icontains=search) |
            Q(supplier__name__icontains=search) |
            Q(sale__invoice_number__icontains=search) |
            Q(purchase__purchase_number__icontains=search)
        )

    if method_filter:
        payments = payments.filter(payment_method=method_filter)

    page_obj = paginate_queryset(request, payments.order_by("-payment_date", "-id"), per_page=20)
    total_amount = payments.aggregate(s=Sum("amount"))["s"] or Decimal("0.00")

    return render(request, "credit/payment_list.html", {
        "page_obj": page_obj,
        "search": search,
        "method_filter": method_filter,
        "total_amount": total_amount,
    })


@login_required_custom
@manager_required
def payment_delete(request: HttpRequest, pk: int) -> HttpResponse:
    """Delete payment voucher and recalculate parent balance."""
    payment = get_object_or_404(Payment, pk=pk)
    redirect_target = "credit:payment_list"
    parent_id = None
    parent_type = None

    if payment.sale_id:
        parent_id = payment.sale_id
        parent_type = "given"
    elif payment.purchase_id:
        parent_id = payment.purchase_id
        parent_type = "taken"

    try:
        CreditService.delete_payment(payment_id=pk, user=request.user)
        messages.success(request, f"Payment voucher #{pk} deleted.")
    except Exception as exc:
        messages.error(request, f"Failed to delete payment: {str(exc)}")

    if parent_type == "given" and parent_id:
        return redirect("credit:given_detail", pk=parent_id)
    elif parent_type == "taken" and parent_id:
        return redirect("credit:taken_detail", pk=parent_id)
    return redirect(redirect_target)


@login_required_custom
@manager_required
def credit_given_delete(request: HttpRequest, pk: int) -> HttpResponse:
    """Delete/cancel credit given sale and restore inventory."""
    try:
        CreditService.delete_credit(credit_type="given", transaction_id=pk, user=request.user)
        messages.success(request, f"Credit invoice #{pk} deleted and inventory restored.")
    except Exception as exc:
        messages.error(request, f"Failed to delete credit: {str(exc)}")
    return redirect("credit:given_list")


@login_required_custom
@manager_required
def credit_taken_delete(request: HttpRequest, pk: int) -> HttpResponse:
    """Delete/cancel credit taken purchase and reverse inventory."""
    try:
        CreditService.delete_credit(credit_type="taken", transaction_id=pk, user=request.user)
        messages.success(request, f"Credit purchase #{pk} deleted and inventory restored.")
    except Exception as exc:
        messages.error(request, f"Failed to delete credit: {str(exc)}")
    return redirect("credit:taken_list")


@login_required_custom
@staff_required
def customers_dues(request: HttpRequest) -> HttpResponse:
    """Customer-wise outstanding credit dues summary."""
    company_id = getattr(request.user.active_company, "id", None)
    search = request.GET.get("q", "").strip()

    dues = CreditService.get_customers_dues(company_id=company_id)

    if search:
        dues = [d for d in dues if search.lower() in d["customer"].name.lower() or search in d["customer"].phone]

    page_obj = paginate_queryset(request, dues, per_page=15)
    total_due = sum((d["remaining_due"] for d in dues), Decimal("0.00"))
    total_overdue = sum((d["overdue_amount"] for d in dues), Decimal("0.00"))

    return render(request, "credit/customers_dues.html", {
        "page_obj": page_obj,
        "search": search,
        "total_due": total_due,
        "total_overdue": total_overdue,
    })


@login_required_custom
@staff_required
def suppliers_dues(request: HttpRequest) -> HttpResponse:
    """Supplier-wise outstanding credit payables summary."""
    company_id = getattr(request.user.active_company, "id", None)
    search = request.GET.get("q", "").strip()

    dues = CreditService.get_suppliers_dues(company_id=company_id)

    if search:
        dues = [d for d in dues if search.lower() in d["supplier"].name.lower() or search in d["supplier"].phone]

    page_obj = paginate_queryset(request, dues, per_page=15)
    total_due = sum((d["remaining_payable"] for d in dues), Decimal("0.00"))
    total_overdue = sum((d["overdue_amount"] for d in dues), Decimal("0.00"))

    return render(request, "credit/suppliers_dues.html", {
        "page_obj": page_obj,
        "search": search,
        "total_due": total_due,
        "total_overdue": total_overdue,
    })


@login_required_custom
@staff_required
def overdue_list(request: HttpRequest) -> HttpResponse:
    """Overdue credit tracking view."""
    company_id = getattr(request.user.active_company, "id", None)
    today = timezone.localdate()

    sales_q = Sale.objects.select_related("customer").filter(
        is_active=True, due_date__lt=today
    )
    purchases_q = Purchase.objects.select_related("supplier").filter(
        is_active=True, due_date__lt=today
    )

    if company_id:
        sales_q = sales_q.filter(company_id=company_id)
        purchases_q = purchases_q.filter(company_id=company_id)

    overdue_given = [s for s in sales_q.order_by("due_date") if s.remaining_amount > Decimal("0.00")]
    overdue_taken = [p for p in purchases_q.order_by("due_date") if p.remaining_amount > Decimal("0.00")]

    total_overdue_given = sum((s.remaining_amount for s in overdue_given), Decimal("0.00"))
    total_overdue_taken = sum((p.remaining_amount for p in overdue_taken), Decimal("0.00"))

    active_tab = request.GET.get("tab", "given")

    return render(request, "credit/overdue_list.html", {
        "overdue_given": overdue_given,
        "overdue_taken": overdue_taken,
        "total_overdue_given": total_overdue_given,
        "total_overdue_taken": total_overdue_taken,
        "active_tab": active_tab,
    })


@login_required_custom
@staff_required
def ledger_select(request: HttpRequest) -> HttpResponse:
    """Selector page to pick a Customer or Supplier to inspect their Ledger."""
    company_id = getattr(request.user.active_company, "id", None)
    customers = Customer.objects.filter(is_active=True).order_by("name")
    suppliers = Supplier.objects.filter(is_active=True).order_by("name")
    if company_id:
        customers = customers.filter(company_id=company_id)
        suppliers = suppliers.filter(company_id=company_id)

    top_customers = CreditService.get_customers_dues(company_id=company_id)[:5]
    top_suppliers = CreditService.get_suppliers_dues(company_id=company_id)[:5]

    return render(request, "credit/ledger_select.html", {
        "customers": customers,
        "suppliers": suppliers,
        "top_customers": top_customers,
        "top_suppliers": top_suppliers,
    })


@login_required_custom
@staff_required
def customer_ledger(request: HttpRequest, pk: int) -> HttpResponse:
    """Comprehensive chronological statement/ledger for a Customer."""
    company_id = getattr(request.user.active_company, "id", None)
    customer_qs = Customer.objects.filter(pk=pk, is_active=True)
    if company_id:
        customer_qs = customer_qs.filter(company_id=company_id)
    customer = get_object_or_404(customer_qs)
    ledger_data = CreditService.get_customer_ledger(customer_id=customer.id)
    return render(request, "credit/customer_ledger.html", ledger_data)


@login_required_custom
@staff_required
def supplier_ledger(request: HttpRequest, pk: int) -> HttpResponse:
    """Comprehensive chronological statement/ledger for a Supplier."""
    company_id = getattr(request.user.active_company, "id", None)
    supplier_qs = Supplier.objects.filter(pk=pk, is_active=True)
    if company_id:
        supplier_qs = supplier_qs.filter(company_id=company_id)
    supplier = get_object_or_404(supplier_qs)
    ledger_data = CreditService.get_supplier_ledger(supplier_id=supplier.id)
    return render(request, "credit/supplier_ledger.html", ledger_data)


@login_required_custom
@staff_required
def credit_reports(request: HttpRequest) -> HttpResponse:
    """Central Credit Reports hub."""
    company_id = getattr(request.user.active_company, "id", None)
    summary = CreditService.get_credit_summary(company_id=company_id)

    return render(request, "credit/reports.html", {
        "summary": summary,
    })


@login_required_custom
@staff_required
def export_credit_csv(request: HttpRequest, report_type: str) -> HttpResponse:
    """Export various Credit reports to CSV format."""
    company_id = getattr(request.user.active_company, "id", None)
    today = timezone.localdate().isoformat()

    if report_type == "given":
        sales = Sale.objects.select_related("customer").filter(is_active=True).order_by("-sale_date")
        if company_id:
            sales = sales.filter(company_id=company_id)
        headers = ["Invoice #", "Bill #", "Date", "Due Date", "Customer", "Phone", "Total", "Paid", "Remaining", "Status"]
        rows = [
            [
                s.invoice_number,
                s.bill_number or "",
                s.sale_date.strftime("%Y-%m-%d"),
                s.due_date.isoformat() if s.due_date else "-",
                s.customer.name if s.customer else "Walk-in",
                s.customer.phone if s.customer else "",
                str(s.total),
                str(s.paid_amount),
                str(s.remaining_amount),
                s.calculated_status,
            ]
            for s in sales
        ]
        return generate_csv_response(headers, rows, f"credit_given_{today}")

    elif report_type == "taken":
        purchases = Purchase.objects.select_related("supplier").filter(is_active=True).order_by("-purchase_date")
        if company_id:
            purchases = purchases.filter(company_id=company_id)
        headers = ["PO #", "Bill #", "Date", "Due Date", "Supplier", "Phone", "Total", "Paid", "Remaining", "Status"]
        rows = [
            [
                p.purchase_number,
                p.bill_number or "",
                p.purchase_date.strftime("%Y-%m-%d"),
                p.due_date.isoformat() if p.due_date else "-",
                p.supplier.name if p.supplier else "Vendor",
                p.supplier.phone if p.supplier else "",
                str(p.total),
                str(p.paid_amount),
                str(p.remaining_amount),
                p.calculated_status,
            ]
            for p in purchases
        ]
        return generate_csv_response(headers, rows, f"credit_taken_{today}")

    elif report_type == "customer_dues":
        dues = CreditService.get_customers_dues(company_id=company_id)
        headers = ["Customer Name", "Phone", "Total Credit", "Total Paid", "Remaining Due", "Overdue Amount", "Invoices"]
        rows = [
            [
                d["customer"].name,
                d["customer"].phone,
                str(d["total_credit"]),
                str(d["total_paid"]),
                str(d["remaining_due"]),
                str(d["overdue_amount"]),
                str(d["invoice_count"]),
            ]
            for d in dues
        ]
        return generate_csv_response(headers, rows, f"customer_dues_{today}")

    elif report_type == "supplier_dues":
        dues = CreditService.get_suppliers_dues(company_id=company_id)
        headers = ["Supplier Name", "Phone", "Total Credit", "Total Paid", "Remaining Payable", "Overdue Amount", "Bills"]
        rows = [
            [
                d["supplier"].name,
                d["supplier"].phone,
                str(d["total_credit"]),
                str(d["total_paid"]),
                str(d["remaining_payable"]),
                str(d["overdue_amount"]),
                str(d["bill_count"]),
            ]
            for d in dues
        ]
        return generate_csv_response(headers, rows, f"supplier_dues_{today}")

    elif report_type == "payments":
        payments = Payment.objects.select_related("customer", "supplier", "sale", "purchase", "created_by").filter(
            status__iexact="Completed"
        ).order_by("-payment_date")
        headers = ["Voucher #", "Date", "Party", "Type", "Ref #", "Method", "Amount", "Notes", "Recorded By"]
        rows = [
            [
                f"PAY-{p.id}",
                p.payment_date.strftime("%Y-%m-%d"),
                p.customer.name if p.customer else (p.supplier.name if p.supplier else "-"),
                "Received (Customer)" if p.customer else ("Paid (Supplier)" if p.supplier else "-"),
                p.reference or (p.sale.invoice_number if p.sale else (p.purchase.purchase_number if p.purchase else "-")),
                p.payment_method,
                str(p.amount),
                p.display_notes,
                p.created_by.name if p.created_by else "-",
            ]
            for p in payments
        ]
        return generate_csv_response(headers, rows, f"payment_history_{today}")

    messages.error(request, f"Unknown report type: {report_type}")
    return redirect("credit:reports")


# -----------------------------------------------------------------------------
# CHEQUE MANAGEMENT VIEWS (Requirements 10, 11, 12, 13)
# -----------------------------------------------------------------------------

@login_required_custom
@staff_required
def cheques_list(request: HttpRequest) -> HttpResponse:
    """Cheque Management List with status tabs, search, and due schedule tracking."""
    tab = request.GET.get("tab", "all").lower().strip()
    search = request.GET.get("q", request.GET.get("search", "")).strip()
    company_id = getattr(request.user.active_company, "id", None) if getattr(request.user, "active_company", None) else None

    cheques_qs = Cheque.objects.select_related("customer", "supplier", "sale", "purchase", "company").all()
    if company_id:
        cheques_qs = cheques_qs.filter(company_id=company_id)

    today = timezone.localdate()

    if tab == "given":
        cheques_qs = cheques_qs.filter(cheque_type=Cheque.TYPE_GIVEN)
    elif tab == "received":
        cheques_qs = cheques_qs.filter(cheque_type=Cheque.TYPE_RECEIVED)
    elif tab == "due_soon":
        from datetime import timedelta
        cheques_qs = cheques_qs.filter(
            status=Cheque.STATUS_PENDING,
            cheque_date__gt=today,
            cheque_date__lte=today + timedelta(days=7),
        )
    elif tab == "due_today":
        cheques_qs = cheques_qs.filter(status=Cheque.STATUS_PENDING, cheque_date=today)
    elif tab == "overdue":
        cheques_qs = cheques_qs.filter(status=Cheque.STATUS_PENDING, cheque_date__lt=today)
    elif tab == "cleared":
        cheques_qs = cheques_qs.filter(status=Cheque.STATUS_CLEARED)
    elif tab == "bounced":
        cheques_qs = cheques_qs.filter(status=Cheque.STATUS_BOUNCED)
    elif tab == "cancelled":
        cheques_qs = cheques_qs.filter(status=Cheque.STATUS_CANCELLED)

    if search:
        cheques_qs = cheques_qs.filter(
            Q(cheque_number__icontains=search)
            | Q(bank_name__icontains=search)
            | Q(customer__name__icontains=search)
            | Q(supplier__name__icontains=search)
            | Q(notes__icontains=search)
        )

    summary = CreditService.get_cheques_summary(company_id=company_id)
    page_obj = paginate_queryset(request, cheques_qs.order_by("cheque_date", "-id"), per_page=15)

    return render(
        request,
        "credit/cheques_list.html",
        {
            "cheques": page_obj,
            "page_obj": page_obj,
            "summary": summary,
            "current_tab": tab,
            "search": search,
        },
    )


@login_required_custom
@staff_required
def cheque_create(request: HttpRequest) -> HttpResponse:
    """Record a new Cheque Given (to supplier) or Cheque Received (from customer)."""
    company_id = getattr(request.user.active_company, "id", None) if getattr(request.user, "active_company", None) else None

    if request.method == "POST":
        form = ChequeForm(request.POST)
        if form.is_valid():
            try:
                cheque = CreditService.create_cheque(
                    company_id=company_id,
                    cheque_type=form.cleaned_data["cheque_type"],
                    cheque_number=form.cleaned_data["cheque_number"],
                    bank_name=form.cleaned_data["bank_name"],
                    amount=form.cleaned_data["amount"],
                    cheque_date=form.cleaned_data["cheque_date"],
                    customer_id=form.cleaned_data["customer"].id if form.cleaned_data["customer"] else None,
                    supplier_id=form.cleaned_data["supplier"].id if form.cleaned_data["supplier"] else None,
                    notes=form.cleaned_data["notes"],
                    user=request.user,
                )
                messages.success(request, f"Cheque #{cheque.cheque_number} recorded successfully.")
                return redirect("credit:cheques_list")
            except Exception as exc:
                messages.error(request, f"Error recording cheque: {str(exc)}")
    else:
        init = {}
        c_type = request.GET.get("type", "").upper()
        if c_type in ("GIVEN", "RECEIVED"):
            init["cheque_type"] = c_type
        form = ChequeForm(initial=init)

    return render(request, "credit/cheque_form.html", {"form": form})


@login_required_custom
@staff_required
def cheque_update_status(request: HttpRequest, pk: int) -> HttpResponse:
    """Update cheque status to Cleared, Bounced, or Cancelled with notes."""
    if request.method == "POST":
        status = request.POST.get("status", "").strip()
        notes = request.POST.get("notes", "").strip()
        try:
            cheque = CreditService.update_cheque_status(
                cheque_id=pk,
                status=status,
                notes=notes,
                user=request.user,
            )
            messages.success(request, f"Cheque #{cheque.cheque_number} status updated to {cheque.get_status_display()}.")
        except Exception as exc:
            messages.error(request, f"Could not update cheque status: {str(exc)}")

    return redirect(request.META.get("HTTP_REFERER", "credit:cheques_list"))


@login_required_custom
@staff_required
def cheques_export(request: HttpRequest, export_format: str = "csv") -> HttpResponse:
    """Export cheques list into CSV, Excel (.xlsx), or JSON (.json)."""
    company_id = getattr(request.user.active_company, "id", None) if getattr(request.user, "active_company", None) else None
    return ImportExportService.export_data(
        module="cheques",
        export_format=export_format,
        filters=request.GET.dict(),
        company_id=company_id,
        user=request.user,
    )
