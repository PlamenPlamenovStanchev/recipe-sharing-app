"""Authentication API resources."""

from flask import request
from flask_restful import Resource
from marshmallow import ValidationError

from app.schemas import LoginSchema, UserOutputSchema, UserRegistrationSchema
from app.services.auth import (
    DuplicateEmailError,
    DuplicateUsernameError,
    InvalidCredentialsError,
    login_user,
    register_user,
)


def _validation_error_response(error: ValidationError) -> tuple[dict, int]:
    """Return a consistent client-safe response for schema failures."""
    return {"message": "Validation failed.", "errors": error.messages}, 400


class RegisterResource(Resource):
    """Create standard user accounts."""

    def post(self):
        """Register a user and return its public representation."""
        try:
            user_data = UserRegistrationSchema().load(
                request.get_json(silent=True) or {}
            )
        except ValidationError as error:
            return _validation_error_response(error)

        try:
            user = register_user(user_data)
        except DuplicateEmailError:
            return {"message": "Email is already registered."}, 409
        except DuplicateUsernameError:
            return {"message": "Username is already registered."}, 409

        return UserOutputSchema().dump(user), 201


class LoginResource(Resource):
    """Authenticate users and issue JWT access tokens."""

    def post(self):
        """Authenticate valid credentials without disclosing account state."""
        try:
            credentials = LoginSchema().load(
                request.get_json(silent=True) or {}
            )
        except ValidationError as error:
            return _validation_error_response(error)

        try:
            access_token, user = login_user(credentials)
        except InvalidCredentialsError:
            return {"message": "Invalid email or password."}, 401

        return {
            "access_token": access_token,
            "user": UserOutputSchema().dump(user),
        }, 200
