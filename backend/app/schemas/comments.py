"""Schemas for recipe comment input and API representations."""

from marshmallow import Schema, fields, pre_load, validate


class CommentInputSchema(Schema):
    """Validate and normalize comment content."""

    content = fields.String(
        required=True,
        validate=validate.Length(min=2, max=1000),
    )

    @pre_load
    def strip_content(self, data: dict, **kwargs) -> dict:
        """Strip surrounding whitespace before length validation."""
        if isinstance(data, dict) and isinstance(data.get("content"), str):
            return {**data, "content": data["content"].strip()}
        return data


class CommentAuthorOutputSchema(Schema):
    """Serialize the basic public identity of a comment author."""

    id = fields.Integer(dump_only=True)
    username = fields.String(dump_only=True)
    first_name = fields.String(dump_only=True, allow_none=True)
    last_name = fields.String(dump_only=True, allow_none=True)


class CommentOutputSchema(Schema):
    """Serialize a non-deleted recipe comment."""

    id = fields.Integer(dump_only=True)
    content = fields.String(dump_only=True)
    recipe_id = fields.Integer(dump_only=True)
    author = fields.Nested(
        CommentAuthorOutputSchema,
        attribute="user",
        dump_only=True,
    )
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
