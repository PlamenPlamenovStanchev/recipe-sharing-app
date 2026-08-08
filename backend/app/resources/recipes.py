"""Public and authenticated recipe API resources."""

from flask import request
from flask_jwt_extended import verify_jwt_in_request
from flask_restful import Resource
from marshmallow import ValidationError

from app.authorization import get_current_authenticated_user, roles_required
from app.models.enums import RecipeStatus, UserRole
from app.repositories import get_recipe, list_approved_recipes
from app.schemas import (
    RecipeInputSchema,
    RecipeRejectionSchema,
)
from app.services.recipe_serialization import (
    serialize_recipe,
    serialize_recipes,
)
from app.services.recipes import (
    RecipeConflictError,
    RecipePermissionError,
    RecipeTransitionError,
    RecipeValidationError,
    approve_recipe,
    create_recipe,
    delete_recipe,
    reject_recipe,
    submit_recipe,
    update_recipe,
)

_AUTHENTICATED_ROLES = (UserRole.USER, UserRole.MODERATOR, UserRole.ADMIN)


def _validation_error(error: ValidationError) -> tuple[dict, int]:
    """Return a consistent response for Marshmallow validation failures."""
    return {"message": "Validation failed.", "errors": error.messages}, 400


def _not_found() -> tuple[dict[str, str], int]:
    """Return the standard response for unavailable recipes."""
    return {"message": "Recipe not found."}, 404


def _active_user_or_error():
    """Return the active user after an authentication decorator runs."""
    user = get_current_authenticated_user()
    if user is None:
        return None, ({"message": "Authentication is required."}, 401)
    return user, None


def _can_view(recipe, user) -> bool:
    """Return whether a public or authenticated viewer may see a recipe."""
    if recipe.status == RecipeStatus.APPROVED:
        return True
    if user is None:
        return False
    return recipe.author_id == user.id or user.role in {
        UserRole.MODERATOR,
        UserRole.ADMIN,
    }


class RecipeListResource(Resource):
    """List public recipes or create a recipe for the current user."""

    def get(self):
        """Return approved recipes ordered newest first."""
        return serialize_recipes(list_approved_recipes()), 200

    @roles_required(*_AUTHENTICATED_ROLES)
    def post(self):
        """Create a draft recipe owned by the current authenticated user."""
        try:
            recipe_data = RecipeInputSchema().load(
                request.get_json(silent=True) or {}
            )
        except ValidationError as error:
            return _validation_error(error)

        user, error_response = _active_user_or_error()
        if error_response:
            return error_response
        try:
            recipe = create_recipe(user, recipe_data)
        except RecipeValidationError as error:
            return {"message": str(error)}, 400
        except RecipeConflictError as error:
            return {"message": str(error)}, 409

        return serialize_recipe(recipe), 201


class RecipeDetailResource(Resource):
    """Read, update, or delete an individual recipe."""

    def get(self, recipe_id: int):
        """Return a recipe when its current visibility permits access."""
        verify_jwt_in_request(optional=True)
        user = get_current_authenticated_user()
        recipe = get_recipe(
            recipe_id,
            current_user_id=user.id if user is not None else None,
        )
        if recipe is None:
            return _not_found()
        if not _can_view(recipe, user):
            return _not_found()
        excluded_fields = (
            () if user is not None else ("liked_by_current_user",)
        )
        return serialize_recipes([recipe], exclude=excluded_fields)[0], 200

    @roles_required(*_AUTHENTICATED_ROLES)
    def put(self, recipe_id: int):
        """Partially update a recipe subject to current role permissions."""
        recipe = get_recipe(recipe_id)
        if recipe is None:
            return _not_found()
        try:
            recipe_data = RecipeInputSchema(partial=True).load(
                request.get_json(silent=True) or {}
            )
        except ValidationError as error:
            return _validation_error(error)

        user, error_response = _active_user_or_error()
        if error_response:
            return error_response
        try:
            recipe = update_recipe(recipe, user, recipe_data)
        except RecipePermissionError:
            return {"message": "Insufficient permissions."}, 403
        except RecipeValidationError as error:
            return {"message": str(error)}, 400
        except RecipeConflictError as error:
            return {"message": str(error)}, 409

        return serialize_recipe(recipe), 200

    @roles_required(*_AUTHENTICATED_ROLES)
    def delete(self, recipe_id: int):
        """Delete a recipe when the current user has permission."""
        recipe = get_recipe(recipe_id)
        if recipe is None:
            return _not_found()
        user, error_response = _active_user_or_error()
        if error_response:
            return error_response
        try:
            delete_recipe(recipe, user)
        except RecipePermissionError:
            return {"message": "Insufficient permissions."}, 403
        except RecipeConflictError as error:
            return {"message": str(error)}, 409

        return "", 204


class RecipeSubmitResource(Resource):
    """Submit an author's recipe for moderation."""

    @roles_required(*_AUTHENTICATED_ROLES)
    def post(self, recipe_id: int):
        """Move an eligible recipe to the pending moderation state."""
        recipe = get_recipe(recipe_id)
        if recipe is None:
            return _not_found()
        user, error_response = _active_user_or_error()
        if error_response:
            return error_response
        try:
            recipe = submit_recipe(recipe, user)
        except RecipePermissionError:
            return {"message": "Insufficient permissions."}, 403
        except RecipeTransitionError as error:
            return {"message": str(error)}, 409

        return serialize_recipe(recipe), 200


class RecipeApproveResource(Resource):
    """Approve pending recipes as moderation staff."""

    @roles_required(UserRole.MODERATOR, UserRole.ADMIN)
    def post(self, recipe_id: int):
        """Approve a pending recipe using the current staff member."""
        recipe = get_recipe(recipe_id)
        if recipe is None:
            return _not_found()
        user, error_response = _active_user_or_error()
        if error_response:
            return error_response
        try:
            recipe = approve_recipe(recipe, user)
        except RecipePermissionError:
            return {"message": "Insufficient permissions."}, 403
        except RecipeTransitionError as error:
            return {"message": str(error)}, 409

        return serialize_recipe(recipe), 200


class RecipeRejectResource(Resource):
    """Reject pending recipes as moderation staff."""

    @roles_required(UserRole.MODERATOR, UserRole.ADMIN)
    def post(self, recipe_id: int):
        """Reject a pending recipe with a validated moderation reason."""
        recipe = get_recipe(recipe_id)
        if recipe is None:
            return _not_found()
        try:
            rejection_data = RecipeRejectionSchema().load(
                request.get_json(silent=True) or {}
            )
        except ValidationError as error:
            return _validation_error(error)

        user, error_response = _active_user_or_error()
        if error_response:
            return error_response
        try:
            recipe = reject_recipe(recipe, user, rejection_data["reason"])
        except RecipePermissionError:
            return {"message": "Insufficient permissions."}, 403
        except RecipeTransitionError as error:
            return {"message": str(error)}, 409

        return serialize_recipe(recipe), 200
