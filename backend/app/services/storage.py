"""AWS S3 storage operations for recipe images."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote
from uuid import uuid4

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from flask import current_app
from werkzeug.datastructures import FileStorage

MAX_RECIPE_IMAGE_SIZE = 5 * 1024 * 1024


class ImageStorageError(Exception):
    """Base error for recipe image storage failures."""


class ImageStorageConfigurationError(ImageStorageError):
    """Raised when required S3 configuration is absent."""


class ImageUploadError(ImageStorageError):
    """Raised when S3 cannot upload an image."""


class ImageDeleteError(ImageStorageError):
    """Raised when S3 cannot delete an image."""


class ImageValidationError(Exception):
    """Raised when an uploaded file is not a permitted recipe image."""


def _detect_image_type(data: bytes) -> tuple[str, str] | None:
    """Return a trusted extension and MIME type from image signature bytes."""
    if data.startswith(b"\xff\xd8\xff"):
        return "jpg", "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png", "image/png"
    if len(data) >= 12 and data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "webp", "image/webp"
    return None


class S3RecipeImageStorage:
    """Upload, delete, and create URLs for recipe image objects."""

    def __init__(
        self,
        *,
        access_key_id: str | None,
        secret_access_key: str | None,
        region: str | None,
        bucket_name: str | None,
        client: Any | None = None,
    ) -> None:
        values = {
            "AWS_ACCESS_KEY_ID": access_key_id,
            "AWS_SECRET_ACCESS_KEY": secret_access_key,
            "AWS_REGION": region,
            "AWS_S3_BUCKET_NAME": bucket_name,
        }
        missing = [name for name, value in values.items() if not value]
        if missing:
            raise ImageStorageConfigurationError(
                f"Missing S3 configuration: {', '.join(missing)}."
            )

        self.region = region
        self.bucket_name = bucket_name
        self.client = (
            client
            if client is not None
            else boto3.client(
                "s3",
                aws_access_key_id=access_key_id,
                aws_secret_access_key=secret_access_key,
                region_name=region,
            )
        )

    @classmethod
    def from_app_config(cls) -> S3RecipeImageStorage:
        """Build storage exclusively from application environment config."""
        return cls(
            access_key_id=current_app.config.get("AWS_ACCESS_KEY_ID"),
            secret_access_key=current_app.config.get("AWS_SECRET_ACCESS_KEY"),
            region=current_app.config.get("AWS_REGION"),
            bucket_name=current_app.config.get("AWS_S3_BUCKET_NAME"),
        )

    def upload_recipe_image(
        self, recipe_id: int, uploaded_file: FileStorage
    ) -> str:
        """Validate and upload a recipe image, returning its unique key."""
        data = uploaded_file.read(MAX_RECIPE_IMAGE_SIZE + 1)
        if not data:
            raise ImageValidationError("Image file cannot be empty.")
        if len(data) > MAX_RECIPE_IMAGE_SIZE:
            raise ImageValidationError("Image file cannot exceed 5 MB.")

        detected_type = _detect_image_type(data)
        if detected_type is None:
            raise ImageValidationError(
                "Image must be a JPEG, PNG, or WebP file."
            )
        extension, content_type = detected_type
        object_key = f"recipes/{recipe_id}/{uuid4().hex}.{extension}"

        try:
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=object_key,
                Body=data,
                ContentType=content_type,
            )
        except (BotoCoreError, ClientError) as error:
            raise ImageUploadError("Recipe image upload failed.") from error
        return object_key

    def delete_recipe_image(self, image_key: str | None) -> None:
        """Delete an existing recipe image object when a key is present."""
        if not image_key:
            return
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=image_key)
        except (BotoCoreError, ClientError) as error:
            raise ImageDeleteError("Recipe image deletion failed.") from error

    def generate_image_url(self, image_key: str | None) -> str | None:
        """Return the regional S3 URL for an object key."""
        if not image_key:
            return None
        encoded_key = quote(image_key, safe="/")
        if self.region == "us-east-1":
            return f"https://{self.bucket_name}.s3.amazonaws.com/{encoded_key}"
        return (
            f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/"
            f"{encoded_key}"
        )
