"""Schemas for recipe input and API representations."""

from marshmallow import Schema, fields, validate

from app.models.enums import RecipeStatus
from app.schemas.users import UserOutputSchema
from app.validators import validate_non_whitespace, validate_recipe_title


class RecipeIngredientInputSchema(Schema):
    """Validate one ingredient used by a recipe."""

    name = fields.String(required=True, validate=validate_non_whitespace)
    quantity = fields.String(allow_none=True)
    unit = fields.String(allow_none=True)
    position = fields.Integer(required=True, validate=validate.Range(min=1))
    notes = fields.String(allow_none=True)


class RecipeStepInputSchema(Schema):
    """Validate one ordered recipe instruction."""

    step_number = fields.Integer(required=True, validate=validate.Range(min=1))
    instruction = fields.String(
        required=True,
        validate=validate_non_whitespace,
    )


class RecipeInputSchema(Schema):
    """Validate recipe creation data; pass ``partial=True`` for updates."""

    title = fields.String(required=True, validate=validate_recipe_title)
    description = fields.String(
        required=True,
        validate=validate_non_whitespace,
    )
    ingredients = fields.List(
        fields.Nested(RecipeIngredientInputSchema),
        required=True,
        validate=validate.Length(min=1),
    )
    steps = fields.List(
        fields.Nested(RecipeStepInputSchema),
        required=True,
        validate=validate.Length(min=1),
    )


class RecipeRejectionSchema(Schema):
    """Validate the reason supplied when rejecting a pending recipe."""

    reason = fields.String(
        required=True,
        validate=[
            validate.Length(min=5, max=500),
            validate_non_whitespace,
        ],
    )


class RecipeIngredientOutputSchema(Schema):
    """Serialize an ingredient as it appears in a recipe."""

    name = fields.String(attribute="ingredient.name", dump_only=True)
    quantity = fields.String(dump_only=True, allow_none=True)
    unit = fields.String(dump_only=True, allow_none=True)
    position = fields.Integer(dump_only=True)
    notes = fields.String(dump_only=True, allow_none=True)


class RecipeStepOutputSchema(Schema):
    """Serialize a recipe instruction."""

    step_number = fields.Integer(dump_only=True)
    instruction = fields.String(dump_only=True)


class RecipeOutputSchema(Schema):
    """Serialize recipe data for API responses."""

    id = fields.Integer(dump_only=True)
    title = fields.String(dump_only=True)
    slug = fields.String(dump_only=True)
    description = fields.String(dump_only=True, allow_none=True)
    status = fields.Enum(RecipeStatus, by_value=True, dump_only=True)
    author = fields.Nested(UserOutputSchema, dump_only=True)
    ingredients = fields.List(
        fields.Nested(RecipeIngredientOutputSchema),
        attribute="recipe_ingredients",
        dump_only=True,
    )
    steps = fields.List(fields.Nested(RecipeStepOutputSchema), dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    approved_at = fields.DateTime(dump_only=True, allow_none=True)
