"""
Dashboard and home views for BizFlow web application.
"""
from datetime import date, datetime
from decimal import Decimal
import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.accounts.permissions import login_required_custom, admin_required
from apps.inventory.models import Product
from apps.sales.models import Sale, Customer
from apps.purchases.models import Purchase, Supplier
from apps.accounting.models import Expense
from apps.audit.models import Notification, NotificationPreference
from domain.services.stock_service import StockService
from domain.services.credit_service import CreditService
from domain.services.notification_service import NotificationService
from domain.services.sms_service import SMSService
from services.nepali_date import NepaliDateService


def home(request: HttpRequest) -> HttpResponse:
    """Public landing page or redirect to dashboard if authenticated."""
    if request.user.is_authenticated:
        return redirect("dashboard:index")
    return render(request, "landing.html")


@login_required_custom
def index(request: HttpRequest) -> HttpResponse:
    """Main business dashboard with KPI metrics, alerts, and recent transactions."""
    if getattr(request.user, "is_customer", False):
        return redirect("inventory:product_list")

    today = timezone.localdate()
    company_id = getattr(request.user.active_company, "id", None) if getattr(request.user, "active_company", None) else None

    # Base querysets scoped by active company if present
    sales_qs = Sale.objects.filter(is_active=True)
    purchases_qs = Purchase.objects.filter(is_active=True)
    products_qs = Product.objects.filter(is_active=True)
    expenses_qs = Expense.objects.all()
    customers_qs = Customer.objects.filter(is_active=True)
    suppliers_qs = Supplier.objects.filter(is_active=True)

    if company_id:
        sales_qs = sales_qs.filter(company_id=company_id)
        purchases_qs = purchases_qs.filter(company_id=company_id)
        products_qs = products_qs.filter(company_id=company_id)
        expenses_qs = expenses_qs.filter(company_id=company_id)
        customers_qs = customers_qs.filter(company_id=company_id)
        suppliers_qs = suppliers_qs.filter(company_id=company_id)

    # Metrics
    todays_sales = sales_qs.filter(sale_date__date=today).count()
    todays_purchases = purchases_qs.filter(purchase_date__date=today).count()
    total_products = products_qs.count()
    low_stock = StockService.low_stock_products(company_id=company_id).count()
    out_of_stock = StockService.out_of_stock_products(company_id=company_id).count()
    customers_count = customers_qs.count()
    suppliers_count = suppliers_qs.count()
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False).count()

    # Financial sums
    total_sales_amount = sales_qs.aggregate(t=Sum("total"))["t"] or Decimal("0.00")
    total_purchases_amount = purchases_qs.aggregate(t=Sum("total"))["t"] or Decimal("0.00")
    total_expenses_amount = expenses_qs.aggregate(t=Sum("amount"))["t"] or Decimal("0.00")
    net_profit = total_sales_amount - total_purchases_amount - total_expenses_amount

    # Receivables & Payables summary
    credit_summary = CreditService.get_credit_summary(company_id=company_id)

    # Central Business Monitoring & Alerts with 60-second cooldown throttle
    from django.core.cache import cache
    cache_key = f"monitors_run_{company_id or 'global'}_{request.user.id}"
    if not cache.get(cache_key):
        NotificationService.run_all_monitors(company_id=company_id, user=request.user)
        cache.set(cache_key, True, timeout=60)

    business_alerts = NotificationService.get_dashboard_business_alerts(company_id=company_id)
    popups = NotificationService.get_active_popups(request.user)

    # Recent activity
    recent_sales = sales_qs.select_related("customer").order_by("-sale_date")[:5]
    recent_purchases = purchases_qs.select_related("supplier").order_by("-purchase_date")[:5]

    context = {
        "todays_sales": todays_sales,
        "todays_purchases": todays_purchases,
        "total_products": total_products,
        "product_count": total_products,
        "low_stock": low_stock,
        "low_stock_count": low_stock,
        "out_of_stock": out_of_stock,
        "out_of_stock_count": out_of_stock,
        "customers": customers_count,
        "suppliers": suppliers_count,
        "notifications": unread_notifications,
        "total_sales": total_sales_amount,
        "total_sales_amount": total_sales_amount,
        "total_purchases": total_purchases_amount,
        "total_purchases_amount": total_purchases_amount,
        "total_expenses": total_expenses_amount,
        "total_expenses_amount": total_expenses_amount,
        "net_profit": net_profit,
        "credit_summary": credit_summary,
        "business_alerts": business_alerts,
        "popups": popups,
        "recent_sales": recent_sales,
        "recent_purchases": recent_purchases,
        "current_user": request.user,
    }
    return render(request, "dashboard/index.html", context)


