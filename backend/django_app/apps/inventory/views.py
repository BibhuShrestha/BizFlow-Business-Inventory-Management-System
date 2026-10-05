"""Product and category views with search, filtering, exports, and import."""
from decimal import Decimal
import uuid
from django.contrib import messages
from django.db.models import Q, F
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.permissions import login_required_custom, staff_required, manager_required
from apps.inventory.forms import ProductForm, CategoryForm
from apps.inventory.models import Product, Category, StockMovement
from apps.companies.models import Company, Seller
from apps.core_app.exports import generate_csv_response, generate_excel_response, parse_uploaded_file
from apps.core_app.pagination import paginate_queryset
from domain.services.stock_service import StockService


@login_required_custom
def product_list(request: HttpRequest) -> HttpResponse:
    """List products with search, category/company/seller filter, low-stock filter, and sorting."""
    search = request.GET.get("search", "").strip()
    category_id = request.GET.get("category_id")
    company_id = request.GET.get("company_id")
    seller_id = request.GET.get("seller_id")
    low_stock = request.GET.get("low_stock")
    sort = request.GET.get("sort", "name")

    query = Product.objects.select_related("category", "company", "seller").filter(is_active=True)

    if search:
        query = query.filter(Q(name__icontains=search) | Q(sku__icontains=search))

    if category_id and category_id.isdigit():
        query = query.filter(category_id=int(category_id))

    if company_id and company_id.isdigit():
        query = query.filter(company_id=int(company_id))

    if seller_id and seller_id.isdigit():
        query = query.filter(seller_id=int(seller_id))

    if low_stock == "1":
        query = query.filter(current_stock__lte=F("minimum_stock"))

    valid_sorts = ["name", "-name", "current_stock", "-current_stock", "selling_price", "-selling_price", "created_at", "-created_at"]
    if sort in valid_sorts:
        query = query.order_by(sort)

    page_obj = paginate_queryset(request, query, per_page=20)

    categories = Category.objects.filter(is_active=True).order_by("name")
    companies = Company.objects.all().order_by("company_name")
    sellers = Seller.objects.all().order_by("seller_name")

    return render(request, "inventory/product_list.html", {
        "page_obj": page_obj,
        "search": search,
        "categories": categories,
        "companies": companies,
        "sellers": sellers,
        "selected_category_id": int(category_id) if category_id and category_id.isdigit() else None,
        "selected_company_id": int(company_id) if company_id and company_id.isdigit() else None,
        "selected_seller_id": int(seller_id) if seller_id and seller_id.isdigit() else None,
        "low_stock": low_stock,
        "sort": sort,
    })


from django.http import HttpRequest, HttpResponse, JsonResponse


@login_required_custom
@staff_required
def product_create(request: HttpRequest) -> HttpResponse:
    """Create a new product with AJAX and return_to redirect support."""
    form = ProductForm(request.POST or None)
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest" or request.content_type == "application/json"

    if request.method == "POST":
        if form.is_valid():
            product = form.save(commit=False)
            if not product.category_id:
                default_cat, _ = Category.objects.get_or_create(name="General", defaults={"description": "Default category"})
                product.category = default_cat
            if not product.sku:
                product.sku = f"SKU-{uuid.uuid4().hex[:6].upper()}"
            if not product.company and hasattr(request.user, "active_company") and request.user.active_company:
                product.company = request.user.active_company
            product.save()

            if product.current_stock > 0:
                StockMovement.objects.create(
                    product=product,
                    movement_type=StockMovement.MOVEMENT_IN,
                    quantity=product.current_stock,
                    reference_type=StockMovement.REFERENCE_ADJUSTMENT,
                    description=f"Initial stock for {product.name}",
                )

            if is_ajax:
                return JsonResponse({
                    "success": True,
                    "id": product.id,
                    "name": f"{product.name} ({product.sku})",
                    "selling_price": str(product.selling_price),
                    "purchase_price": str(product.purchase_price),
                    "current_stock": product.current_stock,
                    "unit": product.unit,
                    "tax_rate": str(product.tax_rate),
                    "message": f'Product "{product.name}" created successfully.',
                })

            messages.success(request, f'Product "{product.name}" created successfully.')
            next_url = request.GET.get("next") or request.POST.get("next") or request.GET.get("return_to") or request.POST.get("return_to")
            if next_url:
                sep = "&" if "?" in next_url else "?"
                return redirect(f"{next_url}{sep}product_id={product.id}")
            return redirect("inventory:product_list")
        elif is_ajax:
            return JsonResponse({"success": False, "errors": form.errors}, status=400)

    return render(request, "inventory/product_form.html", {
        "form": form,
        "title": "Add New Product",
        "return_to": request.GET.get("return_to") or request.GET.get("next") or "",
    })


