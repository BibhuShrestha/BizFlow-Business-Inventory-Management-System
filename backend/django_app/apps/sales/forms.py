"""Forms for Sales transactions and invoices."""
from decimal import Decimal
from django import forms
from apps.sales.models import Sale, Customer
from apps.inventory.models import Product
from apps.companies.models import Company


class SaleForm(forms.Form):
    company = forms.ModelChoiceField(
        queryset=Company.objects.all(),
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
        empty_label="-- Select Company (Optional) --"
    )
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.filter(is_active=True),
        required=True,
        widget=forms.Select(attrs={"class": "form-control"})
    )
    product = forms.ModelChoiceField(
        queryset=Product.objects.filter(is_active=True, current_stock__gt=0),
        required=True,
        widget=forms.Select(attrs={"class": "form-control"})
    )
    quantity = forms.IntegerField(min_value=1, initial=1, widget=forms.NumberInput(attrs={"class": "form-control"}))
    unit_price = forms.DecimalField(
        min_value=Decimal("0.00"),
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "Auto-filled from product if left empty"})
    )
    discount = forms.DecimalField(
        min_value=Decimal("0.00"),
        decimal_places=2,
        initial=Decimal("0.00"),
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"})
    )
    bill_number = forms.CharField(max_length=64, required=False, widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Optional Bill/Slip Number"}))
    payment_status = forms.ChoiceField(
        choices=Sale.STATUS_CHOICES,
        initial=Sale.STATUS_PAID,
        widget=forms.Select(attrs={"class": "form-control"})
    )
    payment_method = forms.ChoiceField(
        choices=[("Cash", "Cash"), ("Cheque", "Cheque"), ("Card", "Card"), ("Online / QR", "Online / QR"), ("Credit", "Credit")],
        initial="Cash",
        widget=forms.Select(attrs={"class": "form-control"})
    )
    cheque_number = forms.CharField(max_length=64, required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    cheque_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}))
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}))
