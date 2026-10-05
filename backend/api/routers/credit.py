"""
FastAPI REST router for Receivables & Payables Management.
Prefix: /api/v1/credit
"""
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.deps import get_current_user, require_role
from api.schemas.credit import (
    CreditGivenCreateRequest,
    CreditTakenCreateRequest,
    CreditSummaryResponse,
    PaymentAddRequest,
)
from apps.sales.models import Sale, Payment, Customer
from apps.purchases.models import Purchase, Supplier
from domain.services.credit_service import CreditService
from domain.exceptions import InsufficientStockError, NotFoundError, ValidationError

router = APIRouter(prefix="/credit", tags=["Receivables & Payables"])


@router.get("/summary", response_model=CreditSummaryResponse, summary="Get Credit KPIs and Summary")
def get_credit_summary(
    current_user: Any = Depends(get_current_user),
):
    """Retrieve business-wide credit KPIs including receivables, payables, and overdue amounts."""
    company_id = getattr(current_user.active_company, "id", None)
    return CreditService.get_credit_summary(company_id=company_id)


@router.get("/given", summary="List Credit Given (Customer Receivables)")
def list_credit_given(
    q: Optional[str] = Query(None, description="Search query"),
    status: Optional[str] = Query(None, description="unpaid, partially paid, paid, overdue"),
    customer_id: Optional[int] = Query(None, description="Filter by customer ID"),
    current_user: Any = Depends(get_current_user),
):
    """List customer sales invoices on credit with outstanding balances and status."""
    company_id = getattr(current_user.active_company, "id", None)
    query = Sale.objects.select_related("customer", "company").prefetch_related("payments").filter(is_active=True)

    if company_id:
        query = query.filter(company_id=company_id)
    if customer_id:
        query = query.filter(customer_id=customer_id)
    if q:
        query = query.filter(invoice_number__icontains=q)

    results = []
    for s in query.order_by("-sale_date")[:100]:
        calc_st = s.calculated_status
        if status and calc_st.lower() != status.lower():
            continue
        results.append({
            "id": s.id,
            "invoice_number": s.invoice_number,
            "bill_number": s.bill_number,
            "sale_date": s.sale_date.isoformat(),
            "due_date": s.due_date.isoformat() if s.due_date else None,
            "customer_id": s.customer_id,
            "customer_name": s.customer.name if s.customer else "Walk-in",
            "customer_phone": s.customer.phone if s.customer else "",
            "subtotal": float(s.subtotal),
            "discount": float(s.discount),
            "tax": float(s.tax),
            "total": float(s.total),
            "paid_amount": float(s.paid_amount),
            "remaining_amount": float(s.remaining_amount),
            "calculated_status": calc_st,
            "is_overdue": s.is_overdue,
        })
    return results


