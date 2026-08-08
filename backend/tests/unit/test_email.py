"""Unit tests for AWS SES welcome email delivery."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from botocore.exceptions import ClientError

from app.services.email import (
    EmailDeliveryError,
    SESWelcomeEmailService,
)


def _service(client: Mock) -> SESWelcomeEmailService:
    """Build an SES service with an injected client and inert credentials."""
    return SESWelcomeEmailService(
        access_key_id="test-access-key",
        secret_access_key="test-secret-key",
        region="eu-west-1",
        sender_email="welcome@example.test",
        application_name="Recipe Community",
        client=client,
    )


def test_welcome_email_contains_text_html_name_and_application():
    """SES receives both body formats with the expected welcome content."""
    client = Mock()
    user = SimpleNamespace(
        email="cook@example.test",
        first_name="Ada",
        username="ada_cooks",
    )

    _service(client).send_welcome_email(user)

    request = client.send_email.call_args.kwargs
    assert request["Source"] == "welcome@example.test"
    assert request["Destination"] == {"ToAddresses": ["cook@example.test"]}
    text = request["Message"]["Body"]["Text"]["Data"]
    html = request["Message"]["Body"]["Html"]["Data"]
    assert "Ada" in text
    assert "Recipe Community" in text
    assert "create your own recipes" in text
    assert "discover recipes" in html


def test_welcome_email_falls_back_to_username_and_escapes_html():
    """A missing first name uses a safely escaped username in HTML."""
    client = Mock()
    user = SimpleNamespace(
        email="cook@example.test",
        first_name=None,
        username="cook<script>",
    )

    _service(client).send_welcome_email(user)

    html = client.send_email.call_args.kwargs["Message"]["Body"]["Html"][
        "Data"
    ]
    assert "cook&lt;script&gt;" in html
    assert "cook<script>" not in html


def test_ses_client_failure_is_normalized():
    """Provider error details are hidden behind a safe service exception."""
    client = Mock()
    client.send_email.side_effect = ClientError(
        {"Error": {"Code": "ServiceUnavailable", "Message": "detail"}},
        "SendEmail",
    )
    user = SimpleNamespace(
        email="cook@example.test",
        first_name="Ada",
        username="ada_cooks",
    )

    with pytest.raises(EmailDeliveryError, match="delivery failed"):
        _service(client).send_welcome_email(user)
