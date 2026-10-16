"""
Shared application configuration.

Both Django and FastAPI read from the same environment variables. Django reads
them via django-environ in config/settings/base.py. FastAPI (and any standalone
scripts) use this Settings class for type-safe access.

Usage:
    from core.config import settings
    print(settings.JWT_SECRET_KEY)
"""
import os
from pathlib import Path

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:
    from pydantic import BaseModel

    class SettingsConfigDict(dict):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)

    class BaseSettings(BaseModel):
        def __init__(self, **data):
            init_kwargs = {}
            for field_name, field in self.__class__.model_fields.items():
                env_val = os.getenv(field_name)
                if env_val is not None:
                    if field.annotation is int:
                        try:
                            init_kwargs[field_name] = int(env_val)
                        except ValueError:
                            pass
                    elif field.annotation is bool:
                        init_kwargs[field_name] = env_val.lower() in ("true", "1", "yes")
                    else:
                        init_kwargs[field_name] = env_val
            init_kwargs.update(data)
            super().__init__(**init_kwargs)


_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_ENV_FILE = str(_REPO_ROOT / ".env") if (_REPO_ROOT / ".env").exists() else ".env"

class Settings(BaseSettings):
    """Centralised settings model. Values are loaded from .env automatically."""

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Django
    DJANGO_SECRET_KEY: str = "change-this-in-production"
    DJANGO_SETTINGS_MODULE: str = "config.settings.development"
    DJANGO_DEBUG: bool = False

    # Database
    DATABASE_URL: str = ""
    MYSQL_USER: str = ""
    MYSQL_PASSWORD: str = ""
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_DATABASE: str = "inventory_db"

    # JWT (FastAPI)
    JWT_SECRET_KEY: str = "change-this-jwt-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 14

    # Email
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_PORT: int = 587
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_USE_TLS: bool = True
    MAIL_DEFAULT_SENDER: str = "noreply@inventory.com"

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = ""

    # AI (future)
    AI_API_KEY: str = ""


# Singleton - import this in FastAPI code instead of instantiating directly.
settings = Settings()