@login_required_custom
@staff_required
def product_edit(request: HttpRequest, pk: int) -> HttpResponse:
    """Edit existing product."""
    product = get_object_or_404(Product, pk=pk)
    form = ProductForm(request.POST or None, instance=product)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f'Product "{product.name}" updated successfully.')
        return redirect("inventory:product_list")
    return render(request, "inventory/product_form.html", {"form": form, "product": product, "title": "Edit Product"})


@login_required_custom
@manager_required
def product_delete(request: HttpRequest, pk: int) -> HttpResponse:
    """Soft-delete product."""
    product = get_object_or_404(Product, pk=pk)
    product.is_active = False
    product.save(update_fields=["is_active"])
    messages.success(request, f'Product "{product.name}" has been deactivated.')
    return redirect("inventory:product_list")


@login_required_custom
def export_csv(request: HttpRequest) -> HttpResponse:
    """Export all items to CSV file."""
    products = Product.objects.select_related("category", "company", "seller").filter(is_active=True).order_by("name")
    headers = ["SKU", "Item Name", "Company", "Seller / Owner", "Seller Phone", "Category", "Unit", "Purchase Price", "Selling Price", "Current Stock", "Min Stock", "Active"]
    rows = [
        [
            p.sku,
            p.name,
            p.company.company_name if p.company else "",
            p.seller.seller_name if p.seller else "",
            p.seller.seller_phone if p.seller and p.seller.seller_phone else "",
            p.category.name if p.category else "",
            p.unit,
            str(p.purchase_price),
            str(p.selling_price),
            p.current_stock,
            p.minimum_stock,
            "Yes" if p.is_active else "No"
        ]
        for p in products
    ]
    return generate_csv_response(headers, rows, "items_export")


@login_required_custom
def export_excel(request: HttpRequest) -> HttpResponse:
    """Export all items to Excel (.xlsx) file."""
    products = Product.objects.select_related("category", "company", "seller").filter(is_active=True).order_by("name")
    headers = ["SKU", "Item Name", "Company", "Seller / Owner", "Seller Phone", "Category", "Unit", "Purchase Price", "Selling Price", "Current Stock", "Min Stock", "Active"]
    rows = [
        [
            p.sku,
            p.name,
            p.company.company_name if p.company else "",
            p.seller.seller_name if p.seller else "",
            p.seller.seller_phone if p.seller and p.seller.seller_phone else "",
            p.category.name if p.category else "",
            p.unit,
            float(p.purchase_price),
            float(p.selling_price),
            p.current_stock,
            p.minimum_stock,
            "Yes" if p.is_active else "No"
        ]
        for p in products
    ]
    return generate_excel_response("Items Catalog", headers, rows, "items_export")


@login_required_custom
def sample_template(request: HttpRequest) -> HttpResponse:
    """Download sample CSV template for bulk product import."""
    headers = ["SKU", "Item Name", "Company", "Seller / Owner", "Seller Phone", "Category", "Unit", "Purchase Price", "Selling Price", "Current Stock"]
    rows = [
        ["ITEM-101", "Item 1", "ABC Company", "Ram Sharma", "9800000001", "Electronics", "pcs", "50.00", "75.00", "20"],
        ["ITEM-102", "Item 2", "ABC Company", "Sita Sharma", "9800000002", "Electronics", "pcs", "100.00", "150.00", "15"],
    ]
    return generate_csv_response(headers, rows, "sample_items_template")


