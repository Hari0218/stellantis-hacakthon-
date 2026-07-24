"""Shared authentication utilities used by multiple services."""
import hashlib
import hmac
import time
from typing import Optional


SECRET_KEY = "autoshop-dev-secret-key-not-for-production"
TOKEN_EXPIRY_SECONDS = 3600


def hash_password(password: str) -> str:
    """Hash a password using SHA-256 with a fixed salt (demo only)."""
    return hashlib.sha256(f"{SECRET_KEY}:{password}".encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a stored hash."""
    return hash_password(plain_password) == hashed_password


def create_token(user_id: int, role: str) -> str:
    """Create a simple HMAC-signed token (demo, not JWT)."""
    payload = f"{user_id}:{role}:{int(time.time()) + TOKEN_EXPIRY_SECONDS}"
    signature = hmac.new(SECRET_KEY.encode(), payload.encode(), "sha256").hexdigest()
    return f"{payload}:{signature}"


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a token. Returns user info dict or None."""
    try:
        parts = token.split(":")
        if len(parts) != 4:
            return None
        user_id, role, expiry, signature = parts
        payload = f"{user_id}:{role}:{expiry}"
        expected_sig = hmac.new(SECRET_KEY.encode(), payload.encode(), "sha256").hexdigest()
        if not hmac.compare_digest(signature, expected_sig):
            return None
        if int(expiry) < int(time.time()):
            return None
        return {"user_id": int(user_id), "role": role}
    except Exception:
        return None


def require_role(token: str, required_role: str) -> bool:
    """Check if a token has a specific role."""
    info = decode_token(token)
    if info is None:
        return False
    return info["role"] == required_role or info["role"] == "admin"
