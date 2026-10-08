"""
StockService — All stock movement and inventory adjustment logic.
"""
import logging
from typing import TYPE_CHECKING

from django.db import transaction

from domain.exceptions import InsufficientStockError

if TYPE_CHECKING:
    from apps.inventory.models import Product, StockMovement

logger = logging.getLogger(__name__)


class StockService:
    """Manages all stock quantity changes and movements."""

    @staticmethod
    @transaction.atomic
    def deduct(product_id: int, quantity: int, reference_type: str, reference_id: int | None = None, description: str = "") -> "StockMovement":
        """
        Deduct stock for a sale. Raises InsufficientStockError if insufficient.

        Must be called within the same transaction as the sale creation.

        Args:
            product_id: Product to deduct from.
            quantity: Units to deduct (positive number).
            reference_type: Source of movement (e.g. SALE).
            reference_id: ID of the source record.
            description: Optional description.

        Returns:
            Created StockMovement record.

        Raises:
            InsufficientStockError: If quantity > current_stock.
        """
        from apps.inventory.models import Product, StockMovement

        product = Product.objects.select_for_update().get(pk=product_id)

        if product.current_stock < quantity:
            raise InsufficientStockError(
                product_name=product.name,
                available=product.current_stock,
                requested=quantity,
            )

        product.current_stock -= quantity
        product.save(update_fields=["current_stock", "updated_at"])

        movement = StockMovement.objects.create(
            product=product,
            movement_type=StockMovement.MOVEMENT_OUT,
            quantity=quantity,
            reference_type=reference_type,
            reference_id=reference_id,
            description=description,
        )

        logger.info(
            "Stock deducted: product=%s qty=%s (stock now %s)",
            product.name, quantity, product.current_stock,
        )

        try:
            if product.current_stock <= product.minimum_stock or product.current_stock == 0:
                from domain.services.notification_service import NotificationService
                NotificationService.check_stock_alerts(company_id=product.company_id)
        except Exception as exc:
            logger.warning("Could not dispatch stock alert: %s", exc)

        return movement

    @staticmethod
    @transaction.atomic
    def add(product_id: int, quantity: int, reference_type: str, reference_id: int | None = None, description: str = "") -> "StockMovement":
        """
        Add stock for a purchase or return.

        Args:
            product_id: Product to add stock to.
            quantity: Units to add (positive number).
            reference_type: Source of movement (e.g. PURCHASE).
            reference_id: ID of the source record.
            description: Optional description.

        Returns:
            Created StockMovement record.
        """
        from apps.inventory.models import Product, StockMovement

        product = Product.objects.select_for_update().get(pk=product_id)
        previous_stock = product.current_stock
        product.current_stock += quantity
        product.save(update_fields=["current_stock", "updated_at"])

        movement = StockMovement.objects.create(
            product=product,
            movement_type=StockMovement.MOVEMENT_IN,
            quantity=quantity,
            reference_type=reference_type,
            reference_id=reference_id,
            description=description,
        )

        logger.info(
            "Stock added: product=%s qty=%s (stock now %s)",
            product.name, quantity, product.current_stock,
        )

        try:
            from domain.services.notification_service import NotificationService
            NotificationService.notify_stock_received(
                product=product,
                quantity=quantity,
                previous_stock=previous_stock,
                new_stock=product.current_stock,
                movement_id=movement.id,
            )
        except Exception as exc:
            logger.warning("Could not dispatch stock received alert: %s", exc)

        return movement

    @staticmethod
    @transaction.atomic
    def adjust(product_id: int, quantity: int, movement_type: str, description: str = "") -> "StockMovement":
        """
        Manually adjust stock (increase or decrease).

        Args:
            product_id: Product to adjust.
            quantity: Absolute quantity (always positive).
            movement_type: IN to add, OUT to subtract.
            description: Reason for adjustment.

        Returns:
            Created StockMovement record.

        Raises:
            InsufficientStockError: If OUT would make stock negative.
        """
        from apps.inventory.models import Product, StockMovement

        product = Product.objects.select_for_update().get(pk=product_id)
        previous_stock = product.current_stock

        if movement_type == StockMovement.MOVEMENT_OUT:
            if product.current_stock < quantity:
                raise InsufficientStockError(
                    product_name=product.name,
                    available=product.current_stock,
                    requested=quantity,
                )
            product.current_stock -= quantity
        else:
            product.current_stock += quantity

        product.save(update_fields=["current_stock", "updated_at"])

        movement = StockMovement.objects.create(
            product=product,
            movement_type=movement_type,
            quantity=quantity,
            reference_type=StockMovement.REFERENCE_ADJUSTMENT,
            description=description,
        )

        logger.info(
            "Stock adjusted: product=%s type=%s qty=%s (stock now %s)",
            product.name, movement_type, quantity, product.current_stock,
        )

        try:
            from domain.services.notification_service import NotificationService
            if movement_type == StockMovement.MOVEMENT_IN:
                NotificationService.notify_stock_received(
                    product=product,
                    quantity=quantity,
                    previous_stock=previous_stock,
                    new_stock=product.current_stock,
                    movement_id=movement.id,
                )
            else:
                if product.current_stock <= product.minimum_stock or product.current_stock == 0:
                    NotificationService.check_stock_alerts(company_id=product.company_id)
        except Exception as exc:
            logger.warning("Could not dispatch stock adjustment notification: %s", exc)

        return movement

    @staticmethod
    def low_stock_products(company_id: int | None = None):
        """Return products where current_stock <= minimum_stock (active products only)."""
        from apps.inventory.models import Product
        from django.db.models import F

        qs = Product.objects.filter(
            is_active=True,
            current_stock__lte=F("minimum_stock"),
        )
        if company_id:
            qs = qs.filter(company_id=company_id)
        return qs.select_related("category").order_by("current_stock")

    @staticmethod
    def critical_stock_products(company_id: int | None = None):
        """Return products where current_stock > 0 and stock is at or below critical threshold."""
        from apps.inventory.models import Product
        from django.db.models import F

        qs = Product.objects.filter(
            is_active=True,
            current_stock__gt=0,
            current_stock__lte=F("critical_stock"),
        )
        if company_id:
            qs = qs.filter(company_id=company_id)
        return qs.select_related("category").order_by("current_stock")

    @staticmethod
    def out_of_stock_products(company_id: int | None = None):
        """Return active products with zero stock."""
        from apps.inventory.models import Product

        qs = Product.objects.filter(is_active=True, current_stock=0)
        if company_id:
            qs = qs.filter(company_id=company_id)
        return qs.select_related("category")

