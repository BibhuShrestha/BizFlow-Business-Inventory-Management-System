"""Forms for User administrative management."""
from django import forms
from apps.accounts.models import User, Role
from apps.companies.models import Company


from domain.validators.password import check_password_strength


class UserCreateForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Password"}))

    class Meta:
        model = User
        fields = ["email", "name", "phone", "role", "active_company", "is_active", "password"]
        widgets = {
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "user@example.com"}),
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Full Name"}),
            "phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "Phone Number"}),
            "role": forms.Select(attrs={"class": "form-control"}),
            "active_company": forms.Select(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_password(self):
        password = self.cleaned_data.get("password")
        if password:
            result = check_password_strength(password)
            if not result.valid:
                raise forms.ValidationError(result.error_message)
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.email_verified = True
        if commit:
            user.save()
        return user


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["email", "name", "phone", "role", "active_company", "is_active", "email_verified"]
        widgets = {
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "role": forms.Select(attrs={"class": "form-control"}),
            "active_company": forms.Select(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "email_verified": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
