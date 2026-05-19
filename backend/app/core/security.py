# launchkit/backend/app/core/security.py
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError

from app.config import settings

# Argon2id — memory-hard, resistant to GPU attacks
_ph = PasswordHasher(
    time_cost=2,
    memory_cost=65536,
    parallelism=2,
    hash_len=32,
    salt_len=16,
)


def hash_password(plain: str) -> str:
    return _ph.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _ph.verify(hashed, plain)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def needs_rehash(hashed: str) -> bool:
    return _ph.check_needs_rehash(hashed)


# ── JWT ──────────────────────────────────────────────────────────────────────

def create_access_token(
    *,
    user_id: uuid.UUID,
    email: str,
    is_superadmin: bool,
) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "email": email,
        "is_superadmin": is_superadmin,
        "iat": now,
        "exp": expire,
        "jti": str(uuid.uuid4()),  # unique token ID
    }
    return jwt.encode(
        payload,
        settings.private_key,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> dict:
    """
    Returns the decoded payload.
    Raises jwt.PyJWTError subclasses on failure — callers must handle.
    """
    return jwt.decode(
        token,
        settings.public_key,
        algorithms=[settings.JWT_ALGORITHM],
    )


# ── Refresh tokens ────────────────────────────────────────────────────────────

def generate_refresh_token() -> tuple[str, str]:
    """
    Returns (raw_token, token_hash).
    raw_token is sent to the client (httpOnly cookie).
    token_hash is stored in the DB.
    """
    raw = secrets.token_bytes(32)
    raw_hex = raw.hex()
    token_hash = hashlib.sha256(raw).hexdigest()
    return raw_hex, token_hash


def hash_token(raw_hex: str) -> str:
    """Hash a raw hex token for DB lookup."""
    return hashlib.sha256(bytes.fromhex(raw_hex)).hexdigest()