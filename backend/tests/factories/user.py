"""Factory for User model instances."""

import factory

from app.extensions import db
from app.models import User, UserRole
from app.services import hash_password


class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Create persisted users for model tests."""

    class Meta:
        model = User
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = "flush"

    email = factory.Sequence(lambda number: f"user{number}@example.test")
    username = factory.Sequence(lambda number: f"user{number}")
    password_hash = factory.LazyFunction(lambda: hash_password("FactoryPass1"))
    first_name = "Factory"
    last_name = "User"
    role = UserRole.USER
    is_active = True
