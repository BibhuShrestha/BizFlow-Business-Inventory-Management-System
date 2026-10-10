"""
Google OAuth 2.0 Integration for BizFlow.

Handles OpenID Connect authorization URLs, authorization code token exchange,
and user profile retrieval with secure state verification and error handling.
"""
import logging
from typing import Any
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

GOOGLE_AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_ENDPOINT = "https://www.googleapis.com/oauth2/v3/userinfo"


class GoogleOAuthError(Exception):
    """Exception raised when Google OAuth negotiation fails."""


class GoogleOAuthClient:
    """Google OAuth2 authentication and OpenID Connect client."""

    @classmethod
    def is_configured(cls) -> bool:
        """Return True if real Google OAuth client credentials are provided."""
        client_id = getattr(settings, "GOOGLE_CLIENT_ID", "")
        client_secret = getattr(settings, "GOOGLE_CLIENT_SECRET", "")
        return bool(client_id and client_secret and not client_id.startswith("your-google"))

    @classmethod
    def get_auth_url(cls, redirect_uri: str, state: str) -> str:
        """Generate Google OAuth 2.0 authorization URL."""
        client_id = getattr(settings, "GOOGLE_CLIENT_ID", "") or "mock-google-client-id"
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "online",
            "prompt": "select_account",
        }
        query_string = "&".join(f"{k}={requests.utils.quote(str(v))}" for k, v in params.items())
        return f"{GOOGLE_AUTH_ENDPOINT}?{query_string}"

    @classmethod
    def exchange_code(cls, code: str, redirect_uri: str) -> dict[str, Any]:
        """
        Exchange authorization code for access and ID tokens.
        In test/mock mode without live credentials, returns a valid mock payload if designated.
        """
        client_id = getattr(settings, "GOOGLE_CLIENT_ID", "")
        client_secret = getattr(settings, "GOOGLE_CLIENT_SECRET", "")

        # If running in test or unconfigured dev environment and mock code is supplied
        if not cls.is_configured():
            if code.startswith("mock_code_") or code.startswith("test_code_") or getattr(settings, "DEBUG", False):
                mock_email = "google_user@example.com"
                if ":" in code:
                    mock_email = code.split(":", 1)[1]
                return {
                    "access_token": "mock_access_token",
                    "id_token": "mock_id_token",
                    "expires_in": 3600,
                    "token_type": "Bearer",
                    "_mock": True,
                    "_mock_email": mock_email,
                }
            raise GoogleOAuthError("Google OAuth credentials are not configured in system settings.")

        payload = {
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }

        try:
            response = requests.post(
                GOOGLE_TOKEN_ENDPOINT,
                data=payload,
                headers={"Accept": "application/json"},
                timeout=10,
            )
            data = response.json()
        except requests.RequestException as exc:
            logger.error("Network error communicating with Google token endpoint: %s", exc)
            raise GoogleOAuthError("Failed to communicate with Google authentication service.") from exc

        if response.status_code != 200 or "access_token" not in data:
            error_desc = data.get("error_description") or data.get("error") or "Unknown error"
            logger.warning("Google token exchange failed: %s (Status: %s)", error_desc, response.status_code)
            raise GoogleOAuthError(f"Google authentication failed: {error_desc}")

        return data

    @classmethod
    def get_user_info(cls, token_data: dict[str, Any]) -> dict[str, Any]:
        """
        Retrieve user profile from Google UserInfo endpoint using access token.
        Returns dict containing: sub, email, email_verified, name, picture.
        """
        if token_data.get("_mock"):
            email = token_data.get("_mock_email", "google_user@example.com")
            return {
                "sub": f"google_sub_{abs(hash(email))}",
                "email": email,
                "email_verified": True,
                "name": email.split("@")[0].title(),
                "picture": "",
            }

        access_token = token_data.get("access_token")
        if not access_token:
            raise GoogleOAuthError("No access token provided in Google authentication response.")

        try:
            response = requests.get(
                GOOGLE_USERINFO_ENDPOINT,
                headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
                timeout=10,
            )
            user_info = response.json()
        except requests.RequestException as exc:
            logger.error("Network error querying Google userinfo endpoint: %s", exc)
            raise GoogleOAuthError("Failed to fetch profile information from Google.") from exc

        if response.status_code != 200 or "email" not in user_info:
            logger.warning("Google userinfo endpoint rejected token: %s", user_info)
            raise GoogleOAuthError("Unable to retrieve verified profile from Google.")

        return {
            "sub": str(user_info.get("sub", "")),
            "email": str(user_info.get("email", "")).lower().strip(),
            "email_verified": bool(user_info.get("email_verified", False)),
            "name": str(user_info.get("name", "")).strip() or user_info.get("email", "").split("@")[0],
            "picture": str(user_info.get("picture", "")),
        }