"""Unit tests for AWS S3 recipe image storage."""

import re
from io import BytesIO
from unittest.mock import Mock

import pytest
from botocore.exceptions import ClientError
from werkzeug.datastructures import FileStorage

from app.services.storage import (
    MAX_RECIPE_IMAGE_SIZE,
    ImageDeleteError,
    ImageStorageConfigurationError,
    ImageUploadError,
    ImageValidationError,
    S3RecipeImageStorage,
)


def _storage(client: Mock) -> S3RecipeImageStorage:
    """Build storage with inert test credentials and an injected client."""
    return S3RecipeImageStorage(
        access_key_id="test-access-key",
        secret_access_key="test-secret-key",
        region="eu-west-1",
        bucket_name="recipe-images-test",
        client=client,
    )


def _file(data: bytes, filename: str = "untrusted.exe") -> FileStorage:
    """Create an in-memory multipart-style upload."""
    return FileStorage(stream=BytesIO(data), filename=filename)


def test_upload_validates_content_and_generates_safe_unique_key():
    """The original filename is ignored and PNG signature determines type."""
    client = Mock()
    storage = _storage(client)
    data = b"\x89PNG\r\n\x1a\n" + b"image payload"

    key = storage.upload_recipe_image(42, _file(data, "../../attack.jpg"))

    assert re.fullmatch(r"recipes/42/[0-9a-f]{32}\.png", key)
    client.put_object.assert_called_once_with(
        Bucket="recipe-images-test",
        Key=key,
        Body=data,
        ContentType="image/png",
    )


@pytest.mark.parametrize(
    ("data", "message"),
    [
        (b"", "cannot be empty"),
        (b"not an image", "JPEG, PNG, or WebP"),
    ],
)
def test_upload_rejects_empty_and_invalid_files(data, message):
    """Empty and invalid input never reaches the S3 client."""
    client = Mock()

    with pytest.raises(ImageValidationError, match=message):
        _storage(client).upload_recipe_image(1, _file(data))

    client.put_object.assert_not_called()


def test_upload_rejects_files_larger_than_five_megabytes():
    """Oversized input is rejected before an S3 request is made."""
    client = Mock()
    data = b"\xff\xd8\xff" + b"x" * MAX_RECIPE_IMAGE_SIZE

    with pytest.raises(ImageValidationError, match="exceed 5 MB"):
        _storage(client).upload_recipe_image(1, _file(data))

    client.put_object.assert_not_called()


def test_s3_upload_and_delete_failures_are_normalized():
    """AWS client exceptions do not leak provider details to callers."""
    error = ClientError(
        {"Error": {"Code": "InternalError", "Message": "AWS detail"}},
        "PutObject",
    )
    client = Mock()
    client.put_object.side_effect = error
    storage = _storage(client)

    with pytest.raises(ImageUploadError, match="upload failed"):
        storage.upload_recipe_image(1, _file(b"\xff\xd8\xffpayload"))

    client.delete_object.side_effect = error
    with pytest.raises(ImageDeleteError, match="deletion failed"):
        storage.delete_recipe_image("recipes/1/old.jpg")


def test_delete_and_url_generation_use_only_the_object_key():
    """Storage creates a private, expiring URL for an object key."""
    client = Mock()
    client.generate_presigned_url.return_value = "https://signed.example/image"
    storage = _storage(client)
    key = "recipes/7/image name.webp"

    storage.delete_recipe_image(key)

    client.delete_object.assert_called_once_with(
        Bucket="recipe-images-test", Key=key
    )
    assert storage.generate_image_url(key) == "https://signed.example/image"
    client.generate_presigned_url.assert_called_once_with(
        "get_object",
        Params={"Bucket": "recipe-images-test", "Key": key},
        ExpiresIn=3600,
    )


def test_url_generation_returns_none_without_an_object_key():
    """No S3 request is made when a recipe has no image."""
    client = Mock()

    assert _storage(client).generate_image_url(None) is None

    client.generate_presigned_url.assert_not_called()


def test_url_generation_uses_configured_expiration():
    """A configured expiration is forwarded to boto3 unchanged."""
    client = Mock()
    storage = S3RecipeImageStorage(
        access_key_id="test-access-key",
        secret_access_key="test-secret-key",
        region="eu-west-1",
        bucket_name="recipe-images-test",
        presigned_url_expiration=120,
        client=client,
    )

    storage.generate_image_url("recipes/1/private.png")

    assert client.generate_presigned_url.call_args.kwargs["ExpiresIn"] == 120


def test_storage_requires_all_environment_backed_configuration():
    """Missing S3 settings fail before constructing an AWS client."""
    with pytest.raises(ImageStorageConfigurationError, match="AWS_REGION"):
        S3RecipeImageStorage(
            access_key_id="key",
            secret_access_key="secret",
            region=None,
            bucket_name="bucket",
        )
