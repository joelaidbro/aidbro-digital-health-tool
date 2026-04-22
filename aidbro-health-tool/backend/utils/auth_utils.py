"""
Auth Utilities
==============
JWT token creation/verification, password hashing,
and random password generation.
"""

import hashlib
import hmac
import os
import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt

try:
    import bcrypt
except ModuleNotFoundError:  # pragma: no cover - depends on local env
    bcrypt = None

# Config
JWT_SECRET = os.getenv("JWT_SECRET", "changeme_use_a_long_random_string")
ADMIN_JWT_SECRET = os.getenv("ADMIN_JWT_SECRET", "changeme_admin_secret")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE = int(os.getenv("JWT_EXPIRES_DAYS", "7"))
REFRESH_TOKEN_EXPIRE = 30
PBKDF2_PREFIX = "pbkdf2_sha256"
PBKDF2_ITERATIONS = int(os.getenv("PASSWORD_HASH_ITERATIONS", "390000"))


def _hash_pbkdf2(password: str, salt: bytes, iterations: int) -> str:
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return digest.hex()


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = _hash_pbkdf2(password, salt, PBKDF2_ITERATIONS)
    return f"{PBKDF2_PREFIX}${PBKDF2_ITERATIONS}${salt.hex()}${digest}"


def verify_password(plain: str, hashed: str) -> bool:
    if not hashed:
        return False

    if hashed.startswith(f"{PBKDF2_PREFIX}$"):
        try:
            _, iterations_raw, salt_hex, digest_hex = hashed.split("$", 3)
            iterations = int(iterations_raw)
            expected = _hash_pbkdf2(plain, bytes.fromhex(salt_hex), iterations)
            return hmac.compare_digest(expected, digest_hex)
        except (TypeError, ValueError):
            return False

    # Legacy bcrypt support for existing hashes created before the migration.
    if hashed.startswith("$2"):
        if bcrypt is None:
            return False
        try:
            return bcrypt.checkpw(
                plain.encode("utf-8")[:72],
                hashed.encode("utf-8"),
            )
        except ValueError:
            return False

    return False


def generate_random_password(length: int = 12) -> str:
    """Generate a secure random password."""
    alphabet = string.ascii_letters + string.digits + "!@#$%"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def create_access_token(
    subject: str,
    role: str = "client",
    expires_days: int = ACCESS_TOKEN_EXPIRE,
) -> str:
    """
    Create a JWT access token.
    subject: user email or id
    role:    'client' | 'super_admin' | 'manager' | 'analyst' | 'admin'
    """
    secret = ADMIN_JWT_SECRET if role in ("super_admin", "admin", "manager", "analyst") else JWT_SECRET
    payload = {
        "sub": subject,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(days=expires_days),
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }
    return jwt.encode(payload, secret, algorithm=JWT_ALGORITHM)


def create_refresh_token(subject: str, role: str = "client") -> str:
    secret = ADMIN_JWT_SECRET if role in ("super_admin", "admin", "manager", "analyst") else JWT_SECRET
    payload = {
        "sub": subject,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE),
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
    }
    return jwt.encode(payload, secret, algorithm=JWT_ALGORITHM)


def decode_token(token: str, is_admin: bool = False) -> Optional[dict]:
    """
    Decode and validate a JWT token.
    Returns payload dict or None if invalid/expired.
    """
    secret = ADMIN_JWT_SECRET if is_admin else JWT_SECRET
    try:
        payload = jwt.decode(token, secret, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        try:
            other = JWT_SECRET if is_admin else ADMIN_JWT_SECRET
            payload = jwt.decode(token, other, algorithms=[JWT_ALGORITHM])
            return payload
        except JWTError:
            return None


def get_token_subject(token: str) -> Optional[str]:
    payload = decode_token(token)
    if payload:
        return payload.get("sub")
    return None
