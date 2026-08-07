"""Validation rules for user-facing usernames."""

import re

from marshmallow import ValidationError

_USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]+$")


def validate_username(username: str) -> None:
    """Require a 3-30 character username made of safe identifier characters."""
    if not 3 <= len(username) <= 30:
        raise ValidationError("Username must be between 3 and 30 characters.")
    if not _USERNAME_PATTERN.fullmatch(username):
        raise ValidationError(
            "Username may contain only letters, numbers, and underscores."
        )
