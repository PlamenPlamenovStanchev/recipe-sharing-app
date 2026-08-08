"""Integration coverage for the mocked recipe image upload endpoint."""

from io import BytesIO
from unittest.mock import Mock, patch

from flask_jwt_extended import create_access_token

from app.extensions import db
from app.models import Recipe, RecipeStatus
from tests.factories import RecipeFactory, UserFactory


def test_owner_uploads_multipart_image_without_real_aws_request(app):
    """The endpoint persists the mocked S3 key and removes a replaced key."""
    with app.app_context():
        owner = UserFactory()
        recipe = RecipeFactory(
            author=owner,
            status=RecipeStatus.DRAFT,
            image_key="recipes/1/previous.jpg",
        )
        recipe_id = recipe.id
        token = create_access_token(identity=str(owner.id))
        headers = {"Authorization": f"Bearer {token}"}
        db.session.commit()

    storage = Mock()
    storage.upload_recipe_image.return_value = (
        f"recipes/{recipe_id}/generated.png"
    )
    storage.generate_image_url.return_value = (
        "https://bucket.example/generated.png"
    )

    with patch(
        "app.services.recipe_images.S3RecipeImageStorage.from_app_config",
        return_value=storage,
    ):
        response = app.test_client().post(
            f"/recipes/{recipe_id}/image",
            data={
                "image": (
                    BytesIO(b"\x89PNG\r\n\x1a\nimage"),
                    "../../untrusted.exe",
                )
            },
            headers=headers,
            content_type="multipart/form-data",
        )

    assert response.status_code == 201
    assert response.get_json() == {
        "image_key": f"recipes/{recipe_id}/generated.png",
        "image_url": "https://bucket.example/generated.png",
    }
    storage.upload_recipe_image.assert_called_once()
    storage.delete_recipe_image.assert_called_once_with(
        "recipes/1/previous.jpg"
    )
    assert db.session.get(Recipe, recipe_id).image_key == (
        f"recipes/{recipe_id}/generated.png"
    )
