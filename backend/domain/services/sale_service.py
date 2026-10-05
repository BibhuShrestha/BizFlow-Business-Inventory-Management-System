"""
SaleService -- Sale invoice creation and cancellation with stock management.
"""
import logging
import uuid
from decimal import Decimal
from typing import Any

from django.db import transaction
from django.utils import timezone

from domain.exceptions import InsufficientStockError, NotFoundError, ValidationError
from domain.services.stock_service import StockService

logger = logging.getLogger(__name__)


class SaleService:
    """Manages sale invoice lifecycle including stock movements."""

    @staticmethod
    def generate_invoice_number() -> str:
        """Generate a unique invoice number in format INV-XXXXXXXX."""
        return f"INV-{uuid.uuid4().hex[:8].upper()}"

    @staticmethod
    def calculate_line_item(quantity: int, unit_price: Decimal, discount: Decimal = Decimal("0.00"), tax_rate: Decimal = Decimal("0.00")) -> dict[str, Decimal]:
        """Calculate line item financial amounts with precision."""
        subtotal = (Decimal(quantity) * unit_price) - discount
        tax_amount = (subtotal * (tax_rate / Decimal("100"))).quantize(Decimal("0.01"))
        total = (subtotal + tax_amount).quantize(Decimal("0.01"))
        return {
            "subtotal": subtotal,
            "tax_amount": tax_amount,
            "total": total,
        }

    @staticmethod
    @transaction.atomic
    def create(data: dict | Any, user: Any = None) -> Any:
        """
        Create a sale invoice with line items and deduct product stock atomically.
        """
        from apps.sales.models import Sale, SaleItem
        from apps.inventory.models import StockMovement

        # Support both dictionary and dataclass/object
        if isinstance(data, dict):
            items_data = data.get("items", [])
            customer_id = data.get("customer_id")
            company_id = data.get("company_id")
            sale_date = data.get("sale_date")
            payment_method = data.get("payment_method", "Cash")
            payment_status = data.get("payment_status", "Due")
            discount = Decimal(str(data.get("discount", "0.00")))
            notes = data.get("notes", "")
            bill_number = data.get("bill_number", "")
            cheque_number = data.get("cheque_number", "")
            cheque_date = data.get("cheque_date")
        else:
            items_data = getattr(data, "items", [])
            customer_id = getattr(data, "customer_id", None)
            company_id = getattr(data, "company_id", None)
            sale_date = getattr(data, "sale_date", None)
            payment_method = getattr(data, "payment_method", "Cash")
            payment_status = getattr(data, "payment_status", "Due")
            discount = getattr(data, "discount", Decimal("0.00"))
            notes = getattr(data, "notes", "")
            bill_number = getattr(data, "bill_number", "") or ""
            cheque_number = getattr(data, "cheque_number", "") or ""
            cheque_date = getattr(data, "cheque_date", None)

        if not items_data:
            raise ValidationError("A sale must have at least one line item.")

        if not company_id and user and hasattr(user, "active_company_id"):
            company_id = user.active_company_id

        sale = Sale(
            invoice_number=SaleService.generate_invoice_number(),
            bill_number=bill_number,
            customer_id=customer_id,
            company_id=company_id,
            sale_date=sale_date or timezone.now(),
            payment_method=payment_method,
            payment_status=payment_status,
            discount=discount,
            notes=notes,
            cheque_number=cheque_number,
            cheque_date=cheque_date,
        )
        sale.save()

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

            # Fetch product to verify and get selling price if not provided
            from apps.inventory.models import Product
            product = Product.objects.get(pk=product_id)
            if unit_price is None:
                unit_price = product.selling_price
            if tax_rate == Decimal("0.00") and product.tax_rate:
                tax_rate = product.tax_rate

            calc = SaleService.calculate_line_item(quantity, unit_price, item_discount, tax_rate)

            SaleItem.objects.create(
                sale=sale,
                product=product,
                quantity=quantity,
                unit_price=unit_price,
                discount=item_discount,
                tax_rate=tax_rate,
                total=calc["total"],
            )

            # Atomically deduct inventory
            StockService.deduct(
                product_id=product_id,
                quantity=quantity,
                reference_type=StockMovement.REFERENCE_SALE,
                reference_id=sale.id,
                description=f"Sale {sale.invoice_number}",
            )

            computed_total += calc["total"]

        sale.total = max(Decimal("0.00"), (computed_total - discount).quantize(Decimal("0.01")))
        sale.save(update_fields=["total"])

        if (sale.payment_method == "Cheque" or sale.cheque_number) and sale.cheque_number:
            try:
                from apps.credit.models import Cheque
                Cheque.objects.get_or_create(
                    sale=sale,
                    defaults={
                        "company": sale.company,
                        "cheque_type": Cheque.TYPE_RECEIVED,
                        "cheque_number": sale.cheque_number,
                        "bank_name": "Bank",
                        "amount": sale.total,
                        "cheque_date": sale.cheque_date or sale.sale_date.date(),
                        "customer": sale.customer,
                        "created_by": user if getattr(user, "is_authenticated", False) else None,
                        "status": Cheque.STATUS_PENDING,
                        "notes": sale.notes,
                    }
                )
            except Exception as exc:
                logger.warning("Failed to auto-create Cheque for sale %s: %s", sale.invoice_number, exc)

        logger.info("Sale invoice %s created with total Rs. %s", sale.invoice_number, sale.total)
        return sale

    @staticmethod
    @transaction.atomic
    def cancel(sale_id: int, user: Any = None) -> Any:
        """
        Cancel a sale and reverse all deducted inventory movements.
        """
        from apps.sales.models import Sale
        from apps.inventory.models import StockMovement

        try:
            sale = Sale.objects.prefetch_related("items").get(pk=sale_id, is_active=True)
        except Sale.DoesNotExist:
            raise NotFoundError(f"Sale with ID {sale_id} not found.")

        # Reverse stock
        for item in sale.items.all():
            StockService.add(
                product_id=item.product_id,
                quantity=item.quantity,
                reference_type=StockMovement.REFERENCE_SALE_CANCEL,
                reference_id=sale.id,
                description=f"Reversal for cancelled sale {sale.invoice_number}",
            )

        sale.is_active = False
        sale.save(update_fields=["is_active", "updated_at"])
        logger.info("Sale %s marked inactive and inventory restored.", sale.invoice_number)
        return sale