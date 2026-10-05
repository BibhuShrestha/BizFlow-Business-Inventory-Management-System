"""Forms for the accounts application."""
from django import forms


class LoginForm(forms.Form):
    email = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(attrs={"placeholder": "you@example.com", "autofocus": True, "class": "form-control"}),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"placeholder": "Your password", "class": "form-control"}),
    )


class RegisterForm(forms.Form):
    name = forms.CharField(
        max_length=128,
        label="Full Name",
        widget=forms.TextInput(attrs={"placeholder": "Your full name", "class": "form-control"}),
    )
    email = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(attrs={"placeholder": "you@example.com", "class": "form-control"}),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"placeholder": "Choose a password", "class": "form-control"}),
    )
    password_confirm = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={"placeholder": "Repeat your password", "class": "form-control"}),
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm = cleaned_data.get("password_confirm")
        if password and confirm and password != confirm:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data


class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(attrs={"placeholder": "you@example.com", "class": "form-control"}),
    )


class ResetPasswordForm(forms.Form):
    password = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={"placeholder": "New password", "class": "form-control"}),
    )
    password_confirm = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={"placeholder": "Repeat new password", "class": "form-control"}),
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm = cleaned_data.get("password_confirm")
        if password and confirm and password != confirm:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data


class ChangePasswordForm(forms.Form):
    current_password = forms.CharField(
        label="Current Password",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
    new_password = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
    new_password_confirm = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

    def clean(self):
        cleaned_data = super().clean()
        new_pw = cleaned_data.get("new_password")
        confirm = cleaned_data.get("new_password_confirm")
        if new_pw and confirm and new_pw != confirm:
            raise forms.ValidationError("New passwords do not match.")
        return cleaned_data
