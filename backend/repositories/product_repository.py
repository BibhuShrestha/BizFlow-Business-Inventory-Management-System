"""Product repository for catalog and inventory queries."""
from apps.inventory.models import Product
from repositories.base import BaseRepository
from django.db.models import F


class ProductRepository(BaseRepository[Product]):
    """Data access methods for Product entity."""

    def __init__(self):
        super().__init__(Product)

    def get_by_sku(self, sku: str, company_id: int | None = None) -> Product | None:
        """Fetch product by SKU."""
        qs = self.model.objects.filter(sku=sku)
        if company_id is not None:
            qs = qs.filter(company_id=company_id)
        return qs.first()

    def list_low_stock(self, company_id: int | None = None):
        """Fetch active products with current_stock <= minimum_stock."""
        qs = self.model.objects.filter(is_active=True, current_stock__lte=F("minimum_stock"))
        if company_id is not None:
            qs = qs.filter(company_id=company_id)
        return qs.select_related("category")