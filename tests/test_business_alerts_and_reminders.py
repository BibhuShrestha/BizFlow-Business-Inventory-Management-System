"""
Comprehensive test suite for BizFlow Business Management Enhancements:
- Stock Alerts (Low, Critical, Out of stock, Received, Restored, Deduplication)
- Cheque Management & Reminders (Given, Received, Status transitions, Reminders)
- Payment Due & Receivables/Payables Schedule
- Central In-App Popup & Notification Center
- SMS Layer & Cost Control
- Import & Export (Excel, CSV, JSON multi-format)
- Web Views & FastAPI REST Endpoints
"""
from datetime import date, timedelta
from decimal import Decimal
import json
import pytest

from django.test import Client
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.accounts.models import Role
from apps.companies.models import Company
from apps.inventory.models import Category, Product, StockMovement
from apps.sales.models import Customer, Sale, SaleItem, Payment
from apps.purchases.models import Supplier, Purchase
from apps.credit.models import Cheque
from apps.audit.models import Notification, NotificationPreference, SMSLog
from domain.services.stock_service import StockService
from domain.services.credit_service import CreditService
from domain.services.notification_service import NotificationService
from domain.services.sms_service import SMSService
from domain.services.import_export_service import ImportExportService
from domain.exceptions import ValidationError, NotFoundError

User = get_user_model()


@pytest.fixture
def test_setup(db):
    """Setup company, users, and base models for tests."""
    admin_role = Role.objects.get_or_create(name="admin", defaults={"description": "Admin"})[0]
    company = Company.objects.create(company_name="Apex Trading Pvt Ltd", vat_pan_number="123456789")
    admin_user = User.objects.create_user(
        email="admin@apextrading.com",
        name="Admin User",
        password="AdminPassword123!",
        role=admin_role,
        active_company=company,
        phone="9800000001",
    )
    customer = Customer.objects.create(
        name="Ram Sharma",
        phone="9841234567",
        company=company,
        email="ram@example.com",
    )
    supplier = Supplier.objects.create(
        name="Himalayan Foods Suppliers",
        phone="9851098765",
        company=company,
        email="himalayan@example.com",
    )
    category = Category.objects.create(name="Groceries")
    product_rice = Product.objects.create(
        name="Mansuli Rice 25kg",
        sku="RICE-25KG",
        category=category,
        company=company,
        selling_price=Decimal("2200.00"),
        purchase_price=Decimal("1800.00"),
        current_stock=20,
        minimum_stock=10,
        critical_stock=3,
        unit="bag",
    )
    return {
        "company": company,
        "admin": admin_user,
        "customer": customer,
        "supplier": supplier,
        "category": category,
        "product": product_rice,
    }


# ==============================================================================
# 1. STOCK MANAGEMENT ALERTS & DEDUPLICATION
# ==============================================================================
@pytest.mark.django_db
class TestStockManagementAlerts:
    def test_low_stock_and_critical_stock_detection(self, test_setup):
        company = test_setup["company"]
        admin = test_setup["admin"]
        product = test_setup["product"]

        # 1. Normal stock (> 10)
        assert product.stock_status == "normal"

        # 2. Low stock (4 - 10)
        product.current_stock = 8
        product.save()
        assert product.stock_status == "low"
        
        NotificationService.check_stock_alerts(company_id=company.id, user=admin)
        notif = Notification.objects.filter(
            record_id=product.id,
            notification_type="low_stock"
        ).first()
        assert notif is not None
        assert "Low Stock Alert" in notif.title
        assert notif.priority == "normal"

        # 3. Critical stock (1 - 3)
        product.current_stock = 2
        product.save()
        assert product.stock_status == "critical"
        
        NotificationService.check_stock_alerts(company_id=company.id, user=admin)
        crit_notif = Notification.objects.filter(
            record_id=product.id,
            notification_type="critical_stock"
        ).first()
        assert crit_notif is not None
        assert crit_notif.priority == "high"

        # 4. Out of stock (0)
        product.current_stock = 0
        product.save()
        assert product.stock_status == "out_of_stock"
        
        NotificationService.check_stock_alerts(company_id=company.id, user=admin)
        out_notif = Notification.objects.filter(
            record_id=product.id,
            notification_type="out_of_stock"
        ).first()
        assert out_notif is not None
        assert out_notif.priority == "critical"
        assert out_notif.is_popup is True

    def test_stock_alert_deduplication(self, test_setup):
        """Verify repeated calls do not create duplicate notifications for the same state."""
        company = test_setup["company"]
        admin = test_setup["admin"]
        product = test_setup["product"]
        product.current_stock = 0
        product.save()

        # Call twice
        NotificationService.check_stock_alerts(company_id=company.id, user=admin)
        NotificationService.check_stock_alerts(company_id=company.id, user=admin)

        count = Notification.objects.filter(record_id=product.id, notification_type="out_of_stock").count()
        assert count == 1, "Duplicate out-of-stock notifications must not be generated"

    def test_stock_received_and_stock_restored_notifications(self, test_setup):
        product = test_setup["product"]

        # Product starts at 0 stock
        product.current_stock = 0
        product.save()

        # Add inward stock
        StockService.add(
            product_id=product.id,
            quantity=50,
            reference_type="PURCHASE",
            description="Supplier shipment received",
        )

        product.refresh_from_db()
        assert product.current_stock == 50

        # Verify stock_received notification
        received_notif = Notification.objects.filter(
            record_id=product.id,
            notification_type="stock_received"
        ).first()
        assert received_notif is not None
        assert "Stock Received" in received_notif.title

        # Verify stock_restored notification (because was previously 0)
        restored_notif = Notification.objects.filter(
            record_id=product.id,
            notification_type="stock_restored"
        ).first()
        assert restored_notif is not None
        assert "Stock Restored" in restored_notif.title


