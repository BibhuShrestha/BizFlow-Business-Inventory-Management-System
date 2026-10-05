"""
CreditService -- Business logic for Receivables & Payables Management.
Handles:
- Receivables / Credit Given (Receivable from Customers via Sales)
- Payables / Credit Taken (Payable to Suppliers via Purchases)
- Payments (Partial & Full Payments against settlements)
- Customer & Supplier Ledgers with Running Balance
- Due date & Overdue Tracking
- Summary KPIs and Reports
- Audit logging
"""
from datetime import datetime, timedelta
from decimal import Decimal
import logging
import uuid
from typing import Any

from django.db import transaction
from django.db.models import Sum, Q
from django.utils import timezone

from apps.sales.models import Sale, SaleItem, Payment, Customer
from apps.purchases.models import Purchase, PurchaseItem, Supplier
from apps.inventory.models import Product, StockMovement
from apps.audit.models import AuditLog
from domain.exceptions import InsufficientStockError, NotFoundError, ValidationError
from domain.services.stock_service import StockService
from domain.services.sale_service import SaleService
from domain.services.purchase_service import PurchaseService

logger = logging.getLogger(__name__)


class CreditService:
    """Core domain service for Receivables and Payables Lifecycle."""

    @staticmethod
    def _log_audit(
        user: Any,
        action: str,
        record_type: str,
        record_id: int | None = None,
        description: str = "",
        details: dict | None = None,
    ) -> None:
        """Create an audit log record safely."""
        try:
            AuditLog.objects.create(
                user=user if getattr(user, "is_authenticated", False) else None,
                module="Credit",
                action=action,
                record_type=record_type,
                record_id=record_id,
                description=description,
                new_values=details,
                success=True,
            )
        except Exception as exc:
            logger.warning("Failed to record audit log for credit: %s", exc)

    @classmethod
    @transaction.atomic
    def create_credit_given(
        cls,
        customer_id: int,
        items: list[dict],
        due_date=None,
        sale_date=None,
        bill_number: str = "",
        discount: Decimal = Decimal("0.00"),
        initial_paid_amount: Decimal = Decimal("0.00"),
        payment_method: str = "Cash",
        notes: str = "",
        company_id: int | None = None,
        user: Any = None,
    ) -> Sale:
        """
        Record credit given to customer (Receivable).
        - Decrements product inventory stock atomically.
        - Records initial payment if provided.
        - Automatically computes total, balance and status.
        """
        if not items:
            raise ValidationError("At least one product item is required for credit transaction.")

        try:
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            raise NotFoundError(f"Customer with ID {customer_id} does not exist.")

        # Check stock availability for all items before any changes
        for item in items:
            p_id = item["product_id"]
            qty = int(item["quantity"])
            product = Product.objects.get(pk=p_id)
            if product.current_stock < qty:
                raise InsufficientStockError(
                    product_name=product.name,
                    available=product.current_stock,
                    requested=qty,
                )

        inv_num = SaleService.generate_invoice_number()
        target_date = sale_date or timezone.now()

        sale = Sale.objects.create(
            invoice_number=inv_num,
            bill_number=bill_number,
            customer=customer,
            company_id=company_id or getattr(customer, "company_id", None),
            sale_date=target_date,
            due_date=due_date,
            discount=discount,
            tax=Decimal("0.00"),
            total=Decimal("0.00"),
            payment_status=Sale.STATUS_DUE,
            payment_method=payment_method,
            notes=notes,
        )

        computed_subtotal = Decimal("0.00")
        computed_tax = Decimal("0.00")

        for item in items:
            p_id = item["product_id"]
            qty = int(item["quantity"])
            product = Product.objects.get(pk=p_id)
            unit_price = Decimal(str(item.get("unit_price") or product.selling_price))
            item_discount = Decimal(str(item.get("discount") or "0.00"))
            tax_rate_val = item.get("tax_rate")
            tax_rate = Decimal(str(tax_rate_val)) if tax_rate_val is not None else Decimal(str(product.tax_rate or "0.00"))

            calc = SaleService.calculate_line_item(qty, unit_price, item_discount, tax_rate)

            SaleItem.objects.create(
                sale=sale,
                product=product,
                quantity=qty,
                unit_price=unit_price,
                discount=item_discount,
                tax_rate=tax_rate,
                total=calc["total"],
            )

            StockService.deduct(
                product_id=product.id,
                quantity=qty,
                reference_type=StockMovement.REFERENCE_SALE,
                reference_id=sale.id,
                description=f"Credit Given Invoice #{sale.invoice_number} to {customer.name}",
            )

            computed_subtotal += calc["subtotal"]
            computed_tax += calc["tax_amount"]

        grand_total = max(Decimal("0.00"), (computed_subtotal + computed_tax - discount).quantize(Decimal("0.01")))
        sale.tax = computed_tax
        sale.total = grand_total

        # Handle initial payment if provided
        initial_paid = Decimal(str(initial_paid_amount or "0.00"))
        if initial_paid > grand_total:
            raise ValidationError(f"Initial payment Rs. {initial_paid} cannot exceed total Rs. {grand_total}.")

        if initial_paid > Decimal("0.00"):
            Payment.objects.create(
                payment_date=target_date,
                amount=initial_paid,
                payment_method=payment_method,
                status="Completed",
                reference=f"Initial payment for {sale.invoice_number}",
                remarks=f"Initial down payment of Rs. {initial_paid}",
                notes=f"Initial payment on {inv_num}",
                sale=sale,
                customer=customer,
                created_by=user if getattr(user, "is_authenticated", False) else None,
            )
            if initial_paid >= grand_total:
                sale.payment_status = Sale.STATUS_PAID
            else:
                sale.payment_status = Sale.STATUS_PARTIAL
        else:
            sale.payment_status = Sale.STATUS_DUE

        sale.save()

        cls._log_audit(
            user=user,
            action="Credit Created",
            record_type="Sale",
            record_id=sale.id,
            description=f"Created Credit Given #{sale.invoice_number} for Rs. {sale.total} to {customer.name}",
            details={"invoice_number": sale.invoice_number, "total": str(sale.total), "paid": str(initial_paid)},
        )

        return sale

    @classmethod
    @transaction.atomic
    def create_credit_taken(
        cls,
        supplier_id: int,
        items: list[dict],
        due_date=None,
        purchase_date=None,
        bill_number: str = "",
        discount: Decimal = Decimal("0.00"),
        initial_paid_amount: Decimal = Decimal("0.00"),
        payment_method: str = "Cash",
        notes: str = "",
        company_id: int | None = None,
        user: Any = None,
    ) -> Purchase:
        """
        Record credit taken from supplier (Payable).
        - Increments product inventory stock atomically.
        - Records initial payment if provided.
        - Automatically computes total, balance and status.
        """
        if not items:
            raise ValidationError("At least one product item is required for credit purchase.")

        try:
            supplier = Supplier.objects.get(pk=supplier_id)
        except Supplier.DoesNotExist:
            raise NotFoundError(f"Supplier with ID {supplier_id} does not exist.")

        po_num = PurchaseService.generate_purchase_number()
        target_date = purchase_date or timezone.now()

        purchase = Purchase.objects.create(
            purchase_number=po_num,
            bill_number=bill_number,
            supplier=supplier,
            company_id=company_id or getattr(supplier, "company_id", None),
            purchase_date=target_date,
            due_date=due_date,
            discount=discount,
            tax=Decimal("0.00"),
            total=Decimal("0.00"),
            payment_status=Purchase.STATUS_DUE,
            payment_method=payment_method,
            notes=notes,
        )

        computed_subtotal = Decimal("0.00")
        computed_tax = Decimal("0.00")

        for item in items:
            p_id = item["product_id"]
            qty = int(item["quantity"])
            product = Product.objects.get(pk=p_id)
            unit_price = Decimal(str(item.get("unit_price") or product.purchase_price))
            item_discount = Decimal(str(item.get("discount") or "0.00"))
            tax_rate_val = item.get("tax_rate")
            tax_rate = Decimal(str(tax_rate_val)) if tax_rate_val is not None else Decimal(str(product.tax_rate or "0.00"))

            line_subtotal = (Decimal(qty) * unit_price) - item_discount
            line_tax = (line_subtotal * (tax_rate / Decimal("100"))).quantize(Decimal("0.01"))
            line_total = (line_subtotal + line_tax).quantize(Decimal("0.01"))

            PurchaseItem.objects.create(
                purchase=purchase,
                product=product,
                quantity=qty,
                unit_price=unit_price,
                discount=item_discount,
                tax_rate=tax_rate,
                total=line_total,
            )

            StockService.add(
                product_id=product.id,
                quantity=qty,
                reference_type=StockMovement.REFERENCE_PURCHASE,
                reference_id=purchase.id,
                description=f"Credit Taken Bill #{purchase.purchase_number} from {supplier.name}",
            )

            computed_subtotal += line_subtotal
            computed_tax += line_tax

        grand_total = max(Decimal("0.00"), (computed_subtotal + computed_tax - discount).quantize(Decimal("0.01")))
        purchase.tax = computed_tax
        purchase.total = grand_total

        initial_paid = Decimal(str(initial_paid_amount or "0.00"))
        if initial_paid > grand_total:
            raise ValidationError(f"Initial payment Rs. {initial_paid} cannot exceed total Rs. {grand_total}.")

        if initial_paid > Decimal("0.00"):
            Payment.objects.create(
                payment_date=target_date,
                amount=initial_paid,
                payment_method=payment_method,
                status="Completed",
                reference=f"Initial payment for {purchase.purchase_number}",
                remarks=f"Initial payment of Rs. {initial_paid}",
                notes=f"Initial payment on {po_num}",
                purchase=purchase,
                supplier=supplier,
                created_by=user if getattr(user, "is_authenticated", False) else None,
            )
            if initial_paid >= grand_total:
                purchase.payment_status = Purchase.STATUS_PAID
            else:
                purchase.payment_status = Purchase.STATUS_PARTIAL
        else:
            purchase.payment_status = Purchase.STATUS_DUE

        purchase.save()

        cls._log_audit(
            user=user,
            action="Credit Created",
            record_type="Purchase",
            record_id=purchase.id,
            description=f"Created Credit Taken #{purchase.purchase_number} for Rs. {purchase.total} from {supplier.name}",
            details={"purchase_number": purchase.purchase_number, "total": str(purchase.total), "paid": str(initial_paid)},
        )

        return purchase

    @classmethod
    @transaction.atomic
    def add_payment(
        cls,
        credit_type: str,
        transaction_id: int,
        amount: Decimal,
        payment_method: str = "Cash",
        payment_date=None,
        reference: str = "",
        notes: str = "",
        user: Any = None,
    ) -> Payment:
        """
        Record a payment against a Credit transaction (Given or Taken).
        - DOES NOT alter inventory quantities.
        - Strictly prevents overpayment.
        - Updates outstanding balance and transaction status.
        """
        amount = Decimal(str(amount))
        if amount <= Decimal("0.00"):
            raise ValidationError("Payment amount must be greater than zero.")

        target_date = payment_date or timezone.now()

        if credit_type.lower() in ("given", "sale", "receivable"):
            try:
                sale = Sale.objects.select_related("customer").get(pk=transaction_id, is_active=True)
            except Sale.DoesNotExist:
                raise NotFoundError(f"Sale invoice with ID {transaction_id} not found.")

            remaining = sale.remaining_amount
            if amount > remaining:
                raise ValidationError(
                    f"Payment of Rs. {amount} exceeds outstanding balance of Rs. {remaining} for {sale.invoice_number}."
                )

            payment = Payment.objects.create(
                payment_date=target_date,
                amount=amount,
                payment_method=payment_method,
                status="Completed",
                reference=reference or f"Payment for {sale.invoice_number}",
                remarks=notes,
                notes=notes,
                sale=sale,
                customer=sale.customer,
                created_by=user if getattr(user, "is_authenticated", False) else None,
            )

            # Re-evaluate status
            new_remaining = sale.remaining_amount
            if new_remaining <= Decimal("0.00"):
                sale.payment_status = Sale.STATUS_PAID
            else:
                sale.payment_status = Sale.STATUS_PARTIAL
            sale.save(update_fields=["payment_status", "updated_at"])

            if payment_method.lower() == "cheque":
                try:
                    from apps.credit.models import Cheque
                    Cheque.objects.create(
                        company=sale.company,
                        cheque_type=Cheque.TYPE_RECEIVED,
                        cheque_number=reference or f"CHQ-{payment.id}",
                        bank_name="Bank",
                        amount=amount,
                        cheque_date=target_date.date() if hasattr(target_date, "date") else target_date,
                        customer=sale.customer,
                        sale=sale,
                        payment=payment,
                        status=Cheque.STATUS_PENDING,
                        notes=notes,
                        created_by=user if getattr(user, "is_authenticated", False) else None,
                    )
                except Exception as exc:
                    logger.warning("Could not create Cheque from sale payment: %s", exc)

            cls._log_audit(
                user=user,
                action="Payment Added",
                record_type="Payment",
                record_id=payment.id,
                description=f"Received payment Rs. {amount} for Sale #{sale.invoice_number}. Remaining: Rs. {new_remaining}",
                details={"sale_id": sale.id, "amount": str(amount), "payment_id": payment.id},
            )
            return payment

        elif credit_type.lower() in ("taken", "purchase", "payable"):
            try:
                purchase = Purchase.objects.select_related("supplier").get(pk=transaction_id, is_active=True)
            except Purchase.DoesNotExist:
                raise NotFoundError(f"Purchase order with ID {transaction_id} not found.")

            remaining = purchase.remaining_amount
            if amount > remaining:
                raise ValidationError(
                    f"Payment of Rs. {amount} exceeds outstanding balance of Rs. {remaining} for {purchase.purchase_number}."
                )

            payment = Payment.objects.create(
                payment_date=target_date,
                amount=amount,
                payment_method=payment_method,
                status="Completed",
                reference=reference or f"Payment for {purchase.purchase_number}",
                remarks=notes,
                notes=notes,
                purchase=purchase,
                supplier=purchase.supplier,
                created_by=user if getattr(user, "is_authenticated", False) else None,
            )

            new_remaining = purchase.remaining_amount
            if new_remaining <= Decimal("0.00"):
                purchase.payment_status = Purchase.STATUS_PAID
            else:
                purchase.payment_status = Purchase.STATUS_PARTIAL
            purchase.save(update_fields=["payment_status", "updated_at"])

            if payment_method.lower() == "cheque":
                try:
                    from apps.credit.models import Cheque
                    Cheque.objects.create(
                        company=purchase.company,
                        cheque_type=Cheque.TYPE_GIVEN,
                        cheque_number=reference or f"CHQ-{payment.id}",
                        bank_name="Bank",
                        amount=amount,
                        cheque_date=target_date.date() if hasattr(target_date, "date") else target_date,
                        supplier=purchase.supplier,
                        purchase=purchase,
                        payment=payment,
                        status=Cheque.STATUS_PENDING,
                        notes=notes,
                        created_by=user if getattr(user, "is_authenticated", False) else None,
                    )
                except Exception as exc:
                    logger.warning("Could not create Cheque from purchase payment: %s", exc)

            cls._log_audit(
                user=user,
                action="Payment Added",
                record_type="Payment",
                record_id=payment.id,
                description=f"Made payment Rs. {amount} for Purchase #{purchase.purchase_number}. Remaining: Rs. {new_remaining}",
                details={"purchase_id": purchase.id, "amount": str(amount), "payment_id": payment.id},
            )
            return payment

        else:
            raise ValidationError(f"Invalid credit type: {credit_type}. Must be 'given' or 'taken'.")

    @classmethod
    @transaction.atomic
    def delete_payment(cls, payment_id: int, user: Any = None) -> None:
        """
        Delete a payment voucher and recalculate parent transaction status.
        Does not touch inventory.
        """
        try:
            payment = Payment.objects.select_related("sale", "purchase").get(pk=payment_id)
        except Payment.DoesNotExist:
            raise NotFoundError(f"Payment voucher with ID {payment_id} not found.")

        sale = payment.sale
        purchase = payment.purchase
        amt = payment.amount

        payment.delete()

        if sale:
            sale.refresh_from_db()
            rem = sale.remaining_amount
            if sale.paid_amount <= Decimal("0.00"):
                sale.payment_status = Sale.STATUS_DUE
            elif rem <= Decimal("0.00"):
                sale.payment_status = Sale.STATUS_PAID
            else:
                sale.payment_status = Sale.STATUS_PARTIAL
            sale.save(update_fields=["payment_status", "updated_at"])

        if purchase:
            purchase.refresh_from_db()
            rem = purchase.remaining_amount
            if purchase.paid_amount <= Decimal("0.00"):
                purchase.payment_status = Purchase.STATUS_DUE
            elif rem <= Decimal("0.00"):
                purchase.payment_status = Purchase.STATUS_PAID
            else:
                purchase.payment_status = Purchase.STATUS_PARTIAL
            purchase.save(update_fields=["payment_status", "updated_at"])

        cls._log_audit(
            user=user,
            action="Payment Deleted",
            record_type="Payment",
            record_id=payment_id,
            description=f"Deleted payment voucher #{payment_id} for Rs. {amt}.",
        )

    @classmethod
    @transaction.atomic
    def delete_credit(cls, credit_type: str, transaction_id: int, user: Any = None) -> None:
        """
        Cancel/delete a credit transaction and restore stock.
        """
        if credit_type.lower() in ("given", "sale"):
            SaleService.cancel(transaction_id)
            cls._log_audit(
                user=user,
                action="Credit Deleted",
                record_type="Sale",
                record_id=transaction_id,
                description=f"Cancelled/Deleted Credit Given #{transaction_id} and restored stock.",
            )
        elif credit_type.lower() in ("taken", "purchase"):
            PurchaseService.cancel(transaction_id)
            cls._log_audit(
                user=user,
                action="Credit Deleted",
                record_type="Purchase",
                record_id=transaction_id,
                description=f"Cancelled/Deleted Credit Taken #{transaction_id} and deducted stock.",
            )
        else:
            raise ValidationError(f"Invalid credit type: {credit_type}")

    @classmethod
    def get_credit_summary(cls, company_id: int | None = None) -> dict[str, Any]:
        """
        Calculate aggregated KPIs for Credit Management:
        - Credit Given (Receivable), Received, Customer Due
        - Credit Taken (Payable), Paid to Suppliers, Supplier Due
        - Overdue Given & Taken counts and amounts
        """
        sales_q = Sale.objects.filter(is_active=True)
        purchases_q = Purchase.objects.filter(is_active=True)
        payments_sales_q = Payment.objects.filter(sale__is_active=True, status__iexact="Completed")
        payments_purchases_q = Payment.objects.filter(purchase__is_active=True, status__iexact="Completed")

        if company_id:
            sales_q = sales_q.filter(company_id=company_id)
            purchases_q = purchases_q.filter(company_id=company_id)
            payments_sales_q = payments_sales_q.filter(sale__company_id=company_id)
            payments_purchases_q = payments_purchases_q.filter(purchase__company_id=company_id)

        credit_given_total = sales_q.aggregate(s=Sum("total"))["s"] or Decimal("0.00")
        credit_given_received = payments_sales_q.aggregate(s=Sum("amount"))["s"] or Decimal("0.00")
        customer_due = max(Decimal("0.00"), credit_given_total - credit_given_received)

        credit_taken_total = purchases_q.aggregate(s=Sum("total"))["s"] or Decimal("0.00")
        credit_taken_paid = payments_purchases_q.aggregate(s=Sum("amount"))["s"] or Decimal("0.00")
        supplier_due = max(Decimal("0.00"), credit_taken_total - credit_taken_paid)

        today = timezone.localdate()

        # Overdue Given
        overdue_sales = [s for s in sales_q.filter(due_date__lt=today) if s.remaining_amount > Decimal("0.00")]
        overdue_given_count = len(overdue_sales)
        overdue_given_amount = sum((s.remaining_amount for s in overdue_sales), Decimal("0.00"))

        # Overdue Taken
        overdue_purchases = [p for p in purchases_q.filter(due_date__lt=today) if p.remaining_amount > Decimal("0.00")]
        overdue_taken_count = len(overdue_purchases)
        overdue_taken_amount = sum((p.remaining_amount for p in overdue_purchases), Decimal("0.00"))

        net_balance = customer_due - supplier_due
        net_type = "Receivable (Dr.)" if net_balance >= Decimal("0.00") else "Payable (Cr.)"

        return {
            "credit_given_total": credit_given_total,
            "credit_given_received": credit_given_received,
            "customer_due": customer_due,
            "credit_taken_total": credit_taken_total,
            "credit_taken_paid": credit_taken_paid,
            "supplier_due": supplier_due,
            "net_balance": abs(net_balance),
            "net_balance_raw": net_balance,
            "net_balance_type": net_type,
            "overdue_given_count": overdue_given_count,
            "overdue_given_amount": overdue_given_amount,
            "overdue_taken_count": overdue_taken_count,
            "overdue_taken_amount": overdue_taken_amount,
            "total_overdue_amount": overdue_given_amount + overdue_taken_amount,
            # Explicit Receivables & Payables terminology (Part 1 requirement)
            "receivables_total": credit_given_total,
            "receivables_received": credit_given_received,
            "receivables_outstanding": customer_due,
            "receivables_overdue": overdue_given_amount,
            "payables_total": credit_taken_total,
            "payables_paid": credit_taken_paid,
            "payables_outstanding": supplier_due,
            "payables_overdue": overdue_taken_amount,
        }

    @classmethod
    def get_customer_ledger(cls, customer_id: int) -> dict[str, Any]:
        """
        Generate complete chronological ledger for a specific customer.
        Returns transactions, payments, and running balance.
        """
        try:
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            raise NotFoundError(f"Customer with ID {customer_id} does not exist.")

        sales = list(Sale.objects.filter(customer=customer, is_active=True).order_by("sale_date"))
        payments = list(
            Payment.objects.filter(customer=customer, status__iexact="Completed").order_by("payment_date")
        )

        # Merge and sort chronologically
        events = []
        for s in sales:
            events.append({
                "date": s.sale_date,
                "type": "Credit Given",
                "reference": s.invoice_number,
                "bill_number": s.bill_number or "-",
                "description": f"Invoice {s.invoice_number}",
                "debit": s.total,
                "credit": Decimal("0.00"),
                "due_date": s.due_date,
                "raw_obj": s,
            })

        for p in payments:
            events.append({
                "date": p.payment_date,
                "type": "Payment Received",
                "reference": p.reference or f"Pay-{p.id}",
                "bill_number": p.sale.bill_number if p.sale and p.sale.bill_number else "-",
                "description": f"Payment via {p.payment_method} ({p.notes or p.remarks or 'Paid'})",
                "debit": Decimal("0.00"),
                "credit": p.amount,
                "due_date": None,
                "raw_obj": p,
            })

        # Sort by date
        events.sort(key=lambda x: x["date"])

        running_balance = customer.opening_balance or Decimal("0.00")
        ledger_rows = []
        today = timezone.localdate()
        total_credit_given = Decimal("0.00")
        total_paid = Decimal("0.00")

        for ev in events:
            total_credit_given += ev["debit"]
            total_paid += ev["credit"]
            running_balance += ev["debit"] - ev["credit"]
            ev_copy = dict(ev)
            ev_copy["running_balance"] = running_balance
            ledger_rows.append(ev_copy)

        remaining_due = max(Decimal("0.00"), total_credit_given - total_paid)
        overdue_amount = sum(
            (s.remaining_amount for s in sales if s.due_date and s.due_date < today and s.remaining_amount > Decimal("0.00")),
            Decimal("0.00")
        )

        return {
            "customer": customer,
            "opening_balance": customer.opening_balance or Decimal("0.00"),
            "total_credit_given": total_credit_given,
            "total_paid": total_paid,
            "remaining_due": remaining_due,
            "overdue_amount": overdue_amount,
            "ledger_rows": ledger_rows,
        }

    @classmethod
    def get_supplier_ledger(cls, supplier_id: int) -> dict[str, Any]:
        """
        Generate complete chronological ledger for a specific supplier.
        Returns purchases, payments, and running balance.
        """
        try:
            supplier = Supplier.objects.get(pk=supplier_id)
        except Supplier.DoesNotExist:
            raise NotFoundError(f"Supplier with ID {supplier_id} does not exist.")

        purchases = list(Purchase.objects.filter(supplier=supplier, is_active=True).order_by("purchase_date"))
        payments = list(
            Payment.objects.filter(supplier=supplier, status__iexact="Completed").order_by("payment_date")
        )

        events = []
        for p in purchases:
            events.append({
                "date": p.purchase_date,
                "type": "Credit Taken",
                "reference": p.purchase_number,
                "bill_number": p.bill_number or "-",
                "description": f"Purchase {p.purchase_number}",
                "credit": p.total,
                "debit": Decimal("0.00"),
                "due_date": p.due_date,
                "raw_obj": p,
            })

        for pay in payments:
            events.append({
                "date": pay.payment_date,
                "type": "Payment Made",
                "reference": pay.reference or f"Pay-{pay.id}",
                "bill_number": pay.purchase.bill_number if pay.purchase and pay.purchase.bill_number else "-",
                "description": f"Payment via {pay.payment_method} ({pay.notes or pay.remarks or 'Paid'})",
                "credit": Decimal("0.00"),
                "debit": pay.amount,
                "due_date": None,
                "raw_obj": pay,
            })

        events.sort(key=lambda x: x["date"])

        running_balance = supplier.opening_balance or Decimal("0.00")
        ledger_rows = []
        today = timezone.localdate()
        total_credit_taken = Decimal("0.00")
        total_paid = Decimal("0.00")

        for ev in events:
            total_credit_taken += ev["credit"]
            total_paid += ev["debit"]
            running_balance += ev["credit"] - ev["debit"]
            ev_copy = dict(ev)
            ev_copy["running_balance"] = running_balance
            ledger_rows.append(ev_copy)

        remaining_payable = max(Decimal("0.00"), total_credit_taken - total_paid)
        overdue_amount = sum(
            (p.remaining_amount for p in purchases if p.due_date and p.due_date < today and p.remaining_amount > Decimal("0.00")),
            Decimal("0.00")
        )

        return {
            "supplier": supplier,
            "opening_balance": supplier.opening_balance or Decimal("0.00"),
            "total_credit_taken": total_credit_taken,
            "total_paid": total_paid,
            "remaining_payable": remaining_payable,
            "overdue_amount": overdue_amount,
            "ledger_rows": ledger_rows,
        }

    @classmethod
    def get_customers_dues(cls, company_id: int | None = None) -> list[dict[str, Any]]:
        """
        List all customers with outstanding credit balances and overdue amounts.
        """
        customers = Customer.objects.filter(is_active=True)
        if company_id:
            customers = customers.filter(company_id=company_id)

        today = timezone.localdate()
        dues_list = []

        for cust in customers:
            sales = cust.sales.filter(is_active=True)
            total_credit = sales.aggregate(s=Sum("total"))["s"] or Decimal("0.00")
            total_paid = Payment.objects.filter(
                customer=cust, status__iexact="Completed"
            ).aggregate(s=Sum("amount"))["s"] or Decimal("0.00")
            remaining = max(Decimal("0.00"), total_credit - total_paid)

            overdue = sum(
                (s.remaining_amount for s in sales if s.due_date and s.due_date < today and s.remaining_amount > Decimal("0.00")),
                Decimal("0.00")
            )

            dues_list.append({
                "customer": cust,
                "total_credit": total_credit,
                "total_paid": total_paid,
                "remaining_due": remaining,
                "overdue_amount": overdue,
                "invoice_count": sales.count(),
            })

        # Order by highest remaining due first
        dues_list.sort(key=lambda x: x["remaining_due"], reverse=True)
        return dues_list

    @classmethod
    def get_suppliers_dues(cls, company_id: int | None = None) -> list[dict[str, Any]]:
        """
        List all suppliers with outstanding payable credit balances and overdue amounts.
        """
        suppliers = Supplier.objects.filter(is_active=True)
        if company_id:
            suppliers = suppliers.filter(company_id=company_id)

        today = timezone.localdate()
        dues_list = []

        for sup in suppliers:
            purchases = sup.purchases.filter(is_active=True)
            total_credit = purchases.aggregate(s=Sum("total"))["s"] or Decimal("0.00")
            total_paid = Payment.objects.filter(
                supplier=sup, status__iexact="Completed"
            ).aggregate(s=Sum("amount"))["s"] or Decimal("0.00")
            remaining = max(Decimal("0.00"), total_credit - total_paid)

            overdue = sum(
                (p.remaining_amount for p in purchases if p.due_date and p.due_date < today and p.remaining_amount > Decimal("0.00")),
                Decimal("0.00")
            )

            dues_list.append({
                "supplier": sup,
                "total_credit": total_credit,
                "total_paid": total_paid,
                "remaining_payable": remaining,
                "overdue_amount": overdue,
                "bill_count": purchases.count(),
            })

        dues_list.sort(key=lambda x: x["remaining_payable"], reverse=True)
        return dues_list

    @classmethod
    @transaction.atomic
    def create_cheque(
        cls,
        cheque_type: str,
        cheque_number: str,
        bank_name: str,
        amount: Decimal,
        cheque_date: Any,
        customer_id: int | None = None,
        supplier_id: int | None = None,
        sale_id: int | None = None,
        purchase_id: int | None = None,
        notes: str = "",
        company_id: int | None = None,
        user: Any = None,
    ):
        """Create a new Cheque Given or Received record with validation and audit trail."""
        from apps.credit.models import Cheque
        amount = Decimal(str(amount))
        if amount <= Decimal("0.00"):
            raise ValidationError("Cheque amount must be greater than zero.")
        if not cheque_number or not str(cheque_number).strip():
            raise ValidationError("Cheque number is required.")
        if not bank_name or not str(bank_name).strip():
            raise ValidationError("Bank name is required.")

        cheque = Cheque.objects.create(
            company_id=company_id,
            cheque_type=cheque_type.upper().strip(),
            cheque_number=str(cheque_number).strip(),
            bank_name=str(bank_name).strip(),
            amount=amount,
            cheque_date=cheque_date,
            customer_id=customer_id,
            supplier_id=supplier_id,
            sale_id=sale_id,
            purchase_id=purchase_id,
            status=Cheque.STATUS_PENDING,
            notes=notes,
            created_by=user if getattr(user, "is_authenticated", False) else None,
        )

        cls._log_audit(
            user=user,
            action="Cheque Created",
            record_type="Cheque",
            record_id=cheque.id,
            description=f"Created {cheque.get_cheque_type_display()} #{cheque.cheque_number} for Rs. {cheque.amount} at {cheque.bank_name}",
            details={"cheque_number": cheque.cheque_number, "amount": str(cheque.amount), "date": str(cheque.cheque_date)},
        )
        return cheque

    @classmethod
    @transaction.atomic
    def update_cheque_status(
        cls,
        cheque_id: int,
        status: str,
        notes: str = "",
        user: Any = None,
    ):
        """Update cheque status (Pending, Cleared, Bounced, Cancelled) and record audit log."""
        from apps.credit.models import Cheque
        try:
            cheque = Cheque.objects.get(pk=cheque_id)
        except Cheque.DoesNotExist:
            raise NotFoundError(f"Cheque with ID {cheque_id} not found.")

        old_status = cheque.status
        status_clean = status.upper().strip()
        valid_statuses = [Cheque.STATUS_PENDING, Cheque.STATUS_CLEARED, Cheque.STATUS_BOUNCED, Cheque.STATUS_CANCELLED]
        if status_clean not in valid_statuses:
            raise ValidationError(f"Invalid cheque status: {status}. Must be one of {valid_statuses}")

        cheque.status = status_clean
        if notes:
            ts = timezone.now().strftime("%Y-%m-%d %H:%M")
            cheque.notes = f"{cheque.notes}\n[{ts}] Status changed from {old_status} to {status_clean}: {notes}".strip()
        cheque.save(update_fields=["status", "notes", "updated_at"])

        cls._log_audit(
            user=user,
            action="Cheque Status Changed",
            record_type="Cheque",
            record_id=cheque.id,
            description=f"Cheque #{cheque.cheque_number} status changed from {old_status} to {status_clean}",
            details={"old_status": old_status, "new_status": status_clean},
        )
        return cheque

    @classmethod
    def get_cheques_summary(cls, company_id: int | None = None) -> dict[str, Any]:
        """Aggregated summary of cheques given, received, pending, cleared, bounced, due today, overdue."""
        from apps.credit.models import Cheque
        today = timezone.localdate()

        qs = Cheque.objects.all()
        if company_id:
            qs = qs.filter(company_id=company_id)

        pending = qs.filter(status=Cheque.STATUS_PENDING)
        cleared = qs.filter(status=Cheque.STATUS_CLEARED)
        bounced = qs.filter(status=Cheque.STATUS_BOUNCED)

        due_today = pending.filter(cheque_date=today)
        overdue = pending.filter(cheque_date__lt=today)
        due_soon = [c for c in pending if 0 < c.days_until_due <= 7]

        return {
            "total_count": qs.count(),
            "total_amount": qs.aggregate(s=Sum("amount"))["s"] or Decimal("0.00"),
            "pending_count": pending.count(),
            "pending_amount": pending.aggregate(s=Sum("amount"))["s"] or Decimal("0.00"),
            "cleared_count": cleared.count(),
            "cleared_amount": cleared.aggregate(s=Sum("amount"))["s"] or Decimal("0.00"),
            "bounced_count": bounced.count(),
            "bounced_amount": bounced.aggregate(s=Sum("amount"))["s"] or Decimal("0.00"),
            "due_today_count": due_today.count(),
            "due_today_amount": due_today.aggregate(s=Sum("amount"))["s"] or Decimal("0.00"),
            "overdue_count": overdue.count(),
            "overdue_amount": overdue.aggregate(s=Sum("amount"))["s"] or Decimal("0.00"),
            "due_soon_count": len(due_soon),
            "given_count": qs.filter(cheque_type=Cheque.TYPE_GIVEN).count(),
            "received_count": qs.filter(cheque_type=Cheque.TYPE_RECEIVED).count(),
            "total_given": qs.filter(cheque_type=Cheque.TYPE_GIVEN).aggregate(s=Sum("amount"))["s"] or Decimal("0.00"),
            "total_received": qs.filter(cheque_type=Cheque.TYPE_RECEIVED).aggregate(s=Sum("amount"))["s"] or Decimal("0.00"),
        }
