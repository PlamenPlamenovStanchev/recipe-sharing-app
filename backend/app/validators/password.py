"""Password policy validation."""

import re


class PasswordValidationError(ValueError):
    """Raised when a password does not meet the required policy."""


def validate_password(password: str) -> None:
    """Validate a password without persisting or exposing its contents."""
    if not isinstance(password, str) or not password:
        raise PasswordValidationError("Password is required.")

    errors: list[str] = []

    if len(password) < 8:
        errors.append("Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter.")
    if not re.search(r"\d", password):
        errors.append("Password must contain at least one digit.")

    if errors:
        raise PasswordValidationError(" ".join(errors))
