"""Forms for User administrative management."""
from django import forms
from apps.accounts.models import User, Role
from apps.companies.models import Company
from domain.validators.password import check_password_strength


class UserCreateForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Enter strong password"}),
        help_text="Minimum 8 characters with uppercase, lowercase, number, and special character.",
    )

    class Meta:
        model = User
        fields = ["email", "name", "phone", "role", "active_company", "is_active", "password"]
        widgets = {
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "user@example.com"}),
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Full Name"}),
            "phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "+977 98XXXXXXXX"}),
            "role": forms.Select(attrs={"class": "form-control"}),
            "active_company": forms.Select(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("A user account with this email address already exists.")
        return email

    def clean_password(self):
        password = self.cleaned_data.get("password")
        if password:
            result = check_password_strength(password)
            if not result.valid:
                raise forms.ValidationError(result.error_message)
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"].strip().lower()
        user.set_password(self.cleaned_data["password"])
        user.email_verified = True
        if user.role and user.role.name.lower() in ("admin", "owner", "manager", "staff"):
            user.is_staff = True
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

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        qs = User.objects.filter(email__iexact=email)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Another user account already uses this email address.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"].strip().lower()
        if user.role and user.role.name.lower() in ("admin", "owner", "manager", "staff"):
            user.is_staff = True
        if commit:
            user.save()
        return user
