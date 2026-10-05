"""Forms for Inventory application."""
from django import forms
from apps.inventory.models import Product, Category, StockAdjustment
from apps.companies.models import Company, Seller


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "sku", "name", "category", "company", "seller", "unit",
            "purchase_price", "selling_price", "tax_rate",
            "minimum_stock", "current_stock", "description"
        ]
        widgets = {
            "sku": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. PROD-001"}),
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Product Name"}),
            "category": forms.Select(attrs={"class": "form-control"}),
            "company": forms.Select(attrs={"class": "form-control"}),
            "seller": forms.Select(attrs={"class": "form-control"}),
            "unit": forms.TextInput(attrs={"class": "form-control", "placeholder": "pcs, kg, m, etc."}),
            "purchase_price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "selling_price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "tax_rate": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "minimum_stock": forms.NumberInput(attrs={"class": "form-control"}),
            "current_stock": forms.NumberInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].required = False
        self.fields["company"].required = False
        self.fields["seller"].required = False
        self.fields["sku"].required = False
        self.fields["unit"].required = False
        self.fields["tax_rate"].required = False
        self.fields["purchase_price"].required = False
        self.fields["minimum_stock"].required = False
        self.fields["current_stock"].required = False



class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "description", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Category Name"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class StockAdjustmentForm(forms.Form):
    product = forms.ModelChoiceField(queryset=Product.objects.filter(is_active=True), widget=forms.Select(attrs={"class": "form-control"}))
    adjustment_type = forms.ChoiceField(
        choices=[("IN", "Add Stock (Increase)"), ("OUT", "Deduct Stock (Decrease)")],
        widget=forms.Select(attrs={"class": "form-control"})
    )
    quantity = forms.IntegerField(min_value=1, widget=forms.NumberInput(attrs={"class": "form-control"}))
    reason = forms.CharField(max_length=255, widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Reason for adjustment"}))
