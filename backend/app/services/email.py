"""AWS SES email delivery for application messages."""

from __future__ import annotations

from html import escape
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from flask import current_app

from app.models.user import User

DEFAULT_APPLICATION_NAME = "Recipe Sharing App"


class EmailServiceError(Exception):
    """Base error for safe handling of email delivery failures."""


class EmailConfigurationError(EmailServiceError):
    """Raised when required SES configuration is absent."""


class EmailDeliveryError(EmailServiceError):
    """Raised when SES cannot accept an email for delivery."""


class SESWelcomeEmailService:
    """Compose and deliver welcome emails through AWS SES."""

    def __init__(
        self,
        *,
        access_key_id: str | None,
        secret_access_key: str | None,
        region: str | None,
        sender_email: str | None,
        application_name: str = DEFAULT_APPLICATION_NAME,
        client: Any | None = None,
    ) -> None:
        values = {
            "AWS_ACCESS_KEY_ID": access_key_id,
            "AWS_SECRET_ACCESS_KEY": secret_access_key,
            "AWS_SES_REGION": region,
            "AWS_SES_SENDER_EMAIL": sender_email,
        }
        missing = [name for name, value in values.items() if not value]
        if missing:
            raise EmailConfigurationError(
                f"Missing SES configuration: {', '.join(missing)}."
            )

        self.sender_email = sender_email
        self.application_name = application_name
        if client is not None:
            self.client = client
            return
        try:
            self.client = boto3.client(
                "ses",
                aws_access_key_id=access_key_id,
                aws_secret_access_key=secret_access_key,
                region_name=region,
            )
        except BotoCoreError as error:
            raise EmailDeliveryError(
                "Welcome email delivery failed."
            ) from error

    @classmethod
    def from_app_config(cls) -> SESWelcomeEmailService:
        """Build the SES service from environment-backed application config."""
        return cls(
            access_key_id=current_app.config.get("AWS_ACCESS_KEY_ID"),
            secret_access_key=current_app.config.get("AWS_SECRET_ACCESS_KEY"),
            region=current_app.config.get("AWS_SES_REGION"),
            sender_email=current_app.config.get("AWS_SES_SENDER_EMAIL"),
            application_name=current_app.config.get(
                "APPLICATION_NAME", DEFAULT_APPLICATION_NAME
            ),
        )

    def send_welcome_email(self, user: User) -> None:
        """Send text and HTML welcome content to a registered user."""
        display_name = (user.first_name or "").strip() or user.username
        text_body = (
            f"Hi {display_name},\n\n"
            f"Welcome to {self.application_name}! "
            "You can now create your own recipes and discover recipes "
            "shared by the community."
        )
        html_body = (
            f"<p>Hi {escape(display_name)},</p>"
            f"<p>Welcome to {escape(self.application_name)}!</p>"
            "<p>You can now create your own recipes and discover recipes "
            "shared by the community.</p>"
        )

        try:
            self.client.send_email(
                Source=self.sender_email,
                Destination={"ToAddresses": [user.email]},
                Message={
                    "Subject": {
                        "Data": f"Welcome to {self.application_name}!",
                        "Charset": "UTF-8",
                    },
                    "Body": {
                        "Text": {"Data": text_body, "Charset": "UTF-8"},
                        "Html": {"Data": html_body, "Charset": "UTF-8"},
                    },
                },
            )
        except (BotoCoreError, ClientError) as error:
            raise EmailDeliveryError(
                "Welcome email delivery failed."
            ) from error


def send_welcome_email(user: User) -> None:
    """Send a welcome email using environment-backed SES configuration."""
    SESWelcomeEmailService.from_app_config().send_welcome_email(user)
