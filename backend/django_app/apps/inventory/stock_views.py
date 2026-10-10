"""Stock movements and adjustment views."""
from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from apps.accounts.permissions import login_required_custom, staff_required, manager_required
from apps.inventory.forms import StockAdjustmentForm
from apps.inventory.models import StockMovement
from apps.core_app.pagination import paginate_queryset
from domain.services.stock_service import StockService


@login_required_custom
@staff_required
def stock_movements(request: HttpRequest) -> HttpResponse:
    """List stock movement ledger."""
    movement_type = request.GET.get("type", "")
    query = StockMovement.objects.select_related("product").all()

    if movement_type in ("IN", "OUT"):
        query = query.filter(movement_type=movement_type)

    page_obj = paginate_queryset(request, query.order_by("-created_at"), per_page=20)
    return render(request, "inventory/stock_movements.html", {
        "page_obj": page_obj,
        "movement_type": movement_type,
    })


@login_required_custom
@manager_required
def stock_adjust(request: HttpRequest) -> HttpResponse:
    """Perform a manual stock adjustment."""
    form = StockAdjustmentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        product = form.cleaned_data["product"]
        adj_type = form.cleaned_data["adjustment_type"]
        qty = form.cleaned_data["quantity"]
        reason = form.cleaned_data["reason"]

        try:
            StockService.adjust(
                product_id=product.id,
                quantity=qty,
                movement_type=adj_type,
                description=reason,
            )
            messages.success(request, f"Adjusted stock for {product.name} ({adj_type} {qty}).")
            return redirect("stock:movements")
        except Exception as exc:
            messages.error(request, str(exc))

    return render(request, "inventory/stock_adjust.html", {"form": form})
