"""Authentication views for BizFlow web application."""
import logging

from django.contrib import messages
from django.contrib.auth import login, logout
from django.db import IntegrityError
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

from apps.core_app.security_utils import (
    get_safe_redirect_url,
    is_rate_limited,
    increment_rate_limit,
    clear_rate_limit,
    record_login_attempt,
    get_client_ip,
)

logger = logging.getLogger(__name__)

def _get_dashboard_url() -> str:
    try:
        from django.urls import reverse
        return reverse("dashboard:index")
    except Exception:
        return "/dashboard/"


def login_view(request: HttpRequest) -> HttpResponse:
    """Email + password login form with rate limiting, audit logging, and open redirect defense."""
    if request.user.is_authenticated:
        return redirect(_get_dashboard_url())

    form = LoginForm(request.POST or None)

    if request.method == "POST":
        client_ip = get_client_ip(request)
        rate_key = f"login_failures:{client_ip}"

        if is_rate_limited(rate_key, max_attempts=5, period_seconds=900):
            messages.error(
                request,
                "Too many failed login attempts. Please wait 15 minutes before trying again."
            )
            return render(request, "accounts/login.html", {"form": form})

        if form.is_valid():
            email = form.cleaned_data["email"].strip().lower()
            password = form.cleaned_data["password"]

            try:
                user = AuthService.authenticate(
                    email=email,
                    password=password,
                )
                clear_rate_limit(rate_key)
                record_login_attempt(user=user, request=request, success=True, method="web", message="Login success")
                login(request, user)
                if hasattr(user, "_supabase_session") and user._supabase_session:
                    request.session["supabase_access_token"] = user._supabase_session.get("access_token")
                    request.session["supabase_refresh_token"] = user._supabase_session.get("refresh_token")

                raw_next = request.GET.get("next") or request.POST.get("next") or _get_dashboard_url()
                safe_next = get_safe_redirect_url(raw_next, request, default=_get_dashboard_url())
                return redirect(safe_next)
            except AuthenticationError as exc:
                increment_rate_limit(rate_key, period_seconds=900)
                record_login_attempt(email=email, request=request, success=False, method="web", message=str(exc))
                # If account is pending verification, redirect directly to OTP screen
                if "verified" in str(exc).lower() or "check your inbox" in str(exc).lower():
                    request.session["verify_user_email"] = email
                    messages.warning(
                        request,
                        "Your email has not been verified yet. Please enter the 6-digit verification code sent to your email."
                    )
                    return redirect("accounts:verify_otp")
                messages.error(request, str(exc))

    return render(request, "accounts/login.html", {"form": form})


def logout_view(request: HttpRequest) -> HttpResponse:
    """Log the current user out and redirect to login."""
    if request.user.is_authenticated:
        from integrations.supabase_client import SupabaseAuthClient
        access_tok = request.session.get("supabase_access_token")
        if access_tok:
            try:
                SupabaseAuthClient.sign_out(access_tok)
            except Exception:
                pass
        logout(request)
        messages.success(request, "You have been logged out successfully.")
    return redirect("accounts:login")


def register_view(request: HttpRequest) -> HttpResponse:
    """New account registration form with rate limiting."""
    if request.user.is_authenticated:
        return redirect(_get_dashboard_url())

    form = RegisterForm(request.POST or None)

    if request.method == "POST":
        client_ip = get_client_ip(request)
        rate_key = f"web_reg_attempts:{client_ip}"
        if is_rate_limited(rate_key, max_attempts=10, period_seconds=900):
            messages.error(
                request,
                "Too many registration attempts. Please wait 15 minutes before trying again."
            )
            return render(request, "accounts/register.html", {"form": form})

        increment_rate_limit(rate_key, period_seconds=900)

        if form.is_valid():
            try:
                user, otp = AuthService.register(
                    name=form.cleaned_data["name"],
                    email=form.cleaned_data["email"],
                    password=form.cleaned_data["password"],
                )
                from core.email import EmailService
                EmailService.send_verification_otp(user, otp, request)

                # Store pending verification in session
                request.session["verify_user_id"] = user.id
                request.session["verify_user_email"] = user.email

                messages.success(
                    request,
                    f"Account created! We have sent a 6-digit verification code to {user.email}.",
                )
                return redirect("accounts:verify_otp")
            except DuplicateEmailError as exc:
                form.add_error("email", str(exc))
                messages.error(request, str(exc))
            except ValidationError as exc:
                form.add_error(None, str(exc))
                messages.error(request, str(exc))
            except IntegrityError:
                err_msg = f"An account with email '{form.cleaned_data.get('email')}' already exists. Please sign in instead."
                form.add_error("email", err_msg)
                messages.error(request, err_msg)

    return render(request, "accounts/register.html", {"form": form})


