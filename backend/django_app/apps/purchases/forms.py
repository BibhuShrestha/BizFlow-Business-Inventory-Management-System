"""Forms for Purchase orders and bills."""
from decimal import Decimal
from django import forms
from apps.purchases.models import Purchase, Supplier
from apps.inventory.models import Product
from apps.companies.models import Company


class PurchaseForm(forms.Form):
    company = forms.ModelChoiceField(
        queryset=Company.objects.all(),
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
        empty_label="-- Select Company (Optional) --"
    )
    supplier = forms.ModelChoiceField(
        queryset=Supplier.objects.filter(is_active=True),
        required=True,
        widget=forms.Select(attrs={"class": "form-control"})
    )
    product = forms.ModelChoiceField(
        queryset=Product.objects.filter(is_active=True),
        required=True,
        widget=forms.Select(attrs={"class": "form-control"})
    )
    quantity = forms.IntegerField(min_value=1, initial=1, widget=forms.NumberInput(attrs={"class": "form-control"}))
    unit_price = forms.DecimalField(
        min_value=Decimal("0.00"),
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "Auto-filled from product purchase price if empty"})
    )
    discount = forms.DecimalField(
        min_value=Decimal("0.00"),
        decimal_places=2,
        initial=Decimal("0.00"),
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"})
    )
    bill_number = forms.CharField(max_length=64, required=False, widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Vendor Bill Number"}))
    payment_status = forms.ChoiceField(
        choices=Purchase.STATUS_CHOICES,
        initial=Purchase.STATUS_PAID,
        widget=forms.Select(attrs={"class": "form-control"})
    )
    payment_method = forms.ChoiceField(
        choices=[("Cash", "Cash"), ("Cheque", "Cheque"), ("Bank Transfer", "Bank Transfer"), ("Credit", "Credit")],
        initial="Cash",
        widget=forms.Select(attrs={"class": "form-control"})
    )
    cheque_number = forms.CharField(max_length=64, required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    cheque_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}))
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}))
