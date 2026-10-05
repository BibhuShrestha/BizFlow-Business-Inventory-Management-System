"""
FastAPI REST router for Cheque Management.
Prefix: /api/v1/cheques
"""
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.deps import get_current_user
from api.schemas.cheque import (
    ChequeCreateRequest,
    ChequeResponse,
    ChequeStatusUpdateRequest,
    ChequeSummaryResponse,
)
from apps.credit.models import Cheque
from domain.exceptions import NotFoundError, ValidationError
from domain.services.credit_service import CreditService

router = APIRouter(prefix="/cheques", tags=["Cheque Management"])


def _serialize_cheque(c: Cheque) -> dict:
    party = ""
    if c.cheque_type == Cheque.ChequeType.GIVEN:
        party = c.supplier.name if c.supplier else "Supplier"
    else:
        party = c.customer.name if c.customer else "Customer"

    return {
        "id": c.id,
        "cheque_type": c.cheque_type,
        "cheque_number": c.cheque_number,
        "bank_name": c.bank_name,
        "amount": c.amount,
        "cheque_date": c.cheque_date,
        "status": c.status,
        "party_name": party,
        "sale_invoice": c.sale.invoice_number if c.sale else None,
        "purchase_bill": c.purchase.bill_number if c.purchase else None,
        "days_until_due": c.days_until_due,
        "is_due_today": c.is_due_today,
        "is_overdue": c.is_overdue,
        "is_due_soon": c.is_due_soon,
        "notes": c.notes,
    }


@router.get("/summary", response_model=ChequeSummaryResponse, summary="Cheques KPI Summary")
def get_cheques_summary(current_user: Any = Depends(get_current_user)):
    """Retrieve summary KPIs for cheques given and received."""
    company_id = getattr(current_user.active_company, "id", None)
    return CreditService.get_cheques_summary(company_id=company_id)


@router.get("/", summary="List Cheques")
def list_cheques(
    cheque_type: Optional[str] = Query(None, description="Filter by GIVEN or RECEIVED"),
    status_filter: Optional[str] = Query(None, alias="status", description="PENDING, CLEARED, BOUNCED, CANCELLED"),
    q: Optional[str] = Query(None, description="Search cheque number, bank, party"),
    current_user: Any = Depends(get_current_user),
):
    """List cheques with optional filtering by type, status, and search."""
    company_id = getattr(current_user.active_company, "id", None)
    qs = Cheque.objects.filter(is_active=True).select_related("customer", "supplier", "sale", "purchase")
    if company_id:
        qs = qs.filter(company_id=company_id)

    if cheque_type:
        qs = qs.filter(cheque_type=cheque_type.upper())
    if status_filter:
        qs = qs.filter(status=status_filter.upper())
    if q:
        from django.db.models import Q
        qs = qs.filter(
            Q(cheque_number__icontains=q)
            | Q(bank_name__icontains=q)
            | Q(customer__name__icontains=q)
            | Q(supplier__name__icontains=q)
        )

    return [_serialize_cheque(c) for c in qs.order_by("cheque_date")[:200]]


@router.post("/", response_model=ChequeResponse, status_code=status.HTTP_201_CREATED, summary="Create Cheque")
def create_cheque(payload: ChequeCreateRequest, current_user: Any = Depends(get_current_user)):
    """Record a newly issued or received cheque."""
    company_id = getattr(current_user.active_company, "id", None)
    try:
        cheque = CreditService.create_cheque(
            cheque_type=payload.cheque_type,
            cheque_number=payload.cheque_number,
            bank_name=payload.bank_name,
            amount=payload.amount,
            cheque_date=payload.cheque_date,
            customer_id=payload.customer_id,
            supplier_id=payload.supplier_id,
            sale_id=payload.sale_id,
            purchase_id=payload.purchase_id,
            notes=payload.notes or "",
            company_id=company_id,
            user=current_user,
        )
        return _serialize_cheque(cheque)
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/{cheque_id}", response_model=ChequeResponse, summary="Get Cheque Detail")
def get_cheque(cheque_id: int, current_user: Any = Depends(get_current_user)):
    """Get single cheque details."""
    company_id = getattr(current_user.active_company, "id", None)
    qs = Cheque.objects.filter(id=cheque_id, is_active=True).select_related("customer", "supplier", "sale", "purchase")
    if company_id:
        qs = qs.filter(company_id=company_id)
    cheque = qs.first()
    if not cheque:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cheque not found.")
    return _serialize_cheque(cheque)


@router.patch("/{cheque_id}/status", response_model=ChequeResponse, summary="Update Cheque Status")
def update_cheque_status(
    cheque_id: int,
    payload: ChequeStatusUpdateRequest,
    current_user: Any = Depends(get_current_user),
):
    """Transition cheque status (e.g. mark Cleared, Bounced, Cancelled)."""
    try:
        cheque = CreditService.update_cheque_status(
            cheque_id=cheque_id,
            status=payload.status,
            notes=payload.notes or "",
            user=current_user,
        )
        return _serialize_cheque(cheque)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
