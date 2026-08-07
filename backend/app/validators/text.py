"""Validation rules for required human-readable text."""

from marshmallow import ValidationError


def validate_non_whitespace(value: str) -> None:
    """Reject strings that contain no non-whitespace characters."""
    if not value.strip():
        raise ValidationError("Field cannot contain only whitespace.")
