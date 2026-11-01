import string
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional

BASE62_ALPHABET = string.digits + string.ascii_letters  # 62 chars


def generate_short_code(length: int = 7) -> str:
    """
    Generate a cryptographically secure random alphanumeric code.
    7 characters in Base62 yield 62^7 (~3.52 trillion) unique possibilities.
    """
    return "".join(secrets.choice(BASE62_ALPHABET) for _ in range(length))


def compute_expiration(days: Optional[int]) -> Optional[datetime]:
    """Compute expiration timestamp given duration in days."""
    if days is None:
        return None
    return datetime.now(timezone.utc) + timedelta(days=days)


def is_url_expired(expires_at: Optional[datetime]) -> bool:
    """Check if an expiration timestamp has elapsed."""
    if expires_at is None:
        return False
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) > expires_at
