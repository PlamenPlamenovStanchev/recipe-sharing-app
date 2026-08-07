"""Argon2 password hashing service."""

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.validators.password import validate_password


_password_hasher = PasswordHasher()


def hash_password(plain_password: str) -> str:
    """Validate and hash a password with Argon2id."""
    validate_password(plain_password)
    return _password_hasher.hash(plain_password)


def verify_password(password_hash: str, plain_password: str) -> bool:
    """Return whether a plaintext password matches an Argon2 hash."""
    if not isinstance(password_hash, str) or not isinstance(
        plain_password,
        str,
    ):
        return False

    try:
        return _password_hasher.verify(password_hash, plain_password)
    except (InvalidHashError, VerificationError):
        return False


def password_needs_rehash(password_hash: str) -> bool:
    """Return whether a valid stored hash needs the current parameters."""
    if not isinstance(password_hash, str):
        return False

    try:
        return _password_hasher.check_needs_rehash(password_hash)
    except (InvalidHashError, VerificationError):
        return False