@admin_required
def admin_dashboard(request: HttpRequest) -> HttpResponse:
    """Administrator overview with system stats."""
    return index(request)


def convert_date(request: HttpRequest) -> JsonResponse:
    """API endpoint to convert dates between Gregorian (AD) and Bikram Sambat (BS)."""
    date_str = ""
    mode = "ad_to_bs"

    if request.method == "POST":
        try:
            body = json.loads(request.body.decode("utf-8")) if request.body else {}
            date_str = (body.get("date") or "").strip()
            mode = (body.get("mode") or body.get("direction") or "ad_to_bs").strip().lower()
        except Exception:
            date_str = request.POST.get("date", "").strip()
            mode = (request.POST.get("mode") or request.POST.get("direction") or "ad_to_bs").strip().lower()
    else:
        date_str = request.GET.get("date", "").strip()
        mode = (request.GET.get("mode") or request.GET.get("direction") or "ad_to_bs").strip().lower()

    if not date_str:
        today_ad = timezone.localdate()
        today_bs = str(NepaliDateService.ad_to_bs(today_ad))
        parts = [int(p) for p in today_bs.split("-") if p.isdigit()]
        return JsonResponse({
            "success": True,
            "ad_date": today_ad.isoformat(),
            "bs_date": today_bs,
            "bs_year": parts[0] if parts else 2083,
            "bs_month": parts[1] if len(parts) > 1 else 1,
            "bs_day": parts[2] if len(parts) > 2 else 1,
            "formatted_ad": today_ad.strftime("%d %b %Y"),
            "formatted_bs": today_bs,
        })

    try:
        if mode == "bs_to_ad":
            parts = [int(p) for p in date_str.replace("/", "-").split("-") if p.isdigit()]
            if len(parts) == 3:
                ad_date = NepaliDateService.bs_to_ad(parts[0], parts[1], parts[2])
                if ad_date:
                    bs_date = str(NepaliDateService.ad_to_bs(ad_date))
                    return JsonResponse({
                        "success": True,
                        "ad_date": ad_date.isoformat(),
                        "bs_date": bs_date,
                        "bs_year": parts[0],
                        "bs_month": parts[1],
                        "bs_day": parts[2],
                        "formatted_ad": ad_date.strftime("%d %b %Y"),
                        "formatted_bs": bs_date,
                    })
        else:
            parts = [int(p) for p in date_str.replace("/", "-").split("-") if p.isdigit()]
            if len(parts) == 3:
                ad_date = date(parts[0], parts[1], parts[2])
                bs_date = str(NepaliDateService.ad_to_bs(ad_date))
                bs_parts = [int(p) for p in bs_date.split("-") if p.isdigit()]
                return JsonResponse({
                    "success": True,
                    "ad_date": ad_date.isoformat(),
                    "bs_date": bs_date,
                    "bs_year": bs_parts[0] if bs_parts else 2083,
                    "bs_month": bs_parts[1] if len(bs_parts) > 1 else 1,
                    "bs_day": bs_parts[2] if len(bs_parts) > 2 else 1,
                    "formatted_ad": ad_date.strftime("%d %b %Y"),
                    "formatted_bs": bs_date,
                })
    except Exception as exc:
        return JsonResponse({"success": False, "error": str(exc)}, status=400)

    return JsonResponse({"success": False, "error": "Invalid date input"}, status=400)


@login_required_custom
def notifications_view(request: HttpRequest) -> HttpResponse:
    """Display user notifications with category filtering and read tracking."""
    tab = request.GET.get("tab", "all").lower().strip()
    notifs = Notification.objects.filter(user=request.user)

    if tab == "unread":
        notifs = notifs.filter(is_read=False)
    elif tab == "stock":
        notifs = notifs.filter(module="inventory")
    elif tab == "cheques":
        notifs = notifs.filter(module="cheques")
    elif tab == "payments":
        notifs = notifs.filter(module__in=["sales", "purchases", "credit"])
    elif tab == "overdue":
        notifs = notifs.filter(
            Q(notification_type__icontains="overdue") | Q(priority=Notification.PRIORITY_CRITICAL)
        )

    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    return render(
        request,
        "dashboard/notifications.html",
        {
            "notifications": notifs.order_by("-created_at"),
            "current_tab": tab,
            "unread_count": unread_count,
        },
    )


