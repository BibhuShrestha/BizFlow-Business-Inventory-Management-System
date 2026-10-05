"""Forms for Expense management."""
from django import forms
from apps.accounting.models import Expense


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ["category", "amount", "expense_date", "payment_method", "reference", "description"]
        widgets = {
            "category": forms.TextInput(attrs={"class": "form-control", "placeholder": "Rent, Utilities, Salary, etc."}),
            "amount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "expense_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "payment_method": forms.Select(
                choices=[("Cash", "Cash"), ("Bank Transfer", "Bank Transfer"), ("Cheque", "Cheque"), ("Online / QR", "Online / QR")],
                attrs={"class": "form-control"}
            ),
            "reference": forms.TextInput(attrs={"class": "form-control", "placeholder": "Bill/Voucher/Receipt Ref"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }
