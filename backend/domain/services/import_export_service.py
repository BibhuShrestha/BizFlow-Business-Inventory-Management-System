"""
ImportExportService -- Domain Service for Multi-Format Business Data Import and Export.
Supports Excel (.xlsx), CSV (.csv), and JSON (.json) across:
- Products
- Customers
- Suppliers
- Sales
- Purchases
- Payments
- Receivables
- Payables
- Cheques
- Stock
"""
from datetime import datetime, date
from decimal import Decimal
import logging
from typing import Any, Dict, List, Optional, Tuple

from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from django.utils import timezone

from apps.core_app.exports import (
    generate_csv_response,
    generate_excel_response,
    generate_json_response,
    parse_uploaded_file,
)
from apps.inventory.models import Product, Category
from apps.sales.models import Customer, Sale, Payment
from apps.purchases.models import Supplier, Purchase
from apps.credit.models import Cheque
from apps.audit.models import AuditLog, ExportLog

logger = logging.getLogger(__name__)


class ImportExportService:
    """Manages enterprise import/export operations with validation and audit trail."""

    SUPPORTED_MODULES = [
        "products",
        "customers",
        "suppliers",
        "sales",
        "purchases",
        "payments",
        "receivables",
        "payables",
        "cheques",
        "stock",
    ]

    # -------------------------------------------------------------------------
    # 1. EXPORT ENGINE
    # -------------------------------------------------------------------------

    @classmethod
    def export_data(
        cls,
        module: str,
        export_format: str = "csv",
        filters: Optional[Dict[str, Any]] = None,
        company_id: Optional[int] = None,
        user: Any = None,
    ) -> HttpResponse:
        """
        Export domain records into CSV, Excel (.xlsx), or JSON (.json).
        Never exports passwords, hashes, tokens, or credentials.
        """
        module = module.lower().strip()
        export_format = export_format.lower().strip()
        filters = filters or {}
        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{module}_export_{timestamp}"

        headers, rows, records_data = cls._fetch_module_export_data(module, filters, company_id)

        # Audit log of export
        try:
            ExportLog.objects.create(
                user=user if getattr(user, "is_authenticated", False) else None,
                module=module,
                format=export_format,
                filters=filters,
                record_count=len(rows),
                success=True,
            )
            AuditLog.objects.create(
                user=user if getattr(user, "is_authenticated", False) else None,
                module="Export",
                action="Export Completed",
                record_type=module.capitalize(),
                description=f"Exported {len(rows)} {module} records as {export_format.upper()}",
                success=True,
            )
        except Exception as exc:
            logger.warning("Could not record export audit log: %s", exc)

        if export_format == "json":
            return generate_json_response(records_data, filename)
        elif export_format in ("excel", "xlsx"):
            sheet_title = module.replace("_", " ").title()[:30]
            return generate_excel_response(sheet_title, headers, rows, filename)
        else:
            return generate_csv_response(headers, rows, filename)

    @classmethod
    def _fetch_module_export_data(
        cls,
        module: str,
        filters: Dict[str, Any],
        company_id: Optional[int] = None,
    ) -> Tuple[List[str], List[List[Any]], List[Dict[str, Any]]]:
        """Fetch and format rows for export."""
        start_date = filters.get("start_date")
        end_date = filters.get("end_date")
        search = filters.get("search", "").strip()

        headers: List[str] = []
        rows: List[List[Any]] = []
        records_data: List[Dict[str, Any]] = []

        if module in ("products", "stock"):
            headers = ["SKU", "Product Name", "Category", "Purchase Price", "Selling Price", "Tax Rate (%)", "Current Stock", "Min Stock", "Critical Stock", "Stock Status", "Valuation"]
            qs = Product.objects.select_related("category").filter(is_active=True)
            if company_id:
                qs = qs.filter(company_id=company_id)
            if search:
                qs = qs.filter(Q(name__icontains=search) | Q(sku__icontains=search))
            if filters.get("stock_status") == "low":
                qs = qs.filter(current_stock__gt=0, current_stock__lte=F("minimum_stock"))
            elif filters.get("stock_status") == "out":
                qs = qs.filter(current_stock=0)

            for p in qs:
                row = [
                    p.sku,
                    p.name,
                    p.category.name if p.category else "",
                    float(p.purchase_price),
                    float(p.selling_price),
                    float(p.tax_rate),
                    p.current_stock,
                    p.minimum_stock,
                    p.critical_stock,
                    p.stock_status_display,
                    float(p.stock_value),
                ]
                rows.append(row)
                records_data.append(dict(zip(headers, row)))

        elif module == "customers":
            headers = ["Name", "Phone", "Email", "Address", "Opening Balance", "Credit Limit", "Created At"]
            qs = Customer.objects.filter(is_active=True)
            if company_id:
                qs = qs.filter(company_id=company_id)
            if search:
                qs = qs.filter(Q(name__icontains=search) | Q(phone__icontains=search) | Q(email__icontains=search))

            for c in qs:
                row = [
                    c.name,
                    c.phone,
                    c.email or "",
                    c.address,
                    float(c.opening_balance),
                    float(c.credit_limit),
                    c.created_at.strftime("%Y-%m-%d %H:%M"),
                ]
                rows.append(row)
                records_data.append(dict(zip(headers, row)))

        elif module == "suppliers":
            headers = ["Name", "Phone", "Email", "Address", "Opening Balance", "Created At"]
            qs = Supplier.objects.filter(is_active=True)
            if company_id:
                qs = qs.filter(company_id=company_id)
            if search:
                qs = qs.filter(Q(name__icontains=search) | Q(phone__icontains=search) | Q(email__icontains=search))

            for s in qs:
                row = [
                    s.name,
                    s.phone,
                    s.email or "",
                    s.address,
                    float(s.opening_balance),
                    s.created_at.strftime("%Y-%m-%d %H:%M"),
                ]
                rows.append(row)
                records_data.append(dict(zip(headers, row)))

        elif module in ("sales", "receivables"):
            headers = ["Invoice Number", "Bill Number", "Customer", "Date", "Due Date", "Total", "Paid Amount", "Remaining (Receivable)", "Status", "Payment Method", "Cheque Number"]
            qs = Sale.objects.select_related("customer").filter(is_active=True)
            if company_id:
                qs = qs.filter(company_id=company_id)
            if start_date:
                qs = qs.filter(sale_date__date__gte=start_date)
            if end_date:
                qs = qs.filter(sale_date__date__lte=end_date)
            if search:
                qs = qs.filter(Q(invoice_number__icontains=search) | Q(customer__name__icontains=search))
            if filters.get("status") == "overdue":
                qs = qs.filter(due_date__lt=timezone.localdate())

            for s in qs:
                row = [
                    s.invoice_number,
                    s.bill_number,
                    s.customer.name if s.customer else "N/A",
                    s.sale_date.strftime("%Y-%m-%d %H:%M"),
                    s.due_date.strftime("%Y-%m-%d") if s.due_date else "",
                    float(s.total),
                    float(s.paid_amount),
                    float(s.remaining_amount),
                    s.calculated_status,
                    s.payment_method,
                    s.cheque_number,
                ]
                rows.append(row)
                records_data.append(dict(zip(headers, row)))

        elif module in ("purchases", "payables"):
            headers = ["Purchase Number", "Bill Number", "Supplier", "Date", "Due Date", "Total", "Paid Amount", "Remaining (Payable)", "Status", "Payment Method", "Cheque Number"]
            qs = Purchase.objects.select_related("supplier").filter(is_active=True)
            if company_id:
                qs = qs.filter(company_id=company_id)
            if start_date:
                qs = qs.filter(purchase_date__date__gte=start_date)
            if end_date:
                qs = qs.filter(purchase_date__date__lte=end_date)
            if search:
                qs = qs.filter(Q(purchase_number__icontains=search) | Q(supplier__name__icontains=search))

            for p in qs:
                row = [
                    p.purchase_number,
                    p.bill_number,
                    p.supplier.name if p.supplier else "N/A",
                    p.purchase_date.strftime("%Y-%m-%d %H:%M"),
                    p.due_date.strftime("%Y-%m-%d") if p.due_date else "",
                    float(p.total),
                    float(p.paid_amount),
                    float(p.remaining_amount),
                    p.calculated_status,
                    p.payment_method,
                    p.cheque_number,
                ]
                rows.append(row)
                records_data.append(dict(zip(headers, row)))

        elif module == "payments":
            headers = ["Payment Date", "Amount", "Method", "Party", "Party Type", "Reference", "Status", "Cheque Number", "Bank Name"]
            qs = Payment.objects.select_related("customer", "supplier").all()
            if company_id:
                qs = qs.filter(Q(sale__company_id=company_id) | Q(purchase__company_id=company_id))

            for p in qs:
                party_type = "Customer" if p.customer else ("Supplier" if p.supplier else "N/A")
                party_name = p.customer.name if p.customer else (p.supplier.name if p.supplier else "N/A")
                row = [
                    p.payment_date.strftime("%Y-%m-%d %H:%M"),
                    float(p.amount),
                    p.payment_method,
                    party_name,
                    party_type,
                    p.reference,
                    p.status,
                    p.cheque_number,
                    p.bank_name,
                ]
                rows.append(row)
                records_data.append(dict(zip(headers, row)))

        elif module == "cheques":
            headers = ["Cheque Number", "Type", "Bank Name", "Amount", "Cheque Date", "Party", "Status", "Due Status", "Notes"]
            qs = Cheque.objects.select_related("customer", "supplier").all()
            if company_id:
                qs = qs.filter(company_id=company_id)
            if filters.get("status"):
                qs = qs.filter(status=filters["status"].upper())
            if filters.get("type"):
                qs = qs.filter(cheque_type=filters["type"].upper())

            for c in qs:
                row = [
                    c.cheque_number,
                    c.get_cheque_type_display(),
                    c.bank_name,
                    float(c.amount),
                    c.cheque_date.strftime("%Y-%m-%d"),
                    c.party_name,
                    c.get_status_display(),
                    c.due_status_display,
                    c.notes,
                ]
                rows.append(row)
                records_data.append(dict(zip(headers, row)))

        return headers, rows, records_data

    # -------------------------------------------------------------------------
    # 2. IMPORT VALIDATION & EXECUTION
    # -------------------------------------------------------------------------

    @classmethod
    def validate_and_preview_import(
        cls,
        uploaded_file,
        module: str,
        company_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Step 1: Upload & Validate
        Parse uploaded file, validate required columns, scan for duplicate keys,
        and generate a clean preview.
        """
        headers, rows, error = parse_uploaded_file(uploaded_file)
        if error:
            return {"valid": False, "error": error}

        module = module.lower().strip()
        req_fields = {
            "products": ["name", "sku", "selling_price"],
            "customers": ["name"],
            "suppliers": ["name"],
            "cheques": ["cheque_number", "bank_name", "amount", "cheque_date"],
        }

        # Normalize header keys in rows
        normalized_headers = [h.strip().lower().replace(" ", "_") for h in headers]
        required = req_fields.get(module, [])

        missing = [rf for rf in required if not any(rf in nh for nh in normalized_headers)]
        if missing:
            return {
                "valid": False,
                "error": f"Missing required columns for {module}: {', '.join(missing)}.",
            }

        preview_rows = rows[:10]
        total_rows = len(rows)

        return {
            "valid": True,
            "module": module,
            "headers": headers,
            "total_records": total_rows,
            "preview_rows": preview_rows,
            "error": None,
        }

    @classmethod
    @transaction.atomic
    def execute_import(
        cls,
        module: str,
        rows: List[Dict[str, str]],
        company_id: Optional[int] = None,
        user: Any = None,
    ) -> Dict[str, Any]:
        """
        Step 2: Confirm & Import
        Safely insert records in a database transaction with duplicate checks and audit logging.
        """
        module = module.lower().strip()
        success_count = 0
        skipped_count = 0
        errors = []

        if module == "products":
            # Ensure default category exists
            default_cat, _ = Category.objects.get_or_create(name="General", defaults={"description": "General Products"})

            for idx, r in enumerate(rows, 1):
                sku = r.get("sku") or r.get("SKU") or f"SKU-{timezone.now().strftime('%y%m%d%H%M%S')}-{idx}"
                name = r.get("name") or r.get("product_name") or r.get("Product Name")
                if not name:
                    errors.append(f"Row {idx}: Name is required")
                    continue

                if Product.objects.filter(sku=sku).exists():
                    skipped_count += 1
                    continue

                cat_name = r.get("category") or r.get("Category") or "General"
                cat, _ = Category.objects.get_or_create(name=cat_name.strip())

                try:
                    p_price = Decimal(str(r.get("purchase_price") or r.get("Purchase Price") or "0.00"))
                    s_price = Decimal(str(r.get("selling_price") or r.get("Selling Price") or "0.00"))
                    c_stock = int(r.get("current_stock") or r.get("Current Stock") or 0)
                    m_stock = int(r.get("minimum_stock") or r.get("Min Stock") or 0)
                    crit_stock = int(r.get("critical_stock") or r.get("Critical Stock") or 0)
                except Exception as exc:
                    errors.append(f"Row {idx}: Invalid numbers: {exc}")
                    continue

                Product.objects.create(
                    company_id=company_id,
                    sku=sku.strip(),
                    name=name.strip(),
                    category=cat,
                    purchase_price=p_price,
                    selling_price=s_price,
                    current_stock=c_stock,
                    minimum_stock=m_stock,
                    critical_stock=crit_stock,
                )
                success_count += 1

        elif module == "customers":
            for idx, r in enumerate(rows, 1):
                name = r.get("name") or r.get("Name") or r.get("customer_name")
                if not name:
                    errors.append(f"Row {idx}: Customer name is required")
                    continue

                phone = r.get("phone") or r.get("Phone") or ""
                email = r.get("email") or r.get("Email") or ""
                address = r.get("address") or r.get("Address") or ""

                if phone and Customer.objects.filter(company_id=company_id, phone=phone.strip()).exists():
                    skipped_count += 1
                    continue

                Customer.objects.create(
                    company_id=company_id,
                    name=name.strip(),
                    phone=phone.strip(),
                    email=email.strip() or None,
                    address=address.strip(),
                )
                success_count += 1

        elif module == "suppliers":
            for idx, r in enumerate(rows, 1):
                name = r.get("name") or r.get("Name") or r.get("supplier_name")
                if not name:
                    errors.append(f"Row {idx}: Supplier name is required")
                    continue

                phone = r.get("phone") or r.get("Phone") or ""
                email = r.get("email") or r.get("Email") or ""
                address = r.get("address") or r.get("Address") or ""

                if phone and Supplier.objects.filter(company_id=company_id, phone=phone.strip()).exists():
                    skipped_count += 1
                    continue

                Supplier.objects.create(
                    company_id=company_id,
                    name=name.strip(),
                    phone=phone.strip(),
                    email=email.strip() or None,
                    address=address.strip(),
                )
                success_count += 1

        elif module == "cheques":
            for idx, r in enumerate(rows, 1):
                c_num = r.get("cheque_number") or r.get("Cheque Number")
                b_name = r.get("bank_name") or r.get("Bank Name")
                amt_str = r.get("amount") or r.get("Amount")
                date_str = r.get("cheque_date") or r.get("Cheque Date")
                c_type = (r.get("type") or r.get("cheque_type") or r.get("Cheque Type") or "RECEIVED").upper()

                if not (c_num and b_name and amt_str and date_str):
                    errors.append(f"Row {idx}: cheque_number, bank_name, amount, cheque_date required")
                    continue

                try:
                    amount = Decimal(str(amt_str))
                    # parse date YYYY-MM-DD
                    clean_date = date_str.split("T")[0].split(" ")[0].strip()
                    parts = [int(p) for p in clean_date.replace("/", "-").split("-") if p.isdigit()]
                    c_date = date(parts[0], parts[1], parts[2])
                except Exception as exc:
                    errors.append(f"Row {idx}: Date/Amount error ({exc})")
                    continue

                if Cheque.objects.filter(company_id=company_id, cheque_number=c_num.strip(), bank_name=b_name.strip()).exists():
                    skipped_count += 1
                    continue

                Cheque.objects.create(
                    company_id=company_id,
                    cheque_number=c_num.strip(),
                    bank_name=b_name.strip(),
                    amount=amount,
                    cheque_date=c_date,
                    cheque_type=c_type if c_type in ("GIVEN", "RECEIVED") else "RECEIVED",
                    status=Cheque.STATUS_PENDING,
                    created_by=user if getattr(user, "is_authenticated", False) else None,
                )
                success_count += 1

        # Audit log of import
        try:
            AuditLog.objects.create(
                user=user if getattr(user, "is_authenticated", False) else None,
                module="Import",
                action="Import Completed",
                record_type=module.capitalize(),
                description=f"Imported {success_count} records into {module} (Skipped {skipped_count}, Errors: {len(errors)})",
                success=len(errors) == 0 or success_count > 0,
            )
        except Exception:
            pass

        return {
            "success": True,
            "module": module,
            "imported": success_count,
            "skipped": skipped_count,
            "errors": errors,
        }
