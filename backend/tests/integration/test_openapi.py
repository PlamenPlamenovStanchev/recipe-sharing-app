"""Smoke tests for machine-readable and interactive API documentation."""


def test_openapi_json_is_available(app):
    response = app.test_client().get("/openapi.json")

    assert response.status_code == 200
    assert response.json["openapi"] == "3.0.3"
    assert response.json["components"]["securitySchemes"]["bearerAuth"]
    assert set(response.json["paths"]) == {
        "/health",
        "/auth/register",
        "/auth/login",
        "/recipes",
        "/recipes/pending",
        "/recipes/{recipe_id}",
        "/recipes/{recipe_id}/submit",
        "/recipes/{recipe_id}/approve",
        "/recipes/{recipe_id}/reject",
        "/recipes/{recipe_id}/comments",
        "/comments/{comment_id}",
        "/recipes/{recipe_id}/likes",
        "/recipes/{recipe_id}/image",
        "/recipes/{recipe_id}/donations",
        "/admin/users",
        "/admin/users/{user_id}",
    }


def test_swagger_ui_is_available(app):
    response = app.test_client().get("/docs")

    assert response.status_code == 200
    assert response.mimetype == "text/html"
    assert b"SwaggerUIBundle" in response.data
