"""Authentication views for BizFlow web application."""
import logging

from django.contrib import messages
from django.contrib.auth import login, logout
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from domain.exceptions import (
    AuthenticationError,
    DuplicateEmailError,
    TokenInvalidError,
    ValidationError,
)
from domain.services.auth_service import AuthService
from apps.accounts.forms import (
    LoginForm,
    RegisterForm,
    ForgotPasswordForm,
    ResetPasswordForm,
    ChangePasswordForm,
)
from apps.accounts.permissions import login_required_custom

logger = logging.getLogger(__name__)

def _get_dashboard_url() -> str:
    try:
        from django.urls import reverse
        return reverse("dashboard:index")
    except Exception:
        return "/dashboard/"



def login_view(request: HttpRequest) -> HttpResponse:
    """Email + password login form."""
    if request.user.is_authenticated:
        return redirect(_get_dashboard_url())

    form = LoginForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        try:
            user = AuthService.authenticate(
                email=form.cleaned_data["email"],
                password=form.cleaned_data["password"],
            )
            login(request, user)
            next_url = request.GET.get("next") or request.POST.get("next") or _get_dashboard_url()
            # Protect against open redirect
            if not next_url.startswith("/") and not next_url.startswith("dashboard"):
                next_url = _get_dashboard_url()
            return redirect(next_url)
        except AuthenticationError as exc:
            messages.error(request, str(exc))

    return render(request, "accounts/login.html", {"form": form})


def logout_view(request: HttpRequest) -> HttpResponse:
    """Log the current user out and redirect to login."""
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, "You have been logged out successfully.")
    return redirect("accounts:login")


def register_view(request: HttpRequest) -> HttpResponse:
    """New account registration form."""
    if request.user.is_authenticated:
        return redirect(_get_dashboard_url())

    form = RegisterForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        try:
            user, token = AuthService.register(
                name=form.cleaned_data["name"],
                email=form.cleaned_data["email"],
                password=form.cleaned_data["password"],
            )
            from core.email import EmailService
            EmailService.send_verification_email(user, token, request)
            messages.success(
                request,
                "Account created! Please check your email to verify your address before logging in.",
            )
            return redirect("accounts:login")
        except (DuplicateEmailError, ValidationError) as exc:
            messages.error(request, str(exc))

    return render(request, "accounts/register.html", {"form": form})


def verify_email_view(request: HttpRequest, token: str) -> HttpResponse:
    """Email address verification via token link."""
    try:
        user = AuthService.verify_email(token)
        messages.success(request, "Email verified! You can now log in.")
    except TokenInvalidError:
        messages.error(request, "Verification link is invalid or has expired. Please request a new one.")
    return redirect("accounts:login")


def forgot_password_view(request: HttpRequest) -> HttpResponse:
    """Request a password reset email."""
    form = ForgotPasswordForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        result = AuthService.request_password_reset(email=form.cleaned_data["email"])
        if result:
            user, token = result
            from core.email import EmailService
            EmailService.send_password_reset_email(user, token, request)
        # Always show success to prevent email enumeration
        messages.success(
            request,
            "If that email is registered, you will receive a password reset link shortly.",
        )
        return redirect("accounts:login")

    return render(request, "accounts/forgot_password.html", {"form": form})


def reset_password_view(request: HttpRequest, token: str) -> HttpResponse:
    """Reset password using token from email."""
    form = ResetPasswordForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        try:
            AuthService.reset_password(
                token=token,
                new_password=form.cleaned_data["password"],
            )
            messages.success(request, "Password reset successfully! You can now log in.")
            return redirect("accounts:login")
        except TokenInvalidError:
            messages.error(request, "Reset link is invalid or has expired.")
            return redirect("accounts:forgot_password")
        except ValidationError as exc:
            messages.error(request, str(exc))

    return render(request, "accounts/reset_password.html", {"form": form, "token": token})


@login_required_custom
def change_password_view(request: HttpRequest) -> HttpResponse:
    """Change current user's password."""
    form = ChangePasswordForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        try:
            AuthService.change_password(
                user=request.user,
                current_password=form.cleaned_data["current_password"],
                new_password=form.cleaned_data["new_password"],
            )
            messages.success(request, "Password changed successfully.")
            return redirect(_get_dashboard_url())
        except (AuthenticationError, ValidationError) as exc:
            messages.error(request, str(exc))

    return render(request, "accounts/change_password.html", {"form": form})
