"""Forms for Expense management."""
from django import forms
from apps.accounting.models import Expense


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ["category", "amount", "expense_date", "payment_method", "reference", "description"]
        widgets = {
            "category": forms.TextInput(attrs={
                "class": "form-control",
                "id": "id_category",
                "placeholder": "e.g. Rent, Utilities, Salary, Office Supplies",
                "required": "required"
            }),
            "amount": forms.NumberInput(attrs={
                "class": "form-control font-mono",
                "id": "id_amount",
                "step": "0.01",
                "min": "0.01",
                "placeholder": "0.00",
                "required": "required"
            }),
            "expense_date": forms.DateInput(attrs={
                "class": "form-control",
                "id": "id_expense_date",
                "type": "date",
                "required": "required"
            }),
            "payment_method": forms.Select(
                choices=[
                    ("Cash", "Cash"),
                    ("Bank Transfer", "Bank Transfer"),
                    ("Online / QR", "Online / QR (Fonepay)"),
                    ("Cheque", "Cheque"),
                ],
                attrs={"class": "form-control", "id": "id_payment_method"}
            ),
            "reference": forms.TextInput(attrs={
                "class": "form-control",
                "id": "id_reference",
                "placeholder": "Payee name, voucher ref, or bill receipt #"
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "id": "id_description",
                "rows": 3,
                "placeholder": "Detailed notes on expense purpose, approval, or department"
            }),
        }
