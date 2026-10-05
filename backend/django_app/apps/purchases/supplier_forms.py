from decimal import Decimal
from django import forms
from apps.purchases.models import Supplier


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ["name", "phone", "email", "address", "opening_balance", "company", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Supplier / Vendor Name"}),
            "phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "Phone Number"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "vendor@example.com"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "opening_balance": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "company": forms.Select(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["opening_balance"].required = False
        self.fields["opening_balance"].initial = Decimal("0.00")
        self.fields["company"].required = False
        self.fields["is_active"].required = False
        self.fields["is_active"].initial = True