# ==============================================================================
# 2. CHEQUE MANAGEMENT & REMINDERS
# ==============================================================================
@pytest.mark.django_db
class TestChequeManagement:
    def test_cheque_given_and_received_lifecycles(self, test_setup):
        company = test_setup["company"]
        admin = test_setup["admin"]
        customer = test_setup["customer"]
        supplier = test_setup["supplier"]

        # Create Cheque Given to Supplier
        cheque_given = CreditService.create_cheque(
            cheque_type=Cheque.TYPE_GIVEN,
            cheque_number="CHQ-99001",
            bank_name="Nepal Investment Mega Bank",
            amount=Decimal("75000.00"),
            cheque_date=timezone.localdate() + timedelta(days=2),
            supplier_id=supplier.id,
            notes="Advance for next consignment",
            company_id=company.id,
            user=admin,
        )
        assert cheque_given.status == Cheque.STATUS_PENDING
        assert cheque_given.is_due_soon is True
        assert cheque_given.days_until_due == 2

        # Create Cheque Received from Customer
        cheque_rcvd = CreditService.create_cheque(
            cheque_type=Cheque.TYPE_RECEIVED,
            cheque_number="CHQ-11002",
            bank_name="Nabil Bank",
            amount=Decimal("45000.00"),
            cheque_date=timezone.localdate(),
            customer_id=customer.id,
            company_id=company.id,
            user=admin,
        )
        assert cheque_rcvd.is_due_today is True

        # Transition status
        cleared_chq = CreditService.update_cheque_status(
            cheque_id=cheque_rcvd.id,
            status=Cheque.STATUS_CLEARED,
            notes="Deposited and realized in current account",
            user=admin,
        )
        assert cleared_chq.status == Cheque.STATUS_CLEARED

        # Summary KPIs
        summary = CreditService.get_cheques_summary(company_id=company.id)
        assert summary["cleared_count"] == 1
        assert summary["pending_count"] == 1
        assert summary["given_count"] == 1
        assert summary["received_count"] == 1

    def test_cheque_due_reminders_schedule(self, test_setup):
        company = test_setup["company"]
        admin = test_setup["admin"]
        customer = test_setup["customer"]

        # Cheque due today
        chq_today = CreditService.create_cheque(
            cheque_type=Cheque.TYPE_RECEIVED,
            cheque_number="CHQ-TODAY",
            bank_name="Global IME Bank",
            amount=Decimal("15000.00"),
            cheque_date=timezone.localdate(),
            customer_id=customer.id,
            company_id=company.id,
            user=admin,
        )

        NotificationService.check_cheque_reminders(company_id=company.id, user=admin)
        notif = Notification.objects.filter(record_id=chq_today.id).first()
        assert notif is not None
        assert "Due Today" in notif.title
        assert notif.priority == "critical"


