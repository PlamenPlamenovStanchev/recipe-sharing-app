"""Public and authenticated comment API resources."""

from flask import request
from flask_jwt_extended import verify_jwt_in_request
from flask_restful import Resource
from marshmallow import ValidationError

from app.authorization import get_current_authenticated_user, roles_required
from app.models.enums import UserRole
from app.schemas.comments import CommentInputSchema, CommentOutputSchema
from app.services.comments import (
    CommentNotFoundError,
    CommentPermissionError,
    CommentRecipeStatusError,
    create_comment,
    delete_comment,
    get_comments_for_recipe,
    update_comment,
)

_AUTHENTICATED_ROLES = (UserRole.USER, UserRole.MODERATOR, UserRole.ADMIN)


def _load_input():
    """Load comment JSON or return the standard validation response."""
    try:
        return (
            CommentInputSchema().load(request.get_json(silent=True) or {}),
            None,
        )
    except ValidationError as error:
        return None, (
            {"message": "Validation failed.", "errors": error.messages},
            400,
        )


def _current_user():
    """Return the active user after an authentication decorator runs."""
    user = get_current_authenticated_user()
    if user is None:
        return None, ({"message": "Authentication is required."}, 401)
    return user, None


class RecipeCommentListResource(Resource):
    """List or create comments belonging to one recipe."""

    def get(self, recipe_id: int):
        """Return active recipe comments in oldest-first order."""
        verify_jwt_in_request(optional=True)
        try:
            comments = get_comments_for_recipe(
                recipe_id, get_current_authenticated_user()
            )
        except CommentNotFoundError:
            return {"message": "Recipe not found."}, 404
        return CommentOutputSchema(many=True).dump(comments), 200

    @roles_required(*_AUTHENTICATED_ROLES)
    def post(self, recipe_id: int):
        """Create a comment by the current user on an approved recipe."""
        data, error_response = _load_input()
        if error_response:
            return error_response
        user, error_response = _current_user()
        if error_response:
            return error_response
        try:
            comment = create_comment(recipe_id, user, data["content"])
        except CommentNotFoundError:
            return {"message": "Recipe not found."}, 404
        except CommentRecipeStatusError as error:
            return {"message": str(error)}, 409
        return CommentOutputSchema().dump(comment), 201


class CommentDetailResource(Resource):
    """Update or soft-delete an individual comment."""

    @roles_required(*_AUTHENTICATED_ROLES)
    def put(self, comment_id: int):
        """Replace comment content when ownership or role permits."""
        data, error_response = _load_input()
        if error_response:
            return error_response
        user, error_response = _current_user()
        if error_response:
            return error_response
        try:
            comment = update_comment(comment_id, user, data["content"])
        except CommentNotFoundError:
            return {"message": "Comment not found."}, 404
        except CommentPermissionError:
            return {"message": "Insufficient permissions."}, 403
        return CommentOutputSchema().dump(comment), 200

    @roles_required(*_AUTHENTICATED_ROLES)
    def delete(self, comment_id: int):
        """Soft-delete a comment when ownership or role permits."""
        user, error_response = _current_user()
        if error_response:
            return error_response
        try:
            delete_comment(comment_id, user)
        except CommentNotFoundError:
            return {"message": "Comment not found."}, 404
        except CommentPermissionError:
            return {"message": "Insufficient permissions."}, 403
        return "", 204
