"""Authenticated recipe image upload resource."""

from flask import request
from flask_restful import Resource

from app.authorization import get_current_authenticated_user, roles_required
from app.models.enums import UserRole
from app.repositories import get_recipe
from app.repositories.recipes import RecipeImagePersistenceError
from app.services.recipe_images import (
    RecipeImagePermissionError,
    replace_recipe_image,
)
from app.services.storage import (
    ImageStorageConfigurationError,
    ImageUploadError,
    ImageValidationError,
)

_AUTHENTICATED_ROLES = (UserRole.USER, UserRole.MODERATOR, UserRole.ADMIN)


class RecipeImageResource(Resource):
    """Upload or replace an image belonging to a recipe."""

    @roles_required(*_AUTHENTICATED_ROLES)
    def post(self, recipe_id: int):
        """Store a validated multipart image for an authorized recipe."""
        recipe = get_recipe(recipe_id)
        if recipe is None:
            return {"message": "Recipe not found."}, 404

        user = get_current_authenticated_user()
        if user is None:
            return {"message": "Authentication is required."}, 401
        uploaded_file = request.files.get("image")
        if uploaded_file is None:
            uploaded_file = request.files.get("file")
        if uploaded_file is None:
            return {"message": "Image file is required."}, 400

        try:
            image_key, image_url = replace_recipe_image(
                recipe, user, uploaded_file
            )
        except RecipeImagePermissionError:
            return {"message": "Insufficient permissions."}, 403
        except ImageValidationError as error:
            return {"message": str(error)}, 400
        except ImageStorageConfigurationError:
            return {"message": "Image storage is not configured."}, 503
        except ImageUploadError as error:
            return {"message": str(error)}, 502
        except RecipeImagePersistenceError:
            return {"message": "Recipe image could not be saved."}, 500

        return {"image_key": image_key, "image_url": image_url}, 201
