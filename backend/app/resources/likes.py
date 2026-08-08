"""Public and authenticated recipe like API resources."""

from flask_restful import Resource

from app.authorization import get_current_authenticated_user, roles_required
from app.models.enums import UserRole
from app.services.likes import (
    RecipeLikeConflictError,
    RecipeLikeNotFoundError,
    RecipeLikeStatusError,
    get_recipe_like_count,
    like_recipe,
    unlike_recipe,
)

_AUTHENTICATED_ROLES = (UserRole.USER, UserRole.MODERATOR, UserRole.ADMIN)


def _current_user():
    """Return the active user after an authentication decorator runs."""
    user = get_current_authenticated_user()
    if user is None:
        return None, ({"message": "Authentication is required."}, 401)
    return user, None


class RecipeLikeResource(Resource):
    """Count, create, or remove likes for one recipe."""

    def get(self, recipe_id: int):
        """Return the public like count for an approved recipe."""
        try:
            count = get_recipe_like_count(recipe_id)
        except RecipeLikeNotFoundError as error:
            return {"message": str(error)}, 404
        except RecipeLikeStatusError:
            return {"message": "Recipe not found."}, 404
        return {"count": count}, 200

    @roles_required(*_AUTHENTICATED_ROLES)
    def post(self, recipe_id: int):
        """Like an approved recipe as the current user."""
        user, error_response = _current_user()
        if error_response:
            return error_response
        try:
            like_recipe(recipe_id, user)
        except RecipeLikeNotFoundError as error:
            return {"message": str(error)}, 404
        except RecipeLikeStatusError as error:
            return {"message": str(error)}, 409
        except RecipeLikeConflictError as error:
            return {"message": str(error)}, 409
        return {"message": "Recipe liked."}, 201

    @roles_required(*_AUTHENTICATED_ROLES)
    def delete(self, recipe_id: int):
        """Remove the current user's like from an approved recipe."""
        user, error_response = _current_user()
        if error_response:
            return error_response
        try:
            unlike_recipe(recipe_id, user)
        except RecipeLikeNotFoundError as error:
            return {"message": str(error)}, 404
        except RecipeLikeStatusError as error:
            return {"message": str(error)}, 409
        return "", 204
