"""
Supabase Auth & Client Integration.

Provides direct, lightweight communication with Supabase Auth (GoTrue) REST API:
- Sign in with email & password
- Sign up with metadata
- Sign out / session revocation
- Password recovery / reset
- JWT verification (offline via SUPABASE_JWT_SECRET or online via /auth/v1/user)
- User identity synchronization with Django accounts.User

Uses standard 'requests' and 'PyJWT' without requiring bulky external SDKs.
"""
import os
import logging
from typing import Any, Dict, Optional, Tuple

import requests
try:
    from jose import jwt, JWTError, ExpiredSignatureError
    InvalidTokenError = JWTError
    PyJWTError = JWTError
except ImportError:
    import jwt
    from jwt import ExpiredSignatureError, InvalidTokenError, PyJWTError

from domain.exceptions import AuthenticationError, ValidationError

logger = logging.getLogger(__name__)


class SupabaseAuthClient:
    """Lightweight client for Supabase Auth REST API."""

    @classmethod
    def get_url(cls) -> str:
        url = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
        for suffix in ["/rest/v1", "/rest", "/auth/v1"]:
            if url.endswith(suffix):
                url = url[:-len(suffix)].rstrip("/")
        return url

    @classmethod
    def get_anon_key(cls) -> str:
        return (
            os.getenv("SUPABASE_ANON_KEY")
            or os.getenv("SUPABASE_PUBLISHABLE_KEY")
            or os.getenv("SUPABASE_KEY")
            or ""
        ).strip()

    @classmethod
    def get_service_role_key(cls) -> str:
        return (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SECRET_KEY") or "").strip()

    @classmethod
    def get_jwt_secret(cls) -> str:
        return os.getenv("SUPABASE_JWT_SECRET", "").strip()

    @classmethod
    def is_configured(cls) -> bool:
        """Return True if Supabase URL and Anon/Publishable Key are configured."""
        return bool(cls.get_url() and cls.get_anon_key())

    @classmethod
    def _headers(cls, access_token: Optional[str] = None) -> Dict[str, str]:
        headers = {
            "apikey": cls.get_anon_key(),
            "Content-Type": "application/json",
        }
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        return headers

    @classmethod
    def sign_in_with_password(cls, email: str, password: str) -> Dict[str, Any]:
        """
        Authenticate user with Supabase Auth using email and password.
        Returns auth session dict with access_token, refresh_token, and user dict.
        """
        if not cls.is_configured():
            raise AuthenticationError("Supabase Auth is not configured.")

        url = f"{cls.get_url()}/auth/v1/token?grant_type=password"
        payload = {
            "email": email.lower().strip(),
            "password": password,
        }

        try:
            resp = requests.post(url, json=payload, headers=cls._headers(), timeout=10)
        except requests.RequestException as e:
            logger.error("Supabase sign-in request failed: %s", e)
            raise AuthenticationError("Authentication service is temporarily unavailable.")

        if resp.status_code != 200:
            data = resp.json() if resp.text else {}
            err_msg = data.get("error_description") or data.get("msg") or data.get("message") or "Invalid email or password."
            logger.info("Supabase sign-in rejected for %s: %s", email, err_msg)
            raise AuthenticationError(err_msg)

        return resp.json()

    @classmethod
    def sign_up(cls, email: str, password: str, name: str = "") -> Dict[str, Any]:
        """Register a new user account with Supabase Auth."""
        if not cls.is_configured():
            raise AuthenticationError("Supabase Auth is not configured.")

        url = f"{cls.get_url()}/auth/v1/signup"
        payload = {
            "email": email.lower().strip(),
            "password": password,
            "data": {"name": name} if name else {},
        }

        try:
            resp = requests.post(url, json=payload, headers=cls._headers(), timeout=2.5)
        except requests.RequestException as e:
            logger.warning("Supabase sign-up request timed out or unavailable: %s", e)
            return {}

        if resp.status_code not in (200, 201):
            data = resp.json() if resp.text else {}
            err_msg = data.get("error_description") or data.get("msg") or data.get("message") or "Registration failed."
            logger.warning("Supabase sign-up response status %s: %s", resp.status_code, err_msg)
            return {}

        return resp.json()

    @classmethod
    def sign_out(cls, access_token: str) -> bool:
        """Revoke user session in Supabase Auth."""
        if not cls.is_configured() or not access_token:
            return True

        url = f"{cls.get_url()}/auth/v1/logout"
        try:
            resp = requests.post(url, headers=cls._headers(access_token), timeout=5)
            return resp.status_code in (200, 204)
        except Exception as e:
            logger.warning("Supabase logout request failed: %s", e)
            return False

    @classmethod
    def reset_password_for_email(cls, email: str, redirect_to: Optional[str] = None) -> bool:
        """Trigger Supabase password recovery email."""
        if not cls.is_configured():
            return False

        url = f"{cls.get_url()}/auth/v1/recover"
        payload = {"email": email.lower().strip()}
        if redirect_to:
            payload["options"] = {"redirectTo": redirect_to}

        try:
            resp = requests.post(url, json=payload, headers=cls._headers(), timeout=10)
            return resp.status_code in (200, 204)
        except Exception as e:
            logger.error("Supabase password recovery failed: %s", e)
            return False

    @classmethod
    def verify_jwt(cls, token: str) -> Dict[str, Any]:
        """
        Verify Supabase JWT token.
        First attempts offline verification via SUPABASE_JWT_SECRET (HS256).
        Falls back to online verification via /auth/v1/user.
        """
        jwt_secret = cls.get_jwt_secret()

        # 1. Fast offline verification if secret is provided
        if jwt_secret:
            try:
                payload = jwt.decode(
                    token,
                    jwt_secret,
                    algorithms=["HS256"],
                    options={"verify_aud": False},
                )
                return payload
            except ExpiredSignatureError:
                raise AuthenticationError("Token has expired.")
            except PyJWTError as e:
                logger.debug("Offline Supabase JWT decode failed: %s", e)

        # 2. Online verification fallback via Supabase Auth API
        if cls.is_configured():
            url = f"{cls.get_url()}/auth/v1/user"
            try:
                resp = requests.get(url, headers=cls._headers(token), timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "sub": data.get("id"),
                        "email": data.get("email"),
                        "aud": data.get("aud", "authenticated"),
                        "role": data.get("role", "authenticated"),
                        "user_metadata": data.get("user_metadata", {}),
                    }
            except Exception as e:
                logger.warning("Online Supabase JWT verification error: %s", e)

        raise AuthenticationError("Invalid or expired Supabase token.")

    @classmethod
    def sync_to_django_user(cls, supabase_user_data: Dict[str, Any]) -> Any:
        """
        Resolve or sync a Supabase user with the local Django accounts.User record.
        Preserves existing user roles, active company, and profile details.
        """
        from apps.accounts.models import User, Role
        from apps.companies.models import Company

        supabase_uid = supabase_user_data.get("id")
        email = (supabase_user_data.get("email") or "").lower().strip()
        metadata = supabase_user_data.get("user_metadata") or {}
        first_last = f"{metadata.get('first_name', '')} {metadata.get('last_name', '')}".strip()
        display_name = (
            metadata.get("name")
            or metadata.get("full_name")
            or first_last
            or email.split("@")[0]
        )

        if not email:
            raise AuthenticationError("Supabase account does not contain a verified email.")

        user = None

        # 1. Match by supabase_uid
        if supabase_uid:
            user = User.objects.select_related("role", "active_company").filter(supabase_uid=supabase_uid).first()

        # 2. Match by email
        if not user:
            user = User.objects.select_related("role", "active_company").filter(email=email).first()
            if user:
                # Link existing user to supabase_uid
                if supabase_uid and user.supabase_uid != supabase_uid:
                    user.supabase_uid = supabase_uid
                    user.save(update_fields=["supabase_uid"])

        # 3. Provision new user if not found
        if not user:
            default_role = Role.objects.filter(name=Role.ROLE_STAFF).first()
            first_company = Company.objects.first()

            user = User.objects.create(
                email=email,
                name=display_name,
                supabase_uid=supabase_uid,
                role=default_role,
                active_company=first_company,
                is_active=True,
                email_verified=True,
            )
            # Set unusable password since authentication is handled via Supabase
            user.set_unusable_password()
            user.save()
            logger.info("Provisioned new Django User (%s) for Supabase UID %s", email, supabase_uid)

        # Ensure active status check
        if not user.is_active:
            raise AuthenticationError("Your account has been deactivated. Please contact an administrator.")

        return user
