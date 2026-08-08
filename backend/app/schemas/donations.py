"""Marshmallow schemas for recipe donations."""

from decimal import Decimal

from marshmallow import Schema, ValidationError, fields, pre_load, validates

from app.models.enums import DonationStatus


class StringDecimal(fields.Decimal):
    """Accept decimal values only from JSON strings, never binary floats."""

    def _deserialize(self, value, attr, data, **kwargs):
        if not isinstance(value, str):
            raise ValidationError("Amount must be provided as a string.")
        return super()._deserialize(value, attr, data, **kwargs)


class DonationInputSchema(Schema):
    """Validate a new EUR donation request."""

    amount = StringDecimal(required=True, allow_nan=False, as_string=True)
    currency = fields.String(required=True)

    @pre_load
    def normalize_currency(self, data: dict, **kwargs) -> dict:
        """Normalize a supplied currency code before validation."""
        if isinstance(data, dict) and isinstance(data.get("currency"), str):
            return {**data, "currency": data["currency"].strip().upper()}
        return data

    @validates("amount")
    def validate_amount(self, value: Decimal, **kwargs) -> None:
        """Require a positive amount representable by Numeric(12, 2)."""
        if value <= Decimal("0"):
            raise ValidationError("Amount must be positive.")
        if value.as_tuple().exponent < -2:
            raise ValidationError("Amount may have at most 2 decimal places.")
        if value > Decimal("9999999999.99"):
            raise ValidationError("Amount is too large.")

    @validates("currency")
    def validate_currency(self, value: str, **kwargs) -> None:
        """Restrict the initial implementation to EUR."""
        if value != "EUR":
            raise ValidationError("Only EUR donations are supported.")


class DonationOutputSchema(Schema):
    """Serialize donation state without provider credentials or internals."""

    id = fields.Integer(dump_only=True)
    recipe_id = fields.Integer(dump_only=True)
    donor_id = fields.Integer(dump_only=True)
    recipient_id = fields.Integer(dump_only=True)
    amount = fields.Decimal(as_string=True, dump_only=True)
    currency = fields.String(dump_only=True)
    status = fields.Enum(DonationStatus, by_value=True, dump_only=True)
    wise_transfer_id = fields.String(dump_only=True, allow_none=True)
    idempotency_key = fields.String(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    completed_at = fields.DateTime(dump_only=True, allow_none=True)
