"""OpenAPI specification and interactive Swagger UI for the HTTP API."""

# ruff: noqa: E501

from flask import Blueprint, Response, jsonify

openapi_blueprint = Blueprint("openapi", __name__)

_JWT_SECURITY = [{"bearerAuth": []}]
_JSON = "application/json"


def _ref(name: str) -> dict:
    return {"$ref": f"#/components/schemas/{name}"}


def _response(description: str, schema: dict | None = None) -> dict:
    response = {"description": description}
    if schema is not None:
        response["content"] = {_JSON: {"schema": schema}}
    return response


def _json_body(schema_name: str, *, required: bool = True) -> dict:
    return {
        "required": required,
        "content": {_JSON: {"schema": _ref(schema_name)}},
    }


def _id_parameter(name: str, description: str) -> dict:
    return {
        "name": name,
        "in": "path",
        "required": True,
        "description": description,
        "schema": {"type": "integer", "minimum": 1},
    }


_RECIPE_ID = _id_parameter("recipe_id", "Recipe identifier.")
_COMMENT_ID = _id_parameter("comment_id", "Comment identifier.")
_USER_ID = _id_parameter("user_id", "User identifier.")

_STANDARD_ERRORS = {
    "400": _response("Validation failed.", _ref("ValidationError")),
    "401": _response("Authentication is required.", _ref("Error")),
    "403": _response("Insufficient permissions.", _ref("Error")),
    "404": _response("Resource not found.", _ref("Error")),
    "409": _response(
        "The request conflicts with current state.", _ref("Error")
    ),
}


