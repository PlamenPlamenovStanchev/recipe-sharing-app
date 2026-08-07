"""Schemas for user registration, authentication, and representation."""

from marshmallow import Schema, ValidationError, fields

from app.models.enums import UserRole
from app.validators import (
    PasswordValidationError,
    validate_password,
    validate_username,
)


def validate_registration_password(password: str) -> None:
    """Adapt the existing password policy to Marshmallow validation errors."""
    try:
        validate_password(password)
    except PasswordValidationError as error:
        raise ValidationError(str(error)) from error


class UserRegistrationSchema(Schema):
    """Validate the data required to create a user account."""

    email = fields.Email(required=True)
    username = fields.String(required=True, validate=validate_username)
    password = fields.String(
        required=True,
        load_only=True,
        validate=validate_registration_password,
    )
    first_name = fields.String(required=True)
    last_name = fields.String(required=True)


class UserOutputSchema(Schema):
    """Serialize public user data without credential fields."""

    id = fields.Integer(dump_only=True)
    email = fields.Email(dump_only=True)
    username = fields.String(dump_only=True)
    first_name = fields.String(dump_only=True, allow_none=True)
    last_name = fields.String(dump_only=True, allow_none=True)
    role = fields.Enum(UserRole, by_value=True, dump_only=True)
    is_active = fields.Boolean(dump_only=True)
    created_at = fields.DateTime(dump_only=True)


class LoginSchema(Schema):
    """Validate credentials submitted for login."""

    email = fields.Email(required=True)
    password = fields.String(required=True, load_only=True)
