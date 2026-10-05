"""
URL patterns for Receivables & Payables Management.
"""
from django.urls import path
from apps.credit import views

app_name = "credit"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("given/", views.credit_given_list, name="given_list"),
    path("taken/", views.credit_taken_list, name="taken_list"),
    path("new/", views.credit_create, name="create"),
    path("given/<int:pk>/", views.credit_given_detail, name="given_detail"),
    path("taken/<int:pk>/", views.credit_taken_detail, name="taken_detail"),
    path("given/<int:pk>/delete/", views.credit_given_delete, name="given_delete"),
    path("taken/<int:pk>/delete/", views.credit_taken_delete, name="taken_delete"),
    path("payment/add/", views.payment_add, name="payment_add"),
    path("payments/", views.payment_list, name="payment_list"),
    path("payment/<int:pk>/delete/", views.payment_delete, name="payment_delete"),
    path("customers-dues/", views.customers_dues, name="customers_dues"),
    path("suppliers-dues/", views.suppliers_dues, name="suppliers_dues"),
    path("overdue/", views.overdue_list, name="overdue_list"),
    path("ledger/", views.ledger_select, name="ledger_select"),
    path("ledger/customer/<int:pk>/", views.customer_ledger, name="customer_ledger"),
    path("ledger/supplier/<int:pk>/", views.supplier_ledger, name="supplier_ledger"),
    path("reports/", views.credit_reports, name="reports"),
    path("export/<str:report_type>/", views.export_credit_csv, name="export_csv"),
    path("cheques/", views.cheques_list, name="cheques_list"),
    path("cheques/new/", views.cheque_create, name="cheque_create"),
    path("cheques/<int:pk>/status/", views.cheque_update_status, name="cheque_update_status"),
    path("cheques/export/<str:export_format>/", views.cheques_export, name="cheques_export"),
]