@login_required_custom
@staff_required
def import_products(request: HttpRequest) -> HttpResponse:
    """Bulk import products from uploaded CSV or Excel file."""
    if request.method == "POST":
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            messages.warning(request, "Please select a valid CSV or Excel file to upload.")
            return redirect("inventory:import_products")

        headers, rows_data, error = parse_uploaded_file(uploaded_file)
        if error:
            messages.error(request, error)
            return redirect("inventory:import_products")

        created_count = 0
        updated_count = 0

        default_cat, _ = Category.objects.get_or_create(name="General", defaults={"description": "General items"})

        for row in rows_data:
            sku = (row.get("SKU") or row.get("sku") or "").strip()
            name = (row.get("Item Name") or row.get("name") or row.get("Item") or "").strip()
            if not sku or not name:
                continue

            c_name = (row.get("Company") or row.get("company_name") or "").strip()
            s_name = (row.get("Seller / Owner") or row.get("seller_name") or row.get("Seller") or "").strip()
            s_phone = (row.get("Seller Phone") or row.get("seller_phone") or "").strip()
            cat_name = (row.get("Category") or row.get("category") or "").strip()

            company = Company.objects.filter(company_name=c_name).first() if c_name else None
            seller = Seller.objects.filter(seller_name=s_name).first() if s_name else None
            if cat_name:
                category, _ = Category.objects.get_or_create(name=cat_name)
            else:
                category = default_cat

            unit = (row.get("Unit") or "pcs").strip()
            try:
                p_price = Decimal(str(row.get("Purchase Price") or "0.00").replace("$", "").strip())
            except Exception:
                p_price = Decimal("0.00")

            try:
                s_price = Decimal(str(row.get("Selling Price") or "0.00").replace("$", "").strip())
            except Exception:
                s_price = Decimal("0.00")

            try:
                stock = int(float(str(row.get("Current Stock") or "0").strip()))
            except Exception:
                stock = 0

            obj, created = Product.objects.update_or_create(
                sku=sku,
                defaults={
                    "name": name,
                    "category": category,
                    "company": company,
                    "seller": seller,
                    "unit": unit,
                    "purchase_price": p_price,
                    "selling_price": s_price,
                    "current_stock": stock,
                    "is_active": True,
                }
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        messages.success(request, f"Import complete: {created_count} items created, {updated_count} items updated.")
        return redirect("inventory:product_list")

    return render(request, "inventory/import.html")


# Categories CRUD
@login_required_custom
def category_list(request: HttpRequest) -> HttpResponse:
    """List product categories."""
    categories = Category.objects.all().order_by("name")
    return render(request, "inventory/category_list.html", {"categories": categories})


@login_required_custom
@staff_required
def category_create(request: HttpRequest) -> HttpResponse:
    """Create a new category with AJAX and return_to redirect support."""
    form = CategoryForm(request.POST or None)
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest" or request.content_type == "application/json"

    if request.method == "POST":
        if form.is_valid():
            cat = form.save()
            if is_ajax:
                return JsonResponse({
                    "success": True,
                    "id": cat.id,
                    "name": cat.name,
                    "message": f'Category "{cat.name}" created.',
                })
            messages.success(request, f'Category "{cat.name}" created.')
            next_url = request.GET.get("next") or request.POST.get("next") or request.GET.get("return_to") or request.POST.get("return_to")
            if next_url:
                sep = "&" if "?" in next_url else "?"
                return redirect(f"{next_url}{sep}category_id={cat.id}")
            return redirect("inventory:category_list")
        elif is_ajax:
            return JsonResponse({"success": False, "errors": form.errors}, status=400)

    return render(request, "inventory/category_form.html", {
        "form": form,
        "title": "Create Category",
        "return_to": request.GET.get("return_to") or request.GET.get("next") or "",
    })


@login_required_custom
@staff_required
def category_edit(request: HttpRequest, pk: int) -> HttpResponse:
    """Edit a category."""
    cat = get_object_or_404(Category, pk=pk)
    form = CategoryForm(request.POST or None, instance=cat)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f'Category "{cat.name}" updated.')
        return redirect("inventory:category_list")
    return render(request, "inventory/category_form.html", {"form": form, "category": cat, "title": "Edit Category"})


@login_required_custom
@manager_required
def category_delete(request: HttpRequest, pk: int) -> HttpResponse:
    """Delete a category."""
    cat = get_object_or_404(Category, pk=pk)
    name = cat.name
    cat.delete()
    messages.success(request, f'Category "{name}" deleted.')
    return redirect("inventory:category_list")
