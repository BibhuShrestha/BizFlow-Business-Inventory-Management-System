"""
Pagination helpers for list views.
"""
from django.core.paginator import Paginator, Page
from django.http import HttpRequest


def paginate_queryset(request: HttpRequest, queryset, per_page: int = 20) -> Page:
    """Paginate a queryset based on request 'page' parameter."""
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get("page", 1)
    return paginator.get_page(page_number)
