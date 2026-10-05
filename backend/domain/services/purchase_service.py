"""
PurchaseService -- Purchase bill creation and cancellation with stock management.
"""
import logging
import uuid
from decimal import Decimal
from typing import Any

from django.db import transaction
from django.utils import timezone

from domain.exceptions import NotFoundError, ValidationError
from domain.services.stock_service import StockService

logger = logging.getLogger(__name__)


class PurchaseService:
    """Manages purchase bills and vendor orders with inventory movements."""

    @staticmethod
    def generate_purchase_number() -> str:
        """Generate unique purchase order identifier."""
        return f"PO-{uuid.uuid4().hex[:8].upper()}"

    @staticmethod
    @transaction.atomic
    def create(data: dict | Any, user: Any = None) -> Any:
        """
        Create a purchase bill with line items and increment stock atomically.
        """
        from apps.purchases.models import Purchase, PurchaseItem
        from apps.inventory.models import StockMovement

        if isinstance(data, dict):
            items_data = data.get("items", [])
            supplier_id = data.get("supplier_id")
            company_id = data.get("company_id")
            purchase_date = data.get("purchase_date")
            payment_method = data.get("payment_method", "Cash")
            payment_status = data.get("payment_status", "Due")
            discount = Decimal(str(data.get("discount", "0.00")))
            notes = data.get("notes", "")
            bill_number = data.get("bill_number", "")
            cheque_number = data.get("cheque_number", "")
            cheque_date = data.get("cheque_date")
        else:
            items_data = getattr(data, "items", [])
            supplier_id = getattr(data, "supplier_id", None)
            company_id = getattr(data, "company_id", None)
            purchase_date = getattr(data, "purchase_date", None)
            payment_method = getattr(data, "payment_method", "Cash")
            payment_status = getattr(data, "payment_status", "Due")
            discount = getattr(data, "discount", Decimal("0.00"))
            notes = getattr(data, "notes", "")
            bill_number = getattr(data, "bill_number", "") or ""
            cheque_number = getattr(data, "cheque_number", "") or ""
            cheque_date = getattr(data, "cheque_date", None)

        if not items_data:
            raise ValidationError("A purchase bill must have at least one line item.")

        if not company_id and user and hasattr(user, "active_company_id"):
            company_id = user.active_company_id

        purchase = Purchase(
            purchase_number=PurchaseService.generate_purchase_number(),
            bill_number=bill_number,
            supplier_id=supplier_id,
            company_id=company_id,
            purchase_date=purchase_date or timezone.now(),
            payment_method=payment_method,
            payment_status=payment_status,
            discount=discount,
            notes=notes,
            cheque_number=cheque_number,
            cheque_date=cheque_date,
        )
        purchase.save()

        computed_total = Decimal("0.00")
        for item_data in items_data:
            if hasattr(item_data, "product_id"):
                product_id = item_data.product_id
                quantity = int(item_data.quantity)
                unit_price = item_data.unit_price
                item_discount = item_data.discount
                tax_rate = item_data.tax_rate
            else:
                product_id = item_data["product_id"]
                quantity = int(item_data["quantity"])
                unit_price = Decimal(str(item_data["unit_price"])) if item_data.get("unit_price") is not None else None
                item_discount = Decimal(str(item_data.get("discount", "0.00")))
                tax_rate = Decimal(str(item_data.get("tax_rate", "0.00")))

            from apps.inventory.models import Product
            product = Product.objects.get(pk=product_id)
            if unit_price is None:
                unit_price = product.purchase_price

            subtotal = (Decimal(quantity) * unit_price) - item_discount
            tax_amount = (subtotal * (tax_rate / Decimal("100"))).quantize(Decimal("0.01"))
            item_total = (subtotal + tax_amount).quantize(Decimal("0.01"))

            PurchaseItem.objects.create(
                purchase=purchase,
                product=product,
                quantity=quantity,
                unit_price=unit_price,
                discount=item_discount,
                tax_rate=tax_rate,
                total=item_total,
            )

            # Atomically increment stock
            StockService.add(
                product_id=product_id,
                quantity=quantity,
                reference_type=StockMovement.REFERENCE_PURCHASE,
                reference_id=purchase.id,
                description=f"Purchase {purchase.purchase_number}",
            )

            computed_total += item_total

        purchase.total = max(Decimal("0.00"), (computed_total - discount).quantize(Decimal("0.01")))
        purchase.save(update_fields=["total"])

        if (purchase.payment_method == "Cheque" or purchase.cheque_number) and purchase.cheque_number:
            try:
                from apps.credit.models import Cheque
                Cheque.objects.get_or_create(
                    purchase=purchase,
                    defaults={
                        "company": purchase.company,
                        "cheque_type": Cheque.TYPE_GIVEN,
                        "cheque_number": purchase.cheque_number,
                        "bank_name": "Bank",
                        "amount": purchase.total,
                        "cheque_date": purchase.cheque_date or purchase.purchase_date.date(),
                        "supplier": purchase.supplier,
                        "created_by": user if getattr(user, "is_authenticated", False) else None,
                        "status": Cheque.STATUS_PENDING,
                        "notes": purchase.notes,
                    }
                )
            except Exception as exc:
                logger.warning("Failed to auto-create Cheque for purchase %s: %s", purchase.purchase_number, exc)

        logger.info("Purchase bill %s created with total Rs. %s", purchase.purchase_number, purchase.total)
        return purchase

    @staticmethod
    @transaction.atomic
    def cancel(purchase_id: int, user: Any = None) -> Any:
        """Cancel purchase bill and reverse inventory increment."""
        from apps.purchases.models import Purchase
        from apps.inventory.models import StockMovement

        try:
            purchase = Purchase.objects.prefetch_related("items").get(pk=purchase_id, is_active=True)
        except Purchase.DoesNotExist:
            raise NotFoundError(f"Purchase with ID {purchase_id} not found.")

        for item in purchase.items.all():
            StockService.deduct(
                product_id=item.product_id,
                quantity=item.quantity,
                reference_type=StockMovement.REFERENCE_PURCHASE_CANCEL,
                reference_id=purchase.id,
                description=f"Reversal for cancelled purchase {purchase.purchase_number}",
            )

        purchase.is_active = False
        purchase.save(update_fields=["is_active", "updated_at"])
        logger.info("Purchase %s cancelled and stock deducted.", purchase.purchase_number)
        return purchase