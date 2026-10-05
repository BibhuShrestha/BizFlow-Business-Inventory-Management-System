"""
Password hashers for Werkzeug compatibility.

Enables seamless migration of user passwords created in Flask (Werkzeug PBKDF2/scrypt)
to Django. When a user with a legacy Werkzeug hash logs in, Django will verify the hash
and automatically upgrade it to Django's default hasher (PBKDF2/Argon2).
"""
from django.contrib.auth.hashers import BasePasswordHasher
from werkzeug.security import check_password_hash, generate_password_hash


class WerkzeugPasswordHasher(BasePasswordHasher):
    """Default Werkzeug hasher verifying pbkdf2 and scrypt."""

    algorithm = "pbkdf2:sha256"

    def verify(self, password: str, encoded: str) -> bool:
        try:
            return check_password_hash(encoded, password)
        except Exception:
            return False

    def encode(self, password: str, salt: str) -> str:
        return generate_password_hash(password)

    def safe_summary(self, encoded: str) -> dict:
        return {
            "algorithm": self.algorithm,
            "hash": encoded[:12] + "...",
        }


class WerkzeugScryptPasswordHasher(BasePasswordHasher):
    """Werkzeug 3.x scrypt hasher (scrypt:32768:8:1)."""

    algorithm = "scrypt:32768:8:1"

    def verify(self, password: str, encoded: str) -> bool:
        try:
            return check_password_hash(encoded, password)
        except Exception:
            return False

    def encode(self, password: str, salt: str) -> str:
        return generate_password_hash(password, method="scrypt")

    def safe_summary(self, encoded: str) -> dict:
        return {
            "algorithm": self.algorithm,
            "hash": encoded[:12] + "...",
        }


class WerkzeugPbkdf2_260000Hasher(BasePasswordHasher):
    """Werkzeug pbkdf2 with 260000 iterations."""

    algorithm = "pbkdf2:sha256:260000"

    def verify(self, password: str, encoded: str) -> bool:
        try:
            return check_password_hash(encoded, password)
        except Exception:
            return False

    def encode(self, password: str, salt: str) -> str:
        return generate_password_hash(password)

    def safe_summary(self, encoded: str) -> dict:
        return {
            "algorithm": self.algorithm,
            "hash": encoded[:12] + "...",
        }


class WerkzeugPbkdf2_600000Hasher(BasePasswordHasher):
    """Werkzeug pbkdf2 with 600000 iterations."""

    algorithm = "pbkdf2:sha256:600000"

    def verify(self, password: str, encoded: str) -> bool:
        try:
            return check_password_hash(encoded, password)
        except Exception:
            return False

    def encode(self, password: str, salt: str) -> str:
        return generate_password_hash(password)

    def safe_summary(self, encoded: str) -> dict:
        return {
            "algorithm": self.algorithm,
            "hash": encoded[:12] + "...",
        }
