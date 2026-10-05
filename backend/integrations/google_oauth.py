"""
Google OAuth 2.0 Integration.

Handles social login token validation and user profile retrieval.
"""
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class GoogleOAuthClient:
    """Google OAuth2 token and profile helper."""

    @classmethod
    def get_auth_url(cls, redirect_uri: str, state: str) -> str:
        """Generate Google OAuth authorization URL."""
        client_id = settings.GOOGLE_CLIENT_ID
        return (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={client_id}&"
            f"redirect_uri={redirect_uri}&"
            f"response_type=code&"
            f"scope=openid%20email%20profile&"
            f"state={state}&"
            f"access_type=offline"
        )