OPENAPI_SPEC = {
    "openapi": "3.0.3",
    "info": {
        "title": "Recipe Sharing API",
        "version": "1.0.0",
        "description": (
            "REST API for recipe publishing, moderation, community interactions, "
            "donations, and account administration. Protected operations require "
            "a JWT access token returned by `/auth/login`."
        ),
    },
    "servers": [{"url": "/", "description": "Current server"}],
    "tags": [
        {"name": "Authentication"},
        {"name": "Recipes"},
        {"name": "Moderation"},
        {"name": "Comments"},
        {"name": "Likes"},
        {"name": "Images"},
        {"name": "Donations"},
        {"name": "Admin Users"},
        {"name": "Health"},
    ],
    "paths": {
        "/health": {
            "get": {
                "tags": ["Health"],
                "summary": "Check API health",
                "operationId": "getHealth",
                "responses": {
                    "200": _response("API is available.", _ref("Health"))
                },
            }
        },
        "/auth/register": {
            "post": {
                "tags": ["Authentication"],
                "summary": "Register a user",
                "operationId": "registerUser",
                "requestBody": _json_body("UserRegistration"),
                "responses": {
                    "201": _response("User registered.", _ref("User")),
                    "400": _STANDARD_ERRORS["400"],
                    "409": _response(
                        "Email or username is already registered.",
                        _ref("Error"),
                    ),
                },
            }
        },
        "/auth/login": {
            "post": {
                "tags": ["Authentication"],
                "summary": "Log in",
                "operationId": "loginUser",
                "requestBody": _json_body("Login"),
                "responses": {
                    "200": _response("Authenticated.", _ref("LoginResponse")),
                    "400": _STANDARD_ERRORS["400"],
                    "401": _response("Invalid credentials.", _ref("Error")),
                },
            }
        },
        "/recipes": {
            "get": {
                "tags": ["Recipes"],
                "summary": "List approved recipes",
                "description": "Public. Returns only APPROVED recipes, newest first.",
                "operationId": "listRecipes",
                "responses": {
                    "200": _response(
                        "Approved recipes.",
                        {"type": "array", "items": _ref("Recipe")},
                    )
                },
            },
            "post": {
                "tags": ["Recipes"],
                "summary": "Create a draft recipe",
                "description": "Authenticated USER, MODERATOR, or ADMIN.",
                "operationId": "createRecipe",
                "security": _JWT_SECURITY,
                "requestBody": _json_body("RecipeInput"),
                "responses": {
                    "201": _response("Draft created.", _ref("Recipe")),
                    "400": _STANDARD_ERRORS["400"],
                    "401": _STANDARD_ERRORS["401"],
                    "403": _STANDARD_ERRORS["403"],
                    "409": _STANDARD_ERRORS["409"],
                },
            },
        },
        "/recipes/pending": {
            "get": {
                "tags": ["Moderation"],
                "summary": "List pending recipes",
                "description": "MODERATOR or ADMIN only. Oldest submissions first.",
                "operationId": "listPendingRecipes",
                "security": _JWT_SECURITY,
                "responses": {
                    "200": _response(
                        "Pending moderation queue.",
                        {"type": "array", "items": _ref("Recipe")},
                    ),
                    "401": _STANDARD_ERRORS["401"],
                    "403": _STANDARD_ERRORS["403"],
                },
            }
        },
        "/recipes/{recipe_id}": {
            "parameters": [_RECIPE_ID],
            "get": {
                "tags": ["Recipes"],
                "summary": "Get a recipe",
                "description": (
                    "Public for APPROVED recipes. An optional JWT allows owners and "
                    "moderation staff to view otherwise hidden recipes."
                ),
                "operationId": "getRecipe",
                "security": [{}, {"bearerAuth": []}],
                "responses": {
                    "200": _response("Recipe details.", _ref("Recipe")),
                    "404": _STANDARD_ERRORS["404"],
                },
            },
            "put": {
                "tags": ["Recipes"],
                "summary": "Update a recipe",
                "description": (
                    "Owners may edit their DRAFT or REJECTED recipes. MODERATOR and "
                    "ADMIN may edit any recipe. All fields are optional for updates."
                ),
                "operationId": "updateRecipe",
                "security": _JWT_SECURITY,
                "requestBody": _json_body("RecipeUpdate"),
                "responses": {
                    "200": _response("Recipe updated.", _ref("Recipe")),
                    **_STANDARD_ERRORS,
                },
            },
            "delete": {
                "tags": ["Recipes"],
                "summary": "Delete a recipe",
                "description": "Authenticated; ownership and role rules are enforced.",
                "operationId": "deleteRecipe",
                "security": _JWT_SECURITY,
                "responses": {
                    "204": _response("Recipe deleted."),
                    "401": _STANDARD_ERRORS["401"],
                    "403": _STANDARD_ERRORS["403"],
                    "404": _STANDARD_ERRORS["404"],
                    "409": _STANDARD_ERRORS["409"],
                },
            },
        },
        "/recipes/{recipe_id}/submit": {
            "parameters": [_RECIPE_ID],
            "post": {
                "tags": ["Moderation"],
                "summary": "Submit a recipe for review",
                "description": "The owner may submit a DRAFT or REJECTED recipe.",
                "operationId": "submitRecipe",
                "security": _JWT_SECURITY,
                "responses": {
                    "200": _response("Recipe submitted.", _ref("Recipe")),
                    "401": _STANDARD_ERRORS["401"],
                    "403": _STANDARD_ERRORS["403"],
                    "404": _STANDARD_ERRORS["404"],
                    "409": _STANDARD_ERRORS["409"],
                },
            },
        },
        "/recipes/{recipe_id}/approve": {
            "parameters": [_RECIPE_ID],
            "post": {
                "tags": ["Moderation"],
                "summary": "Approve a pending recipe",
                "description": "MODERATOR or ADMIN only.",
                "operationId": "approveRecipe",
                "security": _JWT_SECURITY,
                "responses": {
                    "200": _response("Recipe approved.", _ref("Recipe")),
                    "401": _STANDARD_ERRORS["401"],
                    "403": _STANDARD_ERRORS["403"],
                    "404": _STANDARD_ERRORS["404"],
                    "409": _STANDARD_ERRORS["409"],
                },
            },
        },
        "/recipes/{recipe_id}/reject": {
            "parameters": [_RECIPE_ID],
            "post": {
                "tags": ["Moderation"],
                "summary": "Reject a pending recipe",
                "description": "MODERATOR or ADMIN only.",
                "operationId": "rejectRecipe",
                "security": _JWT_SECURITY,
                "requestBody": _json_body("RecipeRejection"),
                "responses": {
                    "200": _response("Recipe rejected.", _ref("Recipe")),
                    "400": _STANDARD_ERRORS["400"],
                    "401": _STANDARD_ERRORS["401"],
                    "403": _STANDARD_ERRORS["403"],
                    "404": _STANDARD_ERRORS["404"],
                    "409": _STANDARD_ERRORS["409"],
                },
            },
        },
        "/recipes/{recipe_id}/comments": {
            "parameters": [_RECIPE_ID],
            "get": {
                "tags": ["Comments"],
                "summary": "List recipe comments",
                "description": (
                    "Public for approved recipes; optional authentication follows recipe "
                    "visibility rules. Deleted comments are omitted. Oldest first."
                ),
                "operationId": "listRecipeComments",
                "security": [{}, {"bearerAuth": []}],
                "responses": {
                    "200": _response(
                        "Comments.",
                        {"type": "array", "items": _ref("Comment")},
                    ),
                    "404": _STANDARD_ERRORS["404"],
                },
            },
            "post": {
                "tags": ["Comments"],
                "summary": "Add a comment",
                "description": "Authenticated users; recipe must be APPROVED.",
                "operationId": "createComment",
                "security": _JWT_SECURITY,
                "requestBody": _json_body("CommentInput"),
                "responses": {
                    "201": _response("Comment created.", _ref("Comment")),
                    "400": _STANDARD_ERRORS["400"],
                    "401": _STANDARD_ERRORS["401"],
                    "403": _STANDARD_ERRORS["403"],
                    "404": _STANDARD_ERRORS["404"],
                    "409": _STANDARD_ERRORS["409"],
                },
            },
        },
        "/comments/{comment_id}": {
            "parameters": [_COMMENT_ID],
            "put": {
                "tags": ["Comments"],
                "summary": "Edit a comment",
                "description": "Comment author, MODERATOR, or ADMIN.",
                "operationId": "updateComment",
                "security": _JWT_SECURITY,
                "requestBody": _json_body("CommentInput"),
                "responses": {
                    "200": _response("Comment updated.", _ref("Comment")),
                    "400": _STANDARD_ERRORS["400"],
                    "401": _STANDARD_ERRORS["401"],
                    "403": _STANDARD_ERRORS["403"],
                    "404": _STANDARD_ERRORS["404"],
                },
            },
            "delete": {
                "tags": ["Comments"],
                "summary": "Soft-delete a comment",
                "description": "Comment author, MODERATOR, or ADMIN.",
                "operationId": "deleteComment",
                "security": _JWT_SECURITY,
                "responses": {
                    "204": _response("Comment soft-deleted."),
                    "401": _STANDARD_ERRORS["401"],
                    "403": _STANDARD_ERRORS["403"],
                    "404": _STANDARD_ERRORS["404"],
                },
            },
        },
        "/recipes/{recipe_id}/likes": {
            "parameters": [_RECIPE_ID],
            "get": {
                "tags": ["Likes"],
                "summary": "Get recipe like count",
                "description": "Public; recipe must be APPROVED.",
                "operationId": "getRecipeLikes",
                "responses": {
                    "200": _response("Like count.", _ref("LikeCount")),
                    "404": _STANDARD_ERRORS["404"],
                },
            },
            "post": {
                "tags": ["Likes"],
                "summary": "Like a recipe",
                "description": "Authenticated; recipe must be APPROVED.",
                "operationId": "likeRecipe",
                "security": _JWT_SECURITY,
                "responses": {
                    "201": _response("Recipe liked.", _ref("Message")),
                    "401": _STANDARD_ERRORS["401"],
                    "403": _STANDARD_ERRORS["403"],
                    "404": _STANDARD_ERRORS["404"],
                    "409": _STANDARD_ERRORS["409"],
                },
            },
            "delete": {
                "tags": ["Likes"],
                "summary": "Unlike a recipe",
                "description": "Authenticated; the current user's like must exist.",
                "operationId": "unlikeRecipe",
                "security": _JWT_SECURITY,
                "responses": {
                    "204": _response("Like removed."),
                    "401": _STANDARD_ERRORS["401"],
                    "403": _STANDARD_ERRORS["403"],
                    "404": _STANDARD_ERRORS["404"],
                    "409": _STANDARD_ERRORS["409"],
                },
            },
        },
        "/recipes/{recipe_id}/image": {
            "parameters": [_RECIPE_ID],
            "post": {
                "tags": ["Images"],
                "summary": "Upload or replace a recipe image",
                "description": (
                    "Owner for their DRAFT or REJECTED recipe, or MODERATOR/ADMIN. "
                    "JPEG, PNG, or WebP; maximum 5 MB. Existing images are replaced."
                ),
                "operationId": "uploadRecipeImage",
                "security": _JWT_SECURITY,
                "requestBody": {
                    "required": True,
                    "content": {
                        "multipart/form-data": {
                            "schema": {
                                "type": "object",
                                "required": ["image"],
                                "properties": {
                                    "image": {
                                        "type": "string",
                                        "format": "binary",
                                        "description": "JPEG, PNG, or WebP image up to 5 MB.",
                                    }
                                },
                            }
                        }
                    },
                },
                "responses": {
                    "201": _response("Image uploaded.", _ref("ImageUpload")),
                    "400": _STANDARD_ERRORS["400"],
                    "401": _STANDARD_ERRORS["401"],
                    "403": _STANDARD_ERRORS["403"],
                    "404": _STANDARD_ERRORS["404"],
                    "500": _response(
                        "Image metadata could not be saved.", _ref("Error")
                    ),
                    "502": _response("S3 upload failed.", _ref("Error")),
                    "503": _response(
                        "Image storage is not configured.", _ref("Error")
                    ),
                },
            },
        },
        "/recipes/{recipe_id}/donations": {
            "parameters": [_RECIPE_ID],
            "post": {
                "tags": ["Donations"],
                "summary": "Create a donation",
                "description": (
                    "Authenticated. Recipe must be APPROVED and donors cannot donate "
                    "to their own recipe. External payment processing is provider-dependent."
                ),
                "operationId": "createDonation",
                "security": _JWT_SECURITY,
                "requestBody": _json_body("DonationInput"),
                "responses": {
                    "201": _response("Donation created.", _ref("Donation")),
                    "400": _STANDARD_ERRORS["400"],
                    "401": _STANDARD_ERRORS["401"],
                    "403": _STANDARD_ERRORS["403"],
                    "404": _STANDARD_ERRORS["404"],
                    "409": _STANDARD_ERRORS["409"],
                    "500": _response(
                        "Donation persistence failed.", _ref("Error")
                    ),
                    "502": _response(
                        "Payment provider failed after donation persistence.",
                        _ref("DonationProviderError"),
                    ),
                },
            },
        },
        "/admin/users": {
            "get": {
                "tags": ["Admin Users"],
                "summary": "List users",
                "description": "ADMIN only.",
                "operationId": "listAdminUsers",
                "security": _JWT_SECURITY,
                "responses": {
                    "200": _response(
                        "Users.", {"type": "array", "items": _ref("AdminUser")}
                    ),
                    "401": _STANDARD_ERRORS["401"],
                    "403": _STANDARD_ERRORS["403"],
                },
            },
            "post": {
                "tags": ["Admin Users"],
                "summary": "Create a user",
                "description": "ADMIN only.",
                "operationId": "createAdminUser",
                "security": _JWT_SECURITY,
                "requestBody": _json_body("AdminUserCreate"),
                "responses": {
                    "201": _response("User created.", _ref("AdminUser")),
                    "400": _STANDARD_ERRORS["400"],
                    "401": _STANDARD_ERRORS["401"],
                    "403": _STANDARD_ERRORS["403"],
                    "409": _STANDARD_ERRORS["409"],
                },
            },
        },
        "/admin/users/{user_id}": {
            "parameters": [_USER_ID],
            "get": {
                "tags": ["Admin Users"],
                "summary": "Get a user",
                "description": "ADMIN only.",
                "operationId": "getAdminUser",
                "security": _JWT_SECURITY,
                "responses": {
                    "200": _response("User.", _ref("AdminUser")),
                    "401": _STANDARD_ERRORS["401"],
                    "403": _STANDARD_ERRORS["403"],
                    "404": _STANDARD_ERRORS["404"],
                },
            },
            "put": {
                "tags": ["Admin Users"],
                "summary": "Update a user",
                "description": (
                    "ADMIN only. Self-protection and last-active-admin rules are enforced."
                ),
                "operationId": "updateAdminUser",
                "security": _JWT_SECURITY,
                "requestBody": _json_body("AdminUserUpdate"),
                "responses": {
                    "200": _response("User updated.", _ref("AdminUser")),
                    "400": _STANDARD_ERRORS["400"],
                    "401": _STANDARD_ERRORS["401"],
                    "403": _STANDARD_ERRORS["403"],
                    "404": _STANDARD_ERRORS["404"],
                    "409": _STANDARD_ERRORS["409"],
                },
            },
            "delete": {
                "tags": ["Admin Users"],
                "summary": "Deactivate a user",
                "description": (
                    "ADMIN only. This is account deactivation, not physical deletion. "
                    "Self-protection and last-active-admin rules are enforced."
                ),
                "operationId": "deactivateAdminUser",
                "security": _JWT_SECURITY,
                "responses": {
                    "204": _response("User deactivated."),
                    "401": _STANDARD_ERRORS["401"],
                    "403": _STANDARD_ERRORS["403"],
                    "404": _STANDARD_ERRORS["404"],
                    "409": _STANDARD_ERRORS["409"],
                },
            },
        },
    },
    "components": {
        "securitySchemes": {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": (
                    "Enter the JWT access token returned by `/auth/login`. Swagger UI "
                    "adds the `Bearer` prefix automatically."
                ),
            }
        },
        "schemas": {
            "Error": {
                "type": "object",
                "required": ["message"],
                "properties": {"message": {"type": "string"}},
            },
            "ValidationError": {
                "allOf": [
                    _ref("Error"),
                    {
                        "type": "object",
                        "properties": {
                            "errors": {
                                "type": "object",
                                "additionalProperties": True,
                            }
                        },
                    },
                ]
            },
            "Message": {
                "type": "object",
                "required": ["message"],
                "properties": {"message": {"type": "string"}},
            },
            "Health": {
                "type": "object",
                "required": ["status", "service"],
                "properties": {
                    "status": {"type": "string", "example": "ok"},
                    "service": {
                        "type": "string",
                        "example": "recipe-sharing-api",
                    },
                },
            },
            "UserRegistration": {
                "type": "object",
                "required": [
                    "email",
                    "username",
                    "password",
                    "first_name",
                    "last_name",
                ],
                "properties": {
                    "email": {"type": "string", "format": "email"},
                    "username": {
                        "type": "string",
                        "minLength": 3,
                        "maxLength": 30,
                    },
                    "password": {
                        "type": "string",
                        "format": "password",
                        "minLength": 8,
                        "writeOnly": True,
                        "description": "Requires uppercase, lowercase, and a digit.",
                    },
                    "first_name": {"type": "string"},
                    "last_name": {"type": "string"},
                },
            },
            "Login": {
                "type": "object",
                "required": ["email", "password"],
                "properties": {
                    "email": {"type": "string", "format": "email"},
                    "password": {
                        "type": "string",
                        "format": "password",
                        "writeOnly": True,
                    },
                },
            },
            "LoginResponse": {
                "type": "object",
                "required": ["access_token", "user"],
                "properties": {
                    "access_token": {
                        "type": "string",
                        "description": "JWT access token.",
                    },
                    "user": _ref("User"),
                },
            },
            "User": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "email": {"type": "string", "format": "email"},
                    "username": {"type": "string"},
                    "first_name": {"type": "string", "nullable": True},
                    "last_name": {"type": "string", "nullable": True},
                    "role": {
                        "type": "string",
                        "enum": ["USER", "MODERATOR", "ADMIN"],
                    },
                    "is_active": {"type": "boolean"},
                    "created_at": {"type": "string", "format": "date-time"},
                },
            },
            "AdminUser": {
                "allOf": [
                    _ref("User"),
                    {
                        "type": "object",
                        "properties": {
                            "updated_at": {
                                "type": "string",
                                "format": "date-time",
                            }
                        },
                    },
                ]
            },
            "AdminUserCreate": {
                "allOf": [
                    _ref("UserRegistration"),
                    {
                        "type": "object",
                        "required": ["role"],
                        "properties": {
                            "role": {
                                "type": "string",
                                "enum": ["USER", "MODERATOR", "ADMIN"],
                            },
                            "is_active": {"type": "boolean", "default": True},
                        },
                    },
                ]
            },
            "AdminUserUpdate": {
                "type": "object",
                "properties": {
                    "email": {"type": "string", "format": "email"},
                    "username": {
                        "type": "string",
                        "minLength": 3,
                        "maxLength": 30,
                    },
                    "first_name": {"type": "string"},
                    "last_name": {"type": "string"},
                    "role": {
                        "type": "string",
                        "enum": ["USER", "MODERATOR", "ADMIN"],
                    },
                    "is_active": {"type": "boolean"},
                },
            },
            "RecipeIngredientInput": {
                "type": "object",
                "required": ["name", "position"],
                "properties": {
                    "name": {"type": "string"},
                    "quantity": {"type": "string", "nullable": True},
                    "unit": {"type": "string", "nullable": True},
                    "position": {"type": "integer", "minimum": 1},
                    "notes": {"type": "string", "nullable": True},
                },
            },
            "RecipeStepInput": {
                "type": "object",
                "required": ["step_number", "instruction"],
                "properties": {
                    "step_number": {"type": "integer", "minimum": 1},
                    "instruction": {"type": "string"},
                },
            },
            "RecipeInput": {
                "type": "object",
                "required": ["title", "description", "ingredients", "steps"],
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "ingredients": {
                        "type": "array",
                        "minItems": 1,
                        "items": _ref("RecipeIngredientInput"),
                    },
                    "steps": {
                        "type": "array",
                        "minItems": 1,
                        "items": _ref("RecipeStepInput"),
                    },
                },
            },
            "RecipeUpdate": {
                "description": "Partial recipe update; every property is optional.",
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "ingredients": {
                        "type": "array",
                        "minItems": 1,
                        "items": _ref("RecipeIngredientInput"),
                    },
                    "steps": {
                        "type": "array",
                        "minItems": 1,
                        "items": _ref("RecipeStepInput"),
                    },
                },
            },
            "RecipeRejection": {
                "type": "object",
                "required": ["reason"],
                "properties": {
                    "reason": {
                        "type": "string",
                        "minLength": 5,
                        "maxLength": 500,
                    }
                },
            },
            "RecipeIngredient": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "quantity": {"type": "string", "nullable": True},
                    "unit": {"type": "string", "nullable": True},
                    "position": {"type": "integer"},
                    "notes": {"type": "string", "nullable": True},
                },
            },
            "RecipeStep": {
                "type": "object",
                "properties": {
                    "step_number": {"type": "integer"},
                    "instruction": {"type": "string"},
                },
            },
            "Recipe": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "title": {"type": "string"},
                    "slug": {"type": "string"},
                    "description": {"type": "string", "nullable": True},
                    "status": {
                        "type": "string",
                        "enum": ["DRAFT", "PENDING", "APPROVED", "REJECTED"],
                    },
                    "like_count": {"type": "integer", "minimum": 0},
                    "liked_by_current_user": {"type": "boolean"},
                    "author": _ref("User"),
                    "ingredients": {
                        "type": "array",
                        "items": _ref("RecipeIngredient"),
                    },
                    "steps": {"type": "array", "items": _ref("RecipeStep")},
                    "created_at": {"type": "string", "format": "date-time"},
                    "submitted_at": {
                        "type": "string",
                        "format": "date-time",
                        "nullable": True,
                    },
                    "approved_at": {
                        "type": "string",
                        "format": "date-time",
                        "nullable": True,
                    },
                    "image_url": {
                        "type": "string",
                        "format": "uri",
                        "nullable": True,
                        "description": "Temporary presigned URL when an image exists.",
                    },
                },
            },
            "CommentInput": {
                "type": "object",
                "required": ["content"],
                "properties": {
                    "content": {
                        "type": "string",
                        "minLength": 2,
                        "maxLength": 1000,
                    }
                },
            },
            "CommentAuthor": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "username": {"type": "string"},
                    "first_name": {"type": "string", "nullable": True},
                    "last_name": {"type": "string", "nullable": True},
                },
            },
            "Comment": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "content": {"type": "string"},
                    "recipe_id": {"type": "integer"},
                    "author": _ref("CommentAuthor"),
                    "created_at": {"type": "string", "format": "date-time"},
                    "updated_at": {"type": "string", "format": "date-time"},
                },
            },
            "LikeCount": {
                "type": "object",
                "required": ["count"],
                "properties": {"count": {"type": "integer", "minimum": 0}},
            },
            "ImageUpload": {
                "type": "object",
                "properties": {
                    "image_key": {
                        "type": "string",
                        "example": "recipes/42/uuid.webp",
                    },
                    "image_url": {
                        "type": "string",
                        "format": "uri",
                        "nullable": True,
                    },
                },
            },
            "DonationInput": {
                "type": "object",
                "required": ["amount", "currency"],
                "properties": {
                    "amount": {
                        "type": "string",
                        "pattern": "^[0-9]+(?:\\.[0-9]{1,2})?$",
                        "example": "10.00",
                        "description": "Positive decimal string with at most two decimal places; never a JSON number.",
                    },
                    "currency": {
                        "type": "string",
                        "enum": ["EUR"],
                        "example": "EUR",
                    },
                },
            },
            "Donation": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "recipe_id": {"type": "integer"},
                    "donor_id": {"type": "integer"},
                    "recipient_id": {"type": "integer"},
                    "amount": {"type": "string", "example": "10.00"},
                    "currency": {"type": "string", "enum": ["EUR"]},
                    "status": {
                        "type": "string",
                        "enum": [
                            "PENDING",
                            "PROCESSING",
                            "COMPLETED",
                            "FAILED",
                            "REFUNDED",
                        ],
                    },
                    "wise_transfer_id": {"type": "string", "nullable": True},
                    "idempotency_key": {"type": "string", "format": "uuid"},
                    "created_at": {"type": "string", "format": "date-time"},
                    "completed_at": {
                        "type": "string",
                        "format": "date-time",
                        "nullable": True,
                    },
                },
            },
            "DonationProviderError": {
                "allOf": [
                    _ref("Error"),
                    {
                        "type": "object",
                        "properties": {"donation": _ref("Donation")},
                    },
                ]
            },
        },
    },
}


_SWAGGER_HTML = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Recipe Sharing API Docs</title>
    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
  </head>
  <body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <script>
      window.onload = () => SwaggerUIBundle({
        url: '/openapi.json',
        dom_id: '#swagger-ui',
        deepLinking: true,
        persistAuthorization: true,
        displayRequestDuration: true
      });
    </script>
  </body>
</html>
"""


@openapi_blueprint.get("/openapi.json")
def openapi_json():
    """Return the machine-readable OpenAPI document."""
    return jsonify(OPENAPI_SPEC)


@openapi_blueprint.get("/docs")
def swagger_ui():
    """Return the interactive Swagger UI shell."""
    return Response(_SWAGGER_HTML, mimetype="text/html")