def verify_otp_view(request: HttpRequest) -> HttpResponse:
    """Verify 6-digit OTP code to activate account and access dashboard."""
    if request.user.is_authenticated:
        return redirect(_get_dashboard_url())

    session_email = request.session.get("verify_user_email") or ""
    query_email = request.GET.get("email") or ""
    email = (query_email or session_email).strip().lower()

    if email:
        from apps.accounts.models import User
        existing = User.objects.filter(email__iexact=email).first()
        if existing and getattr(existing, "email_verified", False) and getattr(existing, "is_active", False):
            request.session.pop("verify_user_id", None)
            request.session.pop("verify_user_email", None)
            messages.info(request, "Your email is already verified. Please sign in with your password.")
            return redirect("accounts:login")

    if request.method == "POST":
        otp = request.POST.get("otp", "").strip()
        target_email = (request.POST.get("email", "").strip() or email).lower()

        if not otp:
            messages.error(request, "Please enter the 6-digit verification code.")
            return render(request, "accounts/verify_otp.html", {"email": target_email})

        try:
            user = AuthService.verify_otp(target_email, otp)
            login(request, user)
            request.session.pop("verify_user_id", None)
            request.session.pop("verify_user_email", None)
            messages.success(
                request,
                f"Welcome to BizFlow, {user.name}! Your account has been verified and is ready.",
            )
            return redirect(_get_dashboard_url())
        except TokenInvalidError as exc:
            messages.error(request, str(exc))
        except Exception as exc:
            messages.error(request, f"Verification failed: {exc}")

        return render(request, "accounts/verify_otp.html", {"email": target_email})

    return render(request, "accounts/verify_otp.html", {"email": email})


def resend_otp_view(request: HttpRequest) -> HttpResponse:
    """Resend a new 6-digit OTP code with rate limiting."""
    client_ip = get_client_ip(request)
    rate_key = f"resend_otp:{client_ip}"
    if is_rate_limited(rate_key, max_attempts=5, period_seconds=300):
        messages.error(request, "Too many requests. Please wait a few minutes before resending.")
        return redirect("accounts:verify_otp")

    increment_rate_limit(rate_key, period_seconds=300)

    email = request.POST.get("email") or request.session.get("verify_user_email") or ""
    if not email:
        messages.error(request, "Unable to find your email. Please register again.")
        return redirect("accounts:register")

    try:
        user, otp = AuthService.resend_otp(email)
        from core.email import EmailService
        EmailService.send_verification_otp(user, otp, request)
        request.session["verify_user_id"] = user.id
        request.session["verify_user_email"] = user.email
        messages.success(request, f"A new 6-digit code has been sent to {user.email}.")
    except Exception as exc:
        messages.error(request, str(exc))

    return redirect("accounts:verify_otp")


def verify_email_view(request: HttpRequest, token: str) -> HttpResponse:
    """Email address verification via token link."""
    try:
        user = AuthService.verify_email(token)
        messages.success(request, "Email verified! You can now log in.")
    except TokenInvalidError:
        messages.error(request, "Verification link is invalid or has expired. Please request a new one.")
    return redirect("accounts:login")


def forgot_password_view(request: HttpRequest) -> HttpResponse:
    """Request a password reset email with abuse rate limiting."""
    form = ForgotPasswordForm(request.POST or None)

    if request.method == "POST":
        client_ip = get_client_ip(request)
        rate_key = f"web_pwd_reset:{client_ip}"
        if is_rate_limited(rate_key, max_attempts=5, period_seconds=900):
            messages.error(
                request,
                "Too many password reset requests. Please wait 15 minutes before trying again."
            )
            return render(request, "accounts/forgot_password.html", {"form": form})

        increment_rate_limit(rate_key, period_seconds=900)

        if form.is_valid():
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