@login_required_custom
@require_POST
def mark_notification_read(request: HttpRequest, notification_id: int) -> JsonResponse:
    """Mark a notification as read."""
    notif = get_object_or_404(Notification, id=notification_id, user=request.user)
    notif.is_read = True
    notif.save(update_fields=["is_read"])
    return JsonResponse({"success": True})


@login_required_custom
@require_POST
def mark_all_notifications_read(request: HttpRequest) -> JsonResponse:
    """Mark all unread notifications for current user as read."""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    messages.success(request, "All notifications marked as read.")
    return redirect("dashboard:notifications")


@login_required_custom
@require_POST
def dismiss_popup(request: HttpRequest, notification_id: int) -> JsonResponse:
    """Dismiss in-app popup for current user."""
    NotificationService.dismiss_popup(user=request.user, notification_id=notification_id)
    return JsonResponse({"success": True})


@login_required_custom
def unread_count_api(request: HttpRequest) -> JsonResponse:
    """API returning live unread count and latest unread notifications for bell popup."""
    count = NotificationService.get_unread_count(request.user)
    recent = Notification.objects.filter(user=request.user, is_read=False).order_by("-created_at")[:5]
    items = [
        {
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "priority": n.priority,
            "badge_class": n.badge_class,
            "link": n.link or "/dashboard/notifications/",
            "created_at": n.created_at.strftime("%b %d, %H:%M"),
        }
        for n in recent
    ]
    return JsonResponse({"count": count, "items": items})


@login_required_custom
def notification_settings_view(request: HttpRequest) -> HttpResponse:
    """Manage user notification preferences and optional SMS settings."""
    pref, _ = NotificationPreference.objects.get_or_create(user=request.user)

    if request.method == "POST":
        action = request.POST.get("action", "save")

        if action == "test_sms":
            # Test SMS Dispatch
            phone = request.POST.get("sms_phone_number", "").strip() or pref.sms_phone_number
            if not phone:
                messages.error(request, "Please enter a valid phone number for SMS test.")
            else:
                res = SMSService.send_alert_sms(
                    user=request.user,
                    notification_type="general",
                    message="[TEST] BizFlow SMS Alert System is configured and working! - BizFlow",
                    force_phone=phone,
                )
                if res.get("sent"):
                    messages.success(request, f"Test SMS successfully dispatched to {phone}!")
                else:
                    messages.warning(request, f"SMS test failed: {res.get('error') or res.get('reason')}")

        else:
            # Save Preferences
            pref.notify_low_stock = "notify_low_stock" in request.POST
            pref.notify_critical_stock = "notify_critical_stock" in request.POST
            pref.notify_out_of_stock = "notify_out_of_stock" in request.POST
            pref.notify_stock_received = "notify_stock_received" in request.POST
            pref.notify_stock_restored = "notify_stock_restored" in request.POST

            pref.notify_payment_due = "notify_payment_due" in request.POST
            pref.notify_payment_overdue = "notify_payment_overdue" in request.POST

            pref.notify_cheque_due_soon = "notify_cheque_due_soon" in request.POST
            pref.notify_cheque_due_today = "notify_cheque_due_today" in request.POST
            pref.notify_cheque_overdue = "notify_cheque_overdue" in request.POST

            pref.notify_receivable_due = "notify_receivable_due" in request.POST
            pref.notify_receivable_overdue = "notify_receivable_overdue" in request.POST
            pref.notify_payable_due = "notify_payable_due" in request.POST
            pref.notify_payable_overdue = "notify_payable_overdue" in request.POST

            pref.sms_enabled = "sms_enabled" in request.POST
            pref.sms_phone_number = request.POST.get("sms_phone_number", "").strip()
            pref.popup_enabled = "popup_enabled" in request.POST

            pref.save()
            messages.success(request, "Notification settings saved successfully.")
            return redirect("dashboard:notification_settings")

    return render(request, "dashboard/notification_settings.html", {"pref": pref})
