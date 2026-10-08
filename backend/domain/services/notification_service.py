"""
NotificationService -- Central Business Notification, Monitoring, and Alerting Engine.

Handles:
- Stock Alerts (Low Stock, Critical Stock, Out of Stock, Stock Received, Stock Restored)
- Payment Due Reminders (7d, 3d, 2d, 1d, today, overdue)
- Cheque Reminders (Given, Received, 7d, 3d, 2d, 1d, today, overdue)
- Receivables & Payables overdue notifications
- In-App Notification Center & Unread tracking
- Dismissible In-App Popups for urgent alerts
- Optional SMS dispatch integration via SMSService
- Strict deduplication preventing repeated alerts for identical state
- Activity / Audit logging
"""
from datetime import datetime, date
from decimal import Decimal
import logging
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.db.models import F, Q, Sum
from django.utils import timezone

from apps.audit.models import AuditLog, Notification, NotificationPreference
from apps.inventory.models import Product, StockMovement
from apps.sales.models import Sale, Customer, Payment
from apps.purchases.models import Purchase, Supplier
from apps.credit.models import Cheque
from domain.services.sms_service import SMSService

logger = logging.getLogger(__name__)


class NotificationService:
    """Central business notification and monitoring engine."""

    # -------------------------------------------------------------------------
    # Core Dispatch & Deduplication
    # -------------------------------------------------------------------------

    @classmethod
    def dispatch_notification(
        cls,
        user: Any,
        title: str,
        message: str,
        notification_type: str,
        priority: str = Notification.PRIORITY_NORMAL,
        module: str = "general",
        record_id: Optional[int] = None,
        company: Any = None,
        link: str = "",
        dedup_key: str = "",
        is_popup: bool = False,
        sms_text: Optional[str] = None,
    ) -> Optional[Notification]:
        """
        Create a notification with user preference validation, deduplication,
        optional popup trigger, and optional SMS dispatch.
        """
        if not user or not getattr(user, "is_authenticated", False):
            # Target company admin/manager if user is not directly specified
            from apps.accounts.models import User
            admins = User.objects.filter(is_active=True, role__name__in=["admin", "manager"])
            if company:
                admins = admins.filter(active_company=company)
            user = admins.first()
            if not user:
                return None

        # Check notification preference
        pref, _ = NotificationPreference.objects.get_or_create(user=user)
        type_field_map = {
            "low_stock": "notify_low_stock",
            "critical_stock": "notify_critical_stock",
            "out_of_stock": "notify_out_of_stock",
            "stock_received": "notify_stock_received",
            "stock_restored": "notify_stock_restored",
            "payment_due": "notify_payment_due",
            "payment_overdue": "notify_payment_overdue",
            "cheque_due_soon": "notify_cheque_due_soon",
            "cheque_due_today": "notify_cheque_due_today",
            "cheque_overdue": "notify_cheque_overdue",
            "receivable_due": "notify_receivable_due",
            "receivable_overdue": "notify_receivable_overdue",
            "payable_due": "notify_payable_due",
            "payable_overdue": "notify_payable_overdue",
        }
        pref_field = type_field_map.get(notification_type)
        if pref_field and not getattr(pref, pref_field, True):
            # User opted out of this alert category
            return None

        # Deduplication check
        if dedup_key:
            existing = Notification.objects.filter(
                user=user,
                dedup_key=dedup_key,
            ).first()
            if existing:
                return existing

        # Popup decision: Urgent/Critical alerts or high priority items
        should_popup = is_popup or (priority in [Notification.PRIORITY_CRITICAL, Notification.PRIORITY_HIGH])
        if not pref.popup_enabled:
            should_popup = False

        notif = Notification.objects.create(
            user=user,
            company=company or getattr(user, "active_company", None),
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            module=module,
            record_id=record_id,
            dedup_key=dedup_key,
            link=link,
            is_popup=should_popup,
            is_read=False,
        )

        # Audit log for alert creation
        try:
            AuditLog.objects.create(
                user=user,
                module=module.capitalize(),
                action=f"{notification_type.replace('_', ' ').title()} Created",
                record_type="Notification",
                record_id=notif.id,
                description=f"{title}: {message[:60]}...",
                success=True,
            )
        except Exception:
            pass

        # Optional SMS Dispatch
        if pref.sms_enabled:
            sms_body = sms_text or f"{title}: {message}"
            SMSService.send_alert_sms(
                user=user,
                notification_type=notification_type,
                message=sms_body,
                dedup_key=f"sms:{dedup_key}" if dedup_key else "",
            )

        return notif

    # -------------------------------------------------------------------------
    # 1. Stock Alerts Monitoring
    # -------------------------------------------------------------------------

    @classmethod
    def check_stock_alerts(cls, company_id: Optional[int] = None, user: Any = None) -> Dict[str, int]:
        """
        Scan inventory products and generate Low, Critical, and Out of Stock alerts.
        """
        products = Product.objects.filter(is_active=True)
        if company_id:
            products = products.filter(company_id=company_id)

        stats = {"out_of_stock": 0, "critical_stock": 0, "low_stock": 0}
        today_str = timezone.localdate().isoformat()

        for product in products:
            status = product.stock_status
            if status == "out_of_stock":
                stats["out_of_stock"] += 1
                cls.dispatch_notification(
                    user=user,
                    title="🚨 Out of Stock",
                    message=f"{product.name} ({product.sku}) is currently out of stock!",
                    notification_type="out_of_stock",
                    priority=Notification.PRIORITY_CRITICAL,
                    module="inventory",
                    record_id=product.id,
                    company=product.company,
                    link=f"/products/?search={product.sku}",
                    dedup_key=f"stock_out:{product.id}:{today_str}",
                    is_popup=True,
                    sms_text=f"ALERT: {product.name} is out of stock. Please restock. - BizFlow",
                )
            elif status == "critical":
                stats["critical_stock"] += 1
                crit = product.effective_critical_stock
                cls.dispatch_notification(
                    user=user,
                    title="⚠️ Critical Low Stock Alert",
                    message=f"{product.name} is at critical stock level! Current Stock: {product.current_stock} (Critical: {crit}, Min: {product.minimum_stock}).",
                    notification_type="critical_stock",
                    priority=Notification.PRIORITY_HIGH,
                    module="inventory",
                    record_id=product.id,
                    company=product.company,
                    link=f"/products/?search={product.sku}",
                    dedup_key=f"stock_crit:{product.id}:{product.current_stock}:{today_str}",
                    is_popup=True,
                    sms_text=f"ALERT: {product.name} critical low stock. Current: {product.current_stock}. Min: {product.minimum_stock}.",
                )
            elif status == "low":
                stats["low_stock"] += 1
                cls.dispatch_notification(
                    user=user,
                    title="⚠️ Low Stock Alert",
                    message=f"{product.name} is running low. Current Stock: {product.current_stock}. Minimum Required: {product.minimum_stock}.",
                    notification_type="low_stock",
                    priority=Notification.PRIORITY_NORMAL,
                    module="inventory",
                    record_id=product.id,
                    company=product.company,
                    link=f"/products/?search={product.sku}",
                    dedup_key=f"stock_low:{product.id}:{product.current_stock}:{today_str}",
                    is_popup=False,
                    sms_text=f"ALERT: {product.name} stock is low. Current stock: {product.current_stock}. Minimum: {product.minimum_stock}.",
                )

        return stats

    @classmethod
    def notify_stock_received(
        cls,
        product: Product,
        quantity: int,
        previous_stock: int,
        new_stock: int,
        movement_id: Optional[int] = None,
        user: Any = None,
    ) -> None:
        """
        Called when stock is received (purchase or inward adjustment).
        Triggers:
        - Stock Received notification
        - Stock Restored notification if previous_stock == 0 and new_stock > 0
        """
        today_str = timezone.localdate().isoformat()
        mid = movement_id or f"{previous_stock}-{new_stock}"

        # 1. Stock Received
        cls.dispatch_notification(
            user=user,
            title="📦 Stock Received",
            message=f"{quantity} units of {product.name} have been added to inventory. Current Stock: {new_stock}.",
            notification_type="stock_received",
            priority=Notification.PRIORITY_INFO,
            module="inventory",
            record_id=product.id,
            company=product.company,
            link=f"/products/?search={product.sku}",
            dedup_key=f"stock_received:{product.id}:{mid}:{today_str}",
            is_popup=False,
            sms_text=f"UPDATE: {quantity} units of {product.name} received. Current stock: {new_stock}.",
        )

        # 2. Stock Restored (Restocked from zero)
        if previous_stock <= 0 and new_stock > 0:
            cls.dispatch_notification(
                user=user,
                title="✅ Stock Restored",
                message=f"{product.name} was out of stock and has now been restocked. New Stock: {new_stock}.",
                notification_type="stock_restored",
                priority=Notification.PRIORITY_INFO,
                module="inventory",
                record_id=product.id,
                company=product.company,
                link=f"/products/?search={product.sku}",
                dedup_key=f"stock_restored:{product.id}:{mid}:{today_str}",
                is_popup=False,
                sms_text=f"UPDATE: {product.name} is back in stock. Current stock: {new_stock}.",
            )

    # -------------------------------------------------------------------------
    # 2. Payment Due Reminders
    # -------------------------------------------------------------------------

    @classmethod
    def check_payment_due_reminders(cls, company_id: Optional[int] = None, user: Any = None) -> Dict[str, int]:
        """
        Scan customer sales (Receivables) and supplier purchases (Payables) with outstanding balances and due dates.
        Notifies at: 7 days, 3 days, 2 days, 1 day, due today, overdue.
        """
        today = timezone.localdate()
        today_str = today.isoformat()
        max_due_date = today + timezone.timedelta(days=7)
        stats = {"sales_due": 0, "sales_overdue": 0, "purchases_due": 0, "purchases_overdue": 0}

        # 1. Sales Receivables
        sales = Sale.objects.filter(
            is_active=True,
            due_date__isnull=False,
            due_date__lte=max_due_date,
        ).exclude(
            payment_status=Sale.STATUS_PAID,
        ).select_related("customer", "company").prefetch_related("payments")
        if company_id:
            sales = sales.filter(company_id=company_id)

        for sale in sales:
            rem = sale.remaining_amount
            if rem <= Decimal("0.00"):
                continue

            days = (sale.due_date - today).days
            cust_name = sale.customer.name if sale.customer else "Customer"

            if days in (7, 3, 2, 1, 0) or days < 0:
                if days < 0:
                    stats["sales_overdue"] += 1
                    title = "⚠️ Receivable Payment Overdue"
                    msg = f"Payment of Rs. {rem:,.2f} for Invoice #{sale.invoice_number} from {cust_name} is overdue by {abs(days)} days."
                    priority = Notification.PRIORITY_CRITICAL
                    notif_type = "receivable_overdue"
                    is_popup = True
                    sms_text = f"ALERT: Overdue payment of Rs.{rem:,.2f} for Invoice #{sale.invoice_number} ({cust_name})."
                elif days == 0:
                    stats["sales_due"] += 1
                    title = "🔔 Receivable Due Today"
                    msg = f"Payment of Rs. {rem:,.2f} for Invoice #{sale.invoice_number} from {cust_name} is due today."
                    priority = Notification.PRIORITY_CRITICAL
                    notif_type = "receivable_due"
                    is_popup = True
                    sms_text = f"REMINDER: Payment of Rs.{rem:,.2f} from {cust_name} is due today."
                elif days == 1:
                    stats["sales_due"] += 1
                    title = "💳 Receivable Due Tomorrow"
                    msg = f"Payment of Rs. {rem:,.2f} for Invoice #{sale.invoice_number} from {cust_name} is due tomorrow."
                    priority = Notification.PRIORITY_HIGH
                    notif_type = "payment_due"
                    is_popup = False
                    sms_text = f"REMINDER: Payment of Rs.{rem:,.2f} from {cust_name} is due tomorrow."
                else:
                    stats["sales_due"] += 1
                    title = f"💳 Receivable Due in {days} Days"
                    msg = f"Payment of Rs. {rem:,.2f} for Invoice #{sale.invoice_number} from {cust_name} is due in {days} days."
                    priority = Notification.PRIORITY_NORMAL
                    notif_type = "payment_due"
                    is_popup = False
                    sms_text = f"REMINDER: Payment of Rs.{rem:,.2f} is due in {days} days."

                cls.dispatch_notification(
                    user=user,
                    title=title,
                    message=msg,
                    notification_type=notif_type,
                    priority=priority,
                    module="sales",
                    record_id=sale.id,
                    company=sale.company,
                    link=f"/sales/{sale.id}/",
                    dedup_key=f"pay_sale:{sale.id}:{days}:{today_str}",
                    is_popup=is_popup,
                    sms_text=sms_text,
                )

        # 2. Purchases Payables
        purchases = Purchase.objects.filter(
            is_active=True,
            due_date__isnull=False,
            due_date__lte=max_due_date,
        ).exclude(
            payment_status=Purchase.STATUS_PAID,
        ).select_related("supplier", "company").prefetch_related("payments")
        if company_id:
            purchases = purchases.filter(company_id=company_id)

        for purchase in purchases:
            rem = purchase.remaining_amount
            if rem <= Decimal("0.00"):
                continue

            days = (purchase.due_date - today).days
            supp_name = purchase.supplier.name if purchase.supplier else "Supplier"

            if days in (7, 3, 2, 1, 0) or days < 0:
                if days < 0:
                    stats["purchases_overdue"] += 1
                    title = "⚠️ Payable Payment Overdue"
                    msg = f"Payment of Rs. {rem:,.2f} for Bill #{purchase.purchase_number} to {supp_name} is overdue by {abs(days)} days."
                    priority = Notification.PRIORITY_CRITICAL
                    notif_type = "payable_overdue"
                    is_popup = True
                    sms_text = f"ALERT: Payment of Rs.{rem:,.2f} to {supp_name} is overdue."
                elif days == 0:
                    stats["purchases_due"] += 1
                    title = "💸 Payable Due Today"
                    msg = f"Payment of Rs. {rem:,.2f} for Bill #{purchase.purchase_number} to {supp_name} is due today."
                    priority = Notification.PRIORITY_CRITICAL
                    notif_type = "payable_due"
                    is_popup = True
                    sms_text = f"REMINDER: Payment of Rs.{rem:,.2f} to {supp_name} is due today."
                elif days == 1:
                    stats["purchases_due"] += 1
                    title = "💸 Payable Due Tomorrow"
                    msg = f"Payment of Rs. {rem:,.2f} for Bill #{purchase.purchase_number} to {supp_name} is due tomorrow."
                    priority = Notification.PRIORITY_HIGH
                    notif_type = "payment_due"
                    is_popup = False
                    sms_text = f"REMINDER: Payment of Rs.{rem:,.2f} to {supp_name} is due tomorrow."
                else:
                    stats["purchases_due"] += 1
                    title = f"💸 Payable Due in {days} Days"
                    msg = f"Payment of Rs. {rem:,.2f} for Bill #{purchase.purchase_number} to {supp_name} is due in {days} days."
                    priority = Notification.PRIORITY_NORMAL
                    notif_type = "payment_due"
                    is_popup = False
                    sms_text = f"REMINDER: Payment of Rs.{rem:,.2f} to {supp_name} is due in {days} days."

                cls.dispatch_notification(
                    user=user,
                    title=title,
                    message=msg,
                    notification_type=notif_type,
                    priority=priority,
                    module="purchases",
                    record_id=purchase.id,
                    company=purchase.company,
                    link=f"/purchases/{purchase.id}/",
                    dedup_key=f"pay_purch:{purchase.id}:{days}:{today_str}",
                    is_popup=is_popup,
                    sms_text=sms_text,
                )

        return stats

    # -------------------------------------------------------------------------
    # 3. Cheque Reminders
    # -------------------------------------------------------------------------

    @classmethod
    def check_cheque_reminders(cls, company_id: Optional[int] = None, user: Any = None) -> Dict[str, int]:
        """
        Scan pending cheques (Given & Received) and generate reminders.
        Reminders at: 7 days, 3 days, 2 days, 1 day, due today, overdue.
        """
        today = timezone.localdate()
        today_str = today.isoformat()
        stats = {"cheques_due": 0, "cheques_overdue": 0}

        cheques = Cheque.objects.filter(
            status=Cheque.STATUS_PENDING,
            cheque_date__lte=today + timezone.timedelta(days=7),
        ).select_related("customer", "supplier", "company")
        if company_id:
            cheques = cheques.filter(company_id=company_id)

        for cheque in cheques:
            days = (cheque.cheque_date - today).days
            direction = "to " + cheque.supplier.name if cheque.cheque_type == Cheque.TYPE_GIVEN and cheque.supplier else (
                "from " + cheque.customer.name if cheque.customer else ""
            )

            if days in (7, 3, 2, 1, 0) or days < 0:
                if days < 0:
                    stats["cheques_overdue"] += 1
                    title = f"⚠️ Cheque Overdue"
                    msg = f"Cheque No. {cheque.cheque_number} ({cheque.bank_name}) for Rs. {cheque.amount:,.2f} {direction} was due on {cheque.cheque_date} ({abs(days)} days ago)."
                    priority = Notification.PRIORITY_CRITICAL
                    notif_type = "cheque_overdue"
                    is_popup = True
                    sms_text = f"ALERT: Cheque No. {cheque.cheque_number} for Rs.{cheque.amount:,.2f} is overdue."
                elif days == 0:
                    stats["cheques_due"] += 1
                    title = "🚨 Cheque Due Today"
                    msg = f"Cheque No. {cheque.cheque_number} ({cheque.bank_name}) for Rs. {cheque.amount:,.2f} {direction} is due today."
                    priority = Notification.PRIORITY_CRITICAL
                    notif_type = "cheque_due_today"
                    is_popup = True
                    sms_text = f"REMINDER: Cheque No. {cheque.cheque_number} for Rs.{cheque.amount:,.2f} is due today."
                elif days == 1:
                    stats["cheques_due"] += 1
                    title = "🧾 Cheque Due Tomorrow"
                    msg = f"Cheque No. {cheque.cheque_number} ({cheque.bank_name}) for Rs. {cheque.amount:,.2f} {direction} is due tomorrow."
                    priority = Notification.PRIORITY_HIGH
                    notif_type = "cheque_due_soon"
                    is_popup = False
                    sms_text = f"REMINDER: Cheque No. {cheque.cheque_number} for Rs.{cheque.amount:,.2f} is due tomorrow."
                else:
                    stats["cheques_due"] += 1
                    title = f"🧾 Cheque Due in {days} Days"
                    msg = f"Cheque No. {cheque.cheque_number} ({cheque.bank_name}) for Rs. {cheque.amount:,.2f} {direction} is due in {days} days."
                    priority = Notification.PRIORITY_NORMAL
                    notif_type = "cheque_due_soon"
                    is_popup = False
                    sms_text = f"REMINDER: Cheque No. {cheque.cheque_number} for Rs.{cheque.amount:,.2f} is due in {days} days."

                cls.dispatch_notification(
                    user=user,
                    title=title,
                    message=msg,
                    notification_type=notif_type,
                    priority=priority,
                    module="cheques",
                    record_id=cheque.id,
                    company=cheque.company,
                    link=f"/credit/cheques/",
                    dedup_key=f"cheque_rem:{cheque.id}:{days}:{today_str}",
                    is_popup=is_popup,
                    sms_text=sms_text,
                )

        return stats

    # -------------------------------------------------------------------------
    # 4. Master Monitoring Runner & Dashboard Summary
    # -------------------------------------------------------------------------

    @classmethod
    def run_all_monitors(cls, company_id: Optional[int] = None, user: Any = None) -> Dict[str, Any]:
        """
        Executes all business health monitors safely without throwing uncaught exceptions.
        """
        results = {}
        try:
            results["stock"] = cls.check_stock_alerts(company_id=company_id, user=user)
        except Exception as exc:
            logger.error("Stock monitor failure: %s", exc)
            results["stock"] = {}

        try:
            results["payments"] = cls.check_payment_due_reminders(company_id=company_id, user=user)
        except Exception as exc:
            logger.error("Payment monitor failure: %s", exc)
            results["payments"] = {}

        try:
            results["cheques"] = cls.check_cheque_reminders(company_id=company_id, user=user)
        except Exception as exc:
            logger.error("Cheque monitor failure: %s", exc)
            results["cheques"] = {}

        return results

    @classmethod
    def get_dashboard_business_alerts(cls, company_id: Optional[int] = None) -> Dict[str, int]:
        """
        Calculate KPI counts for the Dashboard 'Business Alerts' card section:
        - Out of Stock
        - Low Stock
        - Stock Received (last 7 days)
        - Payments Due (due <= 7 days or overdue)
        - Cheques Due (due <= 7 days or overdue)
        - Receivables Overdue
        - Payables Overdue
        """
        today = timezone.localdate()
        from datetime import timedelta

        # Stock
        products = Product.objects.filter(is_active=True)
        if company_id:
            products = products.filter(company_id=company_id)

        out_of_stock_cnt = products.filter(current_stock=0).count()
        low_stock_cnt = products.filter(current_stock__gt=0, current_stock__lte=F("minimum_stock")).count()

        # Stock received recently
        seven_days_ago = timezone.now() - timedelta(days=7)
        movements = StockMovement.objects.filter(movement_type=StockMovement.MOVEMENT_IN, created_at__gte=seven_days_ago)
        if company_id:
            movements = movements.filter(product__company_id=company_id)
        stock_received_cnt = movements.count()

        # Receivables (Sales)
        sales = Sale.objects.filter(is_active=True, due_date__isnull=False)
        if company_id:
            sales = sales.filter(company_id=company_id)
        sales_due_cnt = 0
        receivables_overdue_cnt = 0
        for s in sales:
            if s.remaining_amount > Decimal("0.00"):
                diff = (s.due_date - today).days
                if diff < 0:
                    receivables_overdue_cnt += 1
                elif diff <= 7:
                    sales_due_cnt += 1

        # Payables (Purchases)
        purchases = Purchase.objects.filter(is_active=True, due_date__isnull=False)
        if company_id:
            purchases = purchases.filter(company_id=company_id)
        purchases_due_cnt = 0
        payables_overdue_cnt = 0
        for p in purchases:
            if p.remaining_amount > Decimal("0.00"):
                diff = (p.due_date - today).days
                if diff < 0:
                    payables_overdue_cnt += 1
                elif diff <= 7:
                    purchases_due_cnt += 1

        payments_due_cnt = sales_due_cnt + purchases_due_cnt

        # Cheques
        cheques = Cheque.objects.filter(status=Cheque.STATUS_PENDING)
        if company_id:
            cheques = cheques.filter(company_id=company_id)
        cheques_due_cnt = 0
        for c in cheques:
            diff = (c.cheque_date - today).days
            if diff <= 7:  # includes overdue and upcoming 7 days
                cheques_due_cnt += 1

        return {
            "out_of_stock": out_of_stock_cnt,
            "low_stock": low_stock_cnt,
            "stock_received": stock_received_cnt,
            "payments_due": payments_due_cnt,
            "cheques_due": cheques_due_cnt,
            "receivables_overdue": receivables_overdue_cnt,
            "payables_overdue": payables_overdue_cnt,
        }

    # -------------------------------------------------------------------------
    # 5. Popups & Unread Management
    # -------------------------------------------------------------------------

    @classmethod
    def get_unread_count(cls, user: Any) -> int:
        if not user or not getattr(user, "is_authenticated", False):
            return 0
        return Notification.objects.filter(user=user, is_read=False).count()

    @classmethod
    def get_active_popups(cls, user: Any, limit: int = 3) -> List[Notification]:
        """Fetch active popups for immediate display to user."""
        if not user or not getattr(user, "is_authenticated", False):
            return []
        pref, _ = NotificationPreference.objects.get_or_create(user=user)
        if not pref.popup_enabled:
            return []
        return list(
            Notification.objects.filter(
                user=user,
                is_popup=True,
                popup_dismissed=False,
                is_read=False,
            ).order_by("-created_at")[:limit]
        )

    @classmethod
    def dismiss_popup(cls, user: Any, notification_id: int) -> bool:
        """Dismiss popup without necessarily marking notification as read."""
        if not user or not getattr(user, "is_authenticated", False):
            return False
        updated = Notification.objects.filter(
            id=notification_id,
            user=user,
        ).update(popup_dismissed=True)
        return updated > 0