# ==============================================================================
# 3. PAYMENT DUE REMINDERS & RECEIVABLES/PAYABLES SUMMARY
# ==============================================================================
@pytest.mark.django_db
class TestPaymentDueAndCreditSummary:
    def test_payment_due_reminders_and_overdue(self, test_setup):
        company = test_setup["company"]
        admin = test_setup["admin"]
        customer = test_setup["customer"]
        product = test_setup["product"]

        # Create credit sale due tomorrow
        due_tomorrow = timezone.localdate() + timedelta(days=1)
        sale = Sale.objects.create(
            company=company,
            customer=customer,
            invoice_number="INV-DUE-TOMORROW",
            total=Decimal("4400.00"),
            payment_status=Sale.STATUS_DUE,
            due_date=due_tomorrow,
            sale_date=timezone.now(),
        )
        SaleItem.objects.create(
            sale=sale,
            product=product,
            quantity=2,
            unit_price=Decimal("2200.00"),
            total=Decimal("4400.00"),
        )

        NotificationService.check_payment_due_reminders(company_id=company.id, user=admin)
        notif = Notification.objects.filter(record_id=sale.id, notification_type="payment_due").first()
        assert notif is not None
        assert "Due Tomorrow" in notif.title or "due tomorrow" in notif.message.lower()

    def test_partial_payment_and_overpayment_prevention(self, test_setup):
        company = test_setup["company"]
        customer = test_setup["customer"]
        admin = test_setup["admin"]

        sale = Sale.objects.create(
            company=company,
            customer=customer,
            invoice_number="INV-PARTIAL",
            total=Decimal("10000.00"),
            payment_status=Sale.STATUS_DUE,
            sale_date=timezone.now(),
        )

        # Payment 1: Rs. 3000
        CreditService.add_payment(
            credit_type="given",
            transaction_id=sale.id,
            amount=Decimal("3000.00"),
            payment_method="Cash",
            user=admin,
        )
        sale.refresh_from_db()
        assert sale.paid_amount == Decimal("3000.00")
        assert sale.remaining_amount == Decimal("7000.00")
        assert sale.payment_status == Sale.STATUS_PARTIAL

        # Overpayment: Rs. 8000 when remaining is 7000 -> Should raise ValidationError
        with pytest.raises(ValidationError):
            CreditService.add_payment(
                credit_type="given",
                transaction_id=sale.id,
                amount=Decimal("8000.00"),
                user=admin,
            )

    def test_receivables_and_payables_summary(self, test_setup):
        company = test_setup["company"]
        summary = CreditService.get_credit_summary(company_id=company.id)
        assert "credit_given_total" in summary
        assert "customer_due" in summary
        assert "supplier_due" in summary
        assert "overdue_given_amount" in summary


# ==============================================================================
# 4. IN-APP POPUP NOTIFICATIONS & PREFERENCES
# ==============================================================================
@pytest.mark.django_db
class TestInAppPopupsAndPreferences:
    def test_popup_dismissal(self, test_setup):
        company = test_setup["company"]
        admin = test_setup["admin"]

        notif = Notification.objects.create(
            user=admin,
            company=company,
            title="Immediate Stock Action",
            message="Item is critically low",
            notification_type="critical_stock",
            priority="high",
            is_popup=True,
            popup_dismissed=False,
        )

        active = NotificationService.get_active_popups(user=admin)
        assert len(active) >= 1

        success = NotificationService.dismiss_popup(user=admin, notification_id=notif.id)
        assert success is True
        notif.refresh_from_db()
        assert notif.popup_dismissed is True

    def test_notification_preference_opt_out(self, test_setup):
        admin = test_setup["admin"]

        # Disable low stock alerts in user preference
        pref, _ = NotificationPreference.objects.get_or_create(user=admin)
        pref.notify_low_stock = False
        pref.save()

        # Dispatch should be suppressed by preference
        notif = NotificationService.dispatch_notification(
            user=admin,
            title="Should be skipped",
            message="Test skip",
            notification_type="low_stock",
            priority="normal",
        )
        assert notif is None