def google_login_view(request: HttpRequest) -> HttpResponse:
    """Initiate Google OAuth 2.0 OpenID Connect authorization flow."""
    if request.user.is_authenticated:
        return redirect(_get_dashboard_url())

    from django.conf import settings
    from django.urls import reverse
    from integrations.google_oauth import GoogleOAuthClient
    import secrets

    raw_next = request.GET.get("next") or request.POST.get("next") or _get_dashboard_url()
    safe_next = get_safe_redirect_url(raw_next, request, default=_get_dashboard_url())

    # If real Google credentials are not configured
    if not GoogleOAuthClient.is_configured() and not getattr(settings, "TESTING", False):
        if settings.DEBUG:
            # Handle developer simulation submission
            if request.method == "POST" and request.POST.get("dev_simulate") == "1":
                sim_email = request.POST.get("email", "").lower().strip() or "bibhustha111@gmail.com"
                sim_name = request.POST.get("name", "").strip() or sim_email.split("@")[0].title()
                user_info = {
                    "sub": f"google_dev_{abs(hash(sim_email))}",
                    "email": sim_email,
                    "name": sim_name,
                    "email_verified": True,
                    "picture": "",
                }
                user, created = AuthService.login_or_register_via_google(user_info)
                login(request, user)
                record_login_attempt(user=user, request=request, success=True, method="google_dev_sim", message="Google dev simulation login")
                if created:
                    messages.success(request, f"Welcome to BizFlow, {user.name}! Your account has been created via Google.")
                else:
                    messages.success(request, f"Welcome back, {user.name}!")
                return redirect(safe_next)

            redirect_uri = request.build_absolute_uri(reverse("accounts:google_callback"))
            return render(request, "accounts/google_dev_login.html", {
                "next": safe_next,
                "redirect_uri": redirect_uri,
                "default_email": "bibhustha111@gmail.com",
            })
        else:
            messages.error(request, "Google sign-in is currently unavailable. Please sign in with your email and password.")
            return redirect("accounts:login")

    state = secrets.token_urlsafe(32)
    request.session["google_oauth_state"] = state
    request.session["google_oauth_next"] = safe_next

    redirect_uri = request.build_absolute_uri(reverse("accounts:google_callback"))
    auth_url = GoogleOAuthClient.get_auth_url(redirect_uri=redirect_uri, state=state)
    return redirect(auth_url)



def google_callback_view(request: HttpRequest) -> HttpResponse:
    """Handle Google OAuth 2.0 authorization callback and sign in user."""
    from integrations.google_oauth import GoogleOAuthClient, GoogleOAuthError
    from django.urls import reverse

    if request.user.is_authenticated:
        return redirect(_get_dashboard_url())

    error_param = request.GET.get("error")
    if error_param:
        logger.warning("Google OAuth error response: %s", error_param)
        messages.error(request, f"Google login was cancelled or denied: {error_param}")
        return redirect("accounts:login")

    expected_state = request.session.pop("google_oauth_state", None)
    received_state = request.GET.get("state")

    if not expected_state or not received_state or expected_state != received_state:
        logger.warning("Google OAuth state validation mismatch.")
        messages.error(request, "Google sign-in session expired or invalid. Please try again.")
        return redirect("accounts:login")

    code = request.GET.get("code")
    if not code:
        messages.error(request, "Authorization code not provided by Google.")
        return redirect("accounts:login")

    redirect_uri = request.build_absolute_uri(reverse("accounts:google_callback"))

    try:
        token_data = GoogleOAuthClient.exchange_code(code=code, redirect_uri=redirect_uri)
        user_info = GoogleOAuthClient.get_user_info(token_data=token_data)
        user, created = AuthService.login_or_register_via_google(user_info)
        login(request, user)
        record_login_attempt(user=user, request=request, success=True, method="google_oauth", message="Google login success")

        safe_next = request.session.pop("google_oauth_next", _get_dashboard_url())
        if created:
            messages.success(request, f"Welcome to BizFlow, {user.name}! Your account has been created via Google.")
        else:
            messages.success(request, f"Welcome back, {user.name}!")
        return redirect(safe_next)
    except (GoogleOAuthError, AuthenticationError) as exc:
        record_login_attempt(email=request.GET.get("email", ""), request=request, success=False, method="google_oauth", message=str(exc))
        messages.error(request, str(exc))
        return redirect("accounts:login")
    except Exception as exc:
        logger.exception("Unexpected error during Google OAuth callback: %s", exc)
        messages.error(request, "An unexpected error occurred during Google sign-in. Please try again.")
        return redirect("accounts:login")

