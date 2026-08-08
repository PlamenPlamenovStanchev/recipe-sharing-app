"""Validation and safe serialization for admin-managed users."""

from marshmallow import Schema, fields

from app.models.enums import UserRole
from app.schemas.users import (
    UserOutputSchema,
    validate_registration_password,
)
from app.validators import validate_non_whitespace, validate_username


class AdminUserOutputSchema(UserOutputSchema):
    """Serialize account administration fields without protected values."""

    updated_at = fields.DateTime(dump_only=True)


class AdminUserCreateSchema(Schema):
    """Validate the explicitly supported admin account creation fields."""

    email = fields.Email(required=True)
    username = fields.String(required=True, validate=validate_username)
    password = fields.String(
        required=True,
        load_only=True,
        validate=validate_registration_password,
    )
    first_name = fields.String(required=True, validate=validate_non_whitespace)
    last_name = fields.String(required=True, validate=validate_non_whitespace)
    role = fields.Enum(UserRole, by_value=True, required=True)
    is_active = fields.Boolean(load_default=True)


class AdminUserUpdateSchema(Schema):
    """Validate only fields administrators may change after creation."""

    email = fields.Email()
    username = fields.String(validate=validate_username)
    first_name = fields.String(validate=validate_non_whitespace)
    last_name = fields.String(validate=validate_non_whitespace)
    role = fields.Enum(UserRole, by_value=True)
    is_active = fields.Boolean()