# ==============================================================================
# 5. SMS NOTIFICATION LAYER & COST CONTROL
# ==============================================================================
@pytest.mark.django_db
class TestSMSNotificationsAndCostControl:
    def test_sms_dispatch_and_duplicate_prevention(self, test_setup):
        admin = test_setup["admin"]

        # Set up preferences with SMS enabled
        pref, _ = NotificationPreference.objects.get_or_create(user=admin)
        pref.sms_enabled = True
        pref.sms_phone_number = "9841000000"
        pref.save()

        # First dispatch
        res1 = SMSService.send_alert_sms(
            user=admin,
            notification_type="low_stock",
            message="ALERT: Low stock on Rice.",
            dedup_key="sms_rice_low_001",
        )
        assert res1["sent"] is True

        log_entry = SMSLog.objects.filter(dedup_key="sms_rice_low_001").first()
        assert log_entry is not None
        assert log_entry.status == "Sent"

        # Second dispatch with identical dedup_key -> must be suppressed
        res2 = SMSService.send_alert_sms(
            user=admin,
            notification_type="low_stock",
            message="ALERT: Low stock on Rice.",
            dedup_key="sms_rice_low_001",
        )
        assert res2["sent"] is False
        assert "Deduplicated" in res2["reason"]


# ==============================================================================
# 6. IMPORT & EXPORT SERVICE (EXCEL, CSV, JSON)
# ==============================================================================
@pytest.mark.django_db
class TestImportExportService:
    def test_export_formats_csv_json_excel(self, test_setup):
        company = test_setup["company"]
        admin = test_setup["admin"]

        # CSV Export
        csv_resp = ImportExportService.export_data("products", "csv", company_id=company.id, user=admin)
        assert "text/csv" in csv_resp["Content-Type"]
        assert b"Mansuli Rice" in csv_resp.content

        # JSON Export
        json_resp = ImportExportService.export_data("products", "json", company_id=company.id, user=admin)
        assert "application/json" in json_resp["Content-Type"]
        data = json.loads(json_resp.content.decode("utf-8"))
        assert len(data) >= 1
        assert data[0]["Product Name"] == "Mansuli Rice 25kg"

        # Excel Export
        xlsx_resp = ImportExportService.export_data("products", "xlsx", company_id=company.id, user=admin)
        assert "spreadsheetml" in xlsx_resp["Content-Type"]

    def test_import_validation_and_duplicate_skip(self, test_setup):
        company = test_setup["company"]
        admin = test_setup["admin"]

        rows = [
            {"name": "Soyabean Oil 1L", "sku": "OIL-1L", "selling_price": "240.00", "current_stock": "30"},
            {"name": "Mansuli Rice 25kg", "sku": "RICE-25KG", "selling_price": "2200.00", "current_stock": "20"},  # duplicate SKU
        ]

        result = ImportExportService.execute_import(
            module="products",
            rows=rows,
            company_id=company.id,
            user=admin,
        )

        assert result["imported"] == 1
        assert result["skipped"] == 1

        new_product = Product.objects.filter(sku="OIL-1L").first()
        assert new_product is not None
        assert new_product.selling_price == Decimal("240.00")


# ==============================================================================
# 7. WEB UI VIEWS & FASTAPI REST ENDPOINTS
# ==============================================================================
@pytest.mark.django_db(transaction=True)
class TestWebAndAPIIntegration:
    def test_web_cheques_list_and_dashboard_alerts(self, test_setup):
        client = Client()
        client.force_login(test_setup["admin"])

        # Check Dashboard with Section 18 Business Alerts
        resp = client.get("/dashboard/")
        assert resp.status_code == 200
        assert b"Business Alerts" in resp.content
        assert b"Receivables & Payables Summary" in resp.content

        # Check Cheques view
        resp = client.get("/credit/cheques/")
        assert resp.status_code == 200
        assert b"Cheque Management" in resp.content

        # Check Import/Export hub
        resp = client.get("/import-export/")
        assert resp.status_code == 200
        assert b"Import & Export Hub" in resp.content

    def test_fastapi_rest_endpoints(self, test_setup):
        from fastapi.testclient import TestClient
        from api.main import app
        from core.security import create_access_token

        client = TestClient(app)
        admin = test_setup["admin"]
        company = test_setup["company"]
        token = create_access_token(
            data={
                "sub": str(admin.id),
                "email": admin.email,
                "role": admin.role.name,
                "company_id": company.id,
            }
        )
        headers = {"Authorization": f"Bearer {token}"}

        # Cheques summary
        resp = client.get("/api/v1/cheques/summary", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "total_given" in data
        assert "total_received" in data

        # Business alerts summary
        resp = client.get("/api/v1/notifications/alerts-summary", headers=headers)
        assert resp.status_code == 200
        alert_data = resp.json()
        assert "out_of_stock" in alert_data
        assert "low_stock" in alert_data
        assert "payments_due" in alert_data
        assert "cheques_due" in alert_data
