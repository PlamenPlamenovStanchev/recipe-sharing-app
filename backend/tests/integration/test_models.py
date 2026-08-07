"""Integration tests for database model constraints and defaults."""

from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import Donation, RecipeLike, RecipeStatus
from tests.factories import RecipeFactory, UserFactory


def test_user_email_must_be_unique():
    """Users cannot share an email address."""
    UserFactory(email="duplicate@example.test")

    with pytest.raises(IntegrityError):
        UserFactory(email="duplicate@example.test")

    db.session.rollback()


def test_user_password_is_hashed():
    """Factory users store an Argon2 hash instead of the plaintext password."""
    user = UserFactory()

    assert user.password_hash != "FactoryPass1"
    assert user.check_password("FactoryPass1")


def test_recipe_default_status_is_draft():
    """Recipes use DRAFT status when no status is supplied."""
    recipe = RecipeFactory()

    assert recipe.status == RecipeStatus.DRAFT


def test_recipe_like_is_unique_per_user():
    """A user can like a recipe only once."""
    user = UserFactory()
    recipe = RecipeFactory()
    db.session.add(RecipeLike(user=user, recipe=recipe))
    db.session.flush()

    db.session.add(RecipeLike(user=user, recipe=recipe))

    with pytest.raises(IntegrityError):
        db.session.flush()

    db.session.rollback()


def test_donation_amount_must_be_positive():
    """Database check constraints reject zero-value donations."""
    donor = UserFactory()
    recipient = UserFactory()
    recipe = RecipeFactory()
    donation = Donation(
        donor=donor,
        recipient=recipient,
        recipe=recipe,
        amount=Decimal("0.00"),
        currency="EUR",
        idempotency_key="zero-value-donation",
    )
    db.session.add(donation)

    with pytest.raises(IntegrityError):
        db.session.flush()

    db.session.rollback()
