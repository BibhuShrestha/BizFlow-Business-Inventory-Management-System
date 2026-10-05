"""
Forms for Receivables & Payables Management.
"""
from decimal import Decimal
from django import forms
from django.utils import timezone

from apps.sales.models import Customer, Payment
from apps.purchases.models import Supplier


class CreditEntryForm(forms.Form):
    """Unified entry form for Receivables (Customer Credit Given) and Payables (Supplier Credit Taken)."""

    CREDIT_TYPE_CHOICES = [
        ("given", "Receivable — Customer Credit (Debit / Dr)"),
        ("taken", "Payable — Supplier Credit (Credit / Cr)"),
    ]

    PAYMENT_METHOD_CHOICES = [
        ("Cash", "Cash"),
        ("QR / Mobile Pay", "QR / Mobile Pay"),
        ("Bank Transfer", "Bank Transfer"),
        ("Cheque", "Cheque"),
    ]

    credit_type = forms.ChoiceField(
        choices=CREDIT_TYPE_CHOICES,
        widget=forms.Select(attrs={"class": "form-control", "id": "credit_type_select"}),
        label="Transaction Type",
    )
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.filter(is_active=True).order_by("name"),
        required=False,
        widget=forms.Select(attrs={"class": "form-control", "id": "customer_select"}),
        label="Customer (for Receivables / Debit)",
    )
    supplier = forms.ModelChoiceField(
        queryset=Supplier.objects.filter(is_active=True).order_by("name"),
        required=False,
        widget=forms.Select(attrs={"class": "form-control", "id": "supplier_select"}),
        label="Supplier (for Payables / Credit)",
    )
    transaction_date = forms.DateField(
        initial=timezone.localdate,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        label="Transaction Date",
    )
    due_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        label="Due Date",
    )
    bill_number = forms.CharField(
        max_length=64,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. BILL-1029"}),
        label="Invoice / Bill Number",
    )
    discount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        initial=Decimal("0.00"),
        required=False,
        min_value=Decimal("0.00"),
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        label="Overall Discount (Rs.)",
    )
    initial_paid_amount = forms.DecimalField(
        max_digits=14,
        decimal_places=2,
        initial=Decimal("0.00"),
        required=False,
        min_value=Decimal("0.00"),
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        label="Initial Paid Amount (Rs.)",
    )
    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHOD_CHOICES,
        initial="Cash",
        widget=forms.Select(attrs={"class": "form-control"}),
        label="Payment Method (if paid)",
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Terms, notes or remarks..."}),
        label="Notes",
    )

    def clean(self):
        cleaned_data = super().clean()
        ctype = cleaned_data.get("credit_type")
        customer = cleaned_data.get("customer")
        supplier = cleaned_data.get("supplier")

        if ctype == "given" and not customer:
            self.add_error("customer", "Please select a customer for Credit Given.")
        elif ctype == "taken" and not supplier:
            self.add_error("supplier", "Please select a supplier for Credit Taken.")

        return cleaned_data


class PaymentAddForm(forms.Form):
    """Form to record partial or full payment vouchers against a credit transaction."""

    PAYMENT_METHOD_CHOICES = [
        ("Cash", "Cash"),
        ("QR / Mobile Pay", "QR / Mobile Pay"),
        ("Bank Transfer", "Bank Transfer"),
        ("Cheque", "Cheque"),
    ]

    amount = forms.DecimalField(
        max_digits=14,
        decimal_places=2,
        min_value=Decimal("0.01"),
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "0.00", "required": "required"}),
        label="Payment Amount (Rs.)",
    )
    payment_date = forms.DateField(
        initial=timezone.localdate,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        label="Payment Date",
    )
    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHOD_CHOICES,
        initial="Cash",
        widget=forms.Select(attrs={"class": "form-control"}),
        label="Payment Method",
    )
    reference = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Receipt #, Cheque #, Txn ID"}),
        label="Reference / Cheque / Txn ID",
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Payment notes..."}),
        label="Notes",
    )


class ChequeForm(forms.Form):
    """Form to record Cheque Given (to supplier) or Cheque Received (from customer)."""

    CHEQUE_TYPE_CHOICES = [
        ("RECEIVED", "Cheque Received (Customer - Receivable)"),
        ("GIVEN", "Cheque Given (Supplier - Payable)"),
    ]

    cheque_type = forms.ChoiceField(
        choices=CHEQUE_TYPE_CHOICES,
        widget=forms.Select(attrs={"class": "form-control", "id": "cheque_type_select"}),
        label="Cheque Type *",
    )
    cheque_number = forms.CharField(
        max_length=64,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. 104928"}),
        label="Cheque Number *",
    )
    bank_name = forms.CharField(
        max_length=128,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Nabil Bank"}),
        label="Bank Name *",
    )
    amount = forms.DecimalField(
        min_value=Decimal("0.01"),
        decimal_places=2,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "0.00"}),
        label="Cheque Amount (Rs.) *",
    )
    cheque_date = forms.DateField(
        initial=timezone.localdate,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        label="Cheque Date (Due / Maturity) *",
    )
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.filter(is_active=True).order_by("name"),
        required=False,
        widget=forms.Select(attrs={"class": "form-control", "id": "cheque_customer_select"}),
        label="Customer (if received)",
    )
    supplier = forms.ModelChoiceField(
        queryset=Supplier.objects.filter(is_active=True).order_by("name"),
        required=False,
        widget=forms.Select(attrs={"class": "form-control", "id": "cheque_supplier_select"}),
        label="Supplier (if given)",
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Cheque notes or memo..."}),
        label="Notes",
    )
