"""Forms for Company and Seller models."""
from django import forms
from apps.companies.models import Company, Seller


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ["company_name", "company_phone", "vat_pan_number", "address", "logo_url"]
        widgets = {
            "company_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Company Name"}),
            "company_phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "Phone Number"}),
            "vat_pan_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "VAT / PAN Number"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Address"}),
            "logo_url": forms.TextInput(attrs={"class": "form-control", "placeholder": "Logo URL / Path"}),
        }


class SellerForm(forms.ModelForm):
    class Meta:
        model = Seller
        fields = ["seller_name", "seller_phone", "company"]
        widgets = {
            "seller_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Seller / Owner Name"}),
            "seller_phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "Phone Number"}),
            "company": forms.Select(attrs={"class": "form-control"}),
        }
