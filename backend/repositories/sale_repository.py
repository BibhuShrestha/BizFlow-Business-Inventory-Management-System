"""Sale repository for sales invoice queries."""
from apps.sales.models import Sale
from repositories.base import BaseRepository


class SaleRepository(BaseRepository[Sale]):
    """Data access methods for Sale entity."""

    def __init__(self):
        super().__init__(Sale)

    def get_by_invoice_number(self, invoice_number: str, company_id: int | None = None) -> Sale | None:
        """Fetch sale by invoice number."""
        qs = self.model.objects.filter(invoice_number=invoice_number)
        if company_id is not None:
            qs = qs.filter(company_id=company_id)
        return qs.prefetch_related("items__product").first()