@router.post("/given", status_code=status.HTTP_201_CREATED, summary="Record Credit Given (Customer Sale)")
def create_credit_given(
    payload: CreditGivenCreateRequest,
    current_user: Any = Depends(require_role("admin", "owner", "manager", "staff")),
):
    """Record goods given to a customer on credit. Atomically deducts stock."""
    items = [item.model_dump() for item in payload.items]
    company_id = getattr(current_user.active_company, "id", None)
    sale_dt = datetime.combine(payload.sale_date, datetime.min.time()) if payload.sale_date else None

    try:
        sale = CreditService.create_credit_given(
            customer_id=payload.customer_id,
            items=items,
            due_date=payload.due_date,
            sale_date=sale_dt,
            bill_number=payload.bill_number or "",
            discount=payload.discount or Decimal("0.00"),
            initial_paid_amount=payload.initial_paid_amount or Decimal("0.00"),
            payment_method=payload.payment_method or "Cash",
            notes=payload.notes or "",
            company_id=company_id,
            user=current_user,
        )
        return {
            "success": True,
            "message": "Credit Given recorded successfully",
            "sale_id": sale.id,
            "invoice_number": sale.invoice_number,
            "total": float(sale.total),
            "remaining_amount": float(sale.remaining_amount),
            "status": sale.calculated_status,
        }
    except InsufficientStockError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except (ValidationError, NotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/given/{id}", summary="Get Credit Given Details")
def get_credit_given_detail(
    id: int,
    current_user: Any = Depends(get_current_user),
):
    """Retrieve full details, line items, and payment vouchers for a Credit Given sale."""
    try:
        s = Sale.objects.select_related("customer", "company").prefetch_related("items__product", "payments__created_by").get(pk=id, is_active=True)
    except Sale.DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Sale #{id} not found.")

    items = [
        {
            "id": it.id,
            "product_id": it.product_id,
            "product_name": it.product.name,
            "quantity": it.quantity,
            "unit_price": float(it.unit_price),
            "tax_rate": float(it.tax_rate),
            "discount": float(it.discount),
            "total": float(it.total),
        }
        for it in s.items.all()
    ]

    payments = [
        {
            "id": p.id,
            "payment_date": p.payment_date.isoformat(),
            "amount": float(p.amount),
            "payment_method": p.payment_method,
            "reference": p.reference,
            "notes": p.display_notes,
            "added_by": p.created_by.name if p.created_by else None,
        }
        for p in s.payments.all()
    ]

    return {
        "id": s.id,
        "invoice_number": s.invoice_number,
        "bill_number": s.bill_number,
        "customer": {"id": s.customer.id, "name": s.customer.name, "phone": s.customer.phone} if s.customer else None,
        "sale_date": s.sale_date.isoformat(),
        "due_date": s.due_date.isoformat() if s.due_date else None,
        "subtotal": float(s.subtotal),
        "discount": float(s.discount),
        "tax": float(s.tax),
        "total": float(s.total),
        "paid_amount": float(s.paid_amount),
        "remaining_amount": float(s.remaining_amount),
        "calculated_status": s.calculated_status,
        "is_overdue": s.is_overdue,
        "items": items,
        "payments": payments,
    }


@router.delete("/given/{id}", summary="Delete Credit Given (Cancel Sale & Restore Stock)")
def delete_credit_given(
    id: int,
    current_user: Any = Depends(require_role("admin", "owner", "manager")),
):
    """Delete/cancel a credit given invoice and restore product stock."""
    try:
        CreditService.delete_credit(credit_type="given", transaction_id=id, user=current_user)
        return {"success": True, "message": f"Credit invoice #{id} deleted and stock restored."}
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/taken", summary="List Credit Taken (Supplier Payables)")
def list_credit_taken(
    q: Optional[str] = Query(None, description="Search query"),
    status: Optional[str] = Query(None, description="unpaid, partially paid, paid, overdue"),
    supplier_id: Optional[int] = Query(None, description="Filter by supplier ID"),
    current_user: Any = Depends(get_current_user),
):
    """List purchase bills acquired from suppliers on credit with outstanding liabilities."""
    company_id = getattr(current_user.active_company, "id", None)
    query = Purchase.objects.select_related("supplier", "company").prefetch_related("payments").filter(is_active=True)

    if company_id:
        query = query.filter(company_id=company_id)
    if supplier_id:
        query = query.filter(supplier_id=supplier_id)
    if q:
        query = query.filter(purchase_number__icontains=q)

    results = []
    for p in query.order_by("-purchase_date")[:100]:
        calc_st = p.calculated_status
        if status and calc_st.lower() != status.lower():
            continue
        results.append({
            "id": p.id,
            "purchase_number": p.purchase_number,
            "bill_number": p.bill_number,
            "purchase_date": p.purchase_date.isoformat(),
            "due_date": p.due_date.isoformat() if p.due_date else None,
            "supplier_id": p.supplier_id,
            "supplier_name": p.supplier.name if p.supplier else "Vendor",
            "supplier_phone": p.supplier.phone if p.supplier else "",
            "subtotal": float(p.subtotal),
            "discount": float(p.discount),
            "tax": float(p.tax),
            "total": float(p.total),
            "paid_amount": float(p.paid_amount),
            "remaining_amount": float(p.remaining_amount),
            "calculated_status": calc_st,
            "is_overdue": p.is_overdue,
        })
    return results


@router.post("/taken", status_code=status.HTTP_201_CREATED, summary="Record Credit Taken (Supplier Purchase)")
def create_credit_taken(
    payload: CreditTakenCreateRequest,
    current_user: Any = Depends(require_role("admin", "owner", "manager", "staff")),
):
    """Record goods acquired on credit from a vendor. Atomically increments stock."""
    items = [item.model_dump() for item in payload.items]
    company_id = getattr(current_user.active_company, "id", None)
    po_dt = datetime.combine(payload.purchase_date, datetime.min.time()) if payload.purchase_date else None

    try:
        purchase = CreditService.create_credit_taken(
            supplier_id=payload.supplier_id,
            items=items,
            due_date=payload.due_date,
            purchase_date=po_dt,
            bill_number=payload.bill_number or "",
            discount=payload.discount or Decimal("0.00"),
            initial_paid_amount=payload.initial_paid_amount or Decimal("0.00"),
            payment_method=payload.payment_method or "Cash",
            notes=payload.notes or "",
            company_id=company_id,
            user=current_user,
        )
        return {
            "success": True,
            "message": "Credit Taken recorded successfully",
            "purchase_id": purchase.id,
            "purchase_number": purchase.purchase_number,
            "total": float(purchase.total),
            "remaining_amount": float(purchase.remaining_amount),
            "status": purchase.calculated_status,
        }
    except (ValidationError, NotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/taken/{id}", summary="Get Credit Taken Details")
def get_credit_taken_detail(
    id: int,
    current_user: Any = Depends(get_current_user),
):
    """Retrieve full details, line items, and payment vouchers for a Credit Taken purchase."""
    try:
        p = Purchase.objects.select_related("supplier", "company").prefetch_related("items__product", "payments__created_by").get(pk=id, is_active=True)
    except Purchase.DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Purchase #{id} not found.")

    items = [
        {
            "id": it.id,
            "product_id": it.product_id,
            "product_name": it.product.name,
            "quantity": it.quantity,
            "unit_price": float(it.unit_price),
            "tax_rate": float(it.tax_rate),
            "discount": float(it.discount),
            "total": float(it.total),
        }
        for it in p.items.all()
    ]

    payments = [
        {
            "id": pay.id,
            "payment_date": pay.payment_date.isoformat(),
            "amount": float(pay.amount),
            "payment_method": pay.payment_method,
            "reference": pay.reference,
            "notes": pay.display_notes,
            "added_by": pay.created_by.name if pay.created_by else None,
        }
        for pay in p.payments.all()
    ]

    return {
        "id": p.id,
        "purchase_number": p.purchase_number,
        "bill_number": p.bill_number,
        "supplier": {"id": p.supplier.id, "name": p.supplier.name, "phone": p.supplier.phone} if p.supplier else None,
        "purchase_date": p.purchase_date.isoformat(),
        "due_date": p.due_date.isoformat() if p.due_date else None,
        "subtotal": float(p.subtotal),
        "discount": float(p.discount),
        "tax": float(p.tax),
        "total": float(p.total),
        "paid_amount": float(p.paid_amount),
        "remaining_amount": float(p.remaining_amount),
        "calculated_status": p.calculated_status,
        "is_overdue": p.is_overdue,
        "items": items,
        "payments": payments,
    }


@router.delete("/taken/{id}", summary="Delete Credit Taken (Cancel Purchase & Deduct Stock)")
def delete_credit_taken(
    id: int,
    current_user: Any = Depends(require_role("admin", "owner", "manager")),
):
    """Delete/cancel a credit purchase bill and reverse added stock."""
    try:
        CreditService.delete_credit(credit_type="taken", transaction_id=id, user=current_user)
        return {"success": True, "message": f"Credit purchase #{id} deleted and stock deducted."}
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.post("/payment", status_code=status.HTTP_201_CREATED, summary="Record Payment Voucher")
def add_payment_voucher(
    payload: PaymentAddRequest,
    current_user: Any = Depends(require_role("admin", "owner", "manager", "staff")),
):
    """Record partial or full payment against a credit transaction. Inventory is untouched."""
    p_date = datetime.combine(payload.payment_date, datetime.min.time()) if payload.payment_date else None
    try:
        payment = CreditService.add_payment(
            credit_type=payload.credit_type,
            transaction_id=payload.transaction_id,
            amount=payload.amount,
            payment_method=payload.payment_method or "Cash",
            payment_date=p_date,
            reference=payload.reference or "",
            notes=payload.notes or "",
            user=current_user,
        )
        return {
            "success": True,
            "message": "Payment recorded successfully",
            "payment_id": payment.id,
            "amount": float(payment.amount),
            "payment_method": payment.payment_method,
        }
    except (ValidationError, NotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.delete("/payment/{id}", summary="Delete Payment Voucher")
def delete_payment_voucher(
    id: int,
    current_user: Any = Depends(require_role("admin", "owner", "manager")),
):
    """Delete a payment voucher and restore outstanding balance on the linked transaction."""
    try:
        CreditService.delete_payment(payment_id=id, user=current_user)
        return {"success": True, "message": f"Payment voucher #{id} deleted and balance restored."}
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/payments", summary="List Payment Vouchers")
def list_payments(
    method: Optional[str] = Query(None),
    current_user: Any = Depends(get_current_user),
):
    """Retrieve chronological payment vouchers across customers and suppliers."""
    payments = Payment.objects.select_related("customer", "supplier", "sale", "purchase", "created_by").filter(status__iexact="Completed")
    if method:
        payments = payments.filter(payment_method=method)

    results = []
    for p in payments.order_by("-payment_date")[:100]:
        results.append({
            "id": p.id,
            "payment_date": p.payment_date.isoformat(),
            "amount": float(p.amount),
            "payment_method": p.payment_method,
            "reference": p.reference,
            "notes": p.display_notes,
            "customer_name": p.customer.name if p.customer else None,
            "supplier_name": p.supplier.name if p.supplier else None,
            "sale_invoice": p.sale.invoice_number if p.sale else None,
            "purchase_number": p.purchase.purchase_number if p.purchase else None,
            "added_by": p.created_by.name if p.created_by else None,
        })
    return results


@router.get("/dues/customers", summary="List Customer Dues")
def get_customers_dues(
    current_user: Any = Depends(get_current_user),
):
    """Get list of customers with outstanding credit balances and overdue amounts."""
    company_id = getattr(current_user.active_company, "id", None)
    dues = CreditService.get_customers_dues(company_id=company_id)
    return [
        {
            "customer_id": d["customer"].id,
            "customer_name": d["customer"].name,
            "phone": d["customer"].phone,
            "total_credit": float(d["total_credit"]),
            "total_paid": float(d["total_paid"]),
            "remaining_due": float(d["remaining_due"]),
            "overdue_amount": float(d["overdue_amount"]),
            "invoice_count": d["invoice_count"],
        }
        for d in dues
    ]


@router.get("/dues/suppliers", summary="List Supplier Payables")
def get_suppliers_dues(
    current_user: Any = Depends(get_current_user),
):
    """Get list of suppliers with outstanding credit payables and overdue amounts."""
    company_id = getattr(current_user.active_company, "id", None)
    dues = CreditService.get_suppliers_dues(company_id=company_id)
    return [
        {
            "supplier_id": d["supplier"].id,
            "supplier_name": d["supplier"].name,
            "phone": d["supplier"].phone,
            "total_credit": float(d["total_credit"]),
            "total_paid": float(d["total_paid"]),
            "remaining_payable": float(d["remaining_payable"]),
            "overdue_amount": float(d["overdue_amount"]),
            "bill_count": d["bill_count"],
        }
        for d in dues
    ]


@router.get("/ledger/customer/{id}", summary="Get Customer Ledger Statement")
def get_customer_ledger(
    id: int,
    current_user: Any = Depends(get_current_user),
):
    """Retrieve full chronological statement of account for a customer with running balance."""
    try:
        data = CreditService.get_customer_ledger(customer_id=id)
        rows = [
            {
                "date": r["date"].isoformat(),
                "type": r["type"],
                "reference": r["reference"],
                "description": r["description"],
                "debit": float(r["debit"]),
                "credit": float(r["credit"]),
                "running_balance": float(r["running_balance"]),
            }
            for r in data["ledger_rows"]
        ]
        return {
            "customer_id": data["customer"].id,
            "customer_name": data["customer"].name,
            "opening_balance": float(data["opening_balance"]),
            "total_credit_given": float(data["total_credit_given"]),
            "total_paid": float(data["total_paid"]),
            "remaining_due": float(data["remaining_due"]),
            "overdue_amount": float(data["overdue_amount"]),
            "ledger_rows": rows,
        }
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/ledger/supplier/{id}", summary="Get Supplier Ledger Statement")
def get_supplier_ledger(
    id: int,
    current_user: Any = Depends(get_current_user),
):
    """Retrieve full chronological statement of account for a supplier with running balance."""
    try:
        data = CreditService.get_supplier_ledger(supplier_id=id)
        rows = [
            {
                "date": r["date"].isoformat(),
                "type": r["type"],
                "reference": r["reference"],
                "description": r["description"],
                "credit": float(r["credit"]),
                "debit": float(r["debit"]),
                "running_balance": float(r["running_balance"]),
            }
            for r in data["ledger_rows"]
        ]
        return {
            "supplier_id": data["supplier"].id,
            "supplier_name": data["supplier"].name,
            "opening_balance": float(data["opening_balance"]),
            "total_credit_taken": float(data["total_credit_taken"]),
            "total_paid": float(data["total_paid"]),
            "remaining_payable": float(data["remaining_payable"]),
            "overdue_amount": float(data["overdue_amount"]),
            "ledger_rows": rows,
        }
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
