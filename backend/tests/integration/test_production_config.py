"""Production configuration and CORS safety tests."""

import pytest

from app import create_app


def _configure_production(monkeypatch, tmp_path, frontend_origin=None):
    database_path = tmp_path / "production.sqlite"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path.as_posix()}")
    monkeypatch.setenv("SECRET_KEY", "production-test-secret-key")
    monkeypatch.setenv("JWT_SECRET_KEY", "production-test-jwt-key")
    if frontend_origin is None:
        monkeypatch.delenv("FRONTEND_ORIGIN", raising=False)
    else:
        monkeypatch.setenv("FRONTEND_ORIGIN", frontend_origin)


def test_production_requires_a_frontend_origin(monkeypatch, tmp_path):
    _configure_production(monkeypatch, tmp_path)

    with pytest.raises(RuntimeError, match="FRONTEND_ORIGIN"):
        create_app("production")


def test_production_rejects_unrestricted_cors(monkeypatch, tmp_path):
    _configure_production(monkeypatch, tmp_path, "*")

    with pytest.raises(RuntimeError, match="cannot allow every origin"):
        create_app("production")


def test_production_cors_allows_only_configured_origin(monkeypatch, tmp_path):
    allowed_origin = "https://example.netlify.app"
    _configure_production(monkeypatch, tmp_path, f"{allowed_origin}/")
    application = create_app("production")
    client = application.test_client()

    allowed_response = client.get(
        "/health", headers={"Origin": allowed_origin}
    )
    blocked_response = client.get(
        "/health", headers={"Origin": "https://untrusted.example"}
    )

    assert allowed_response.headers["Access-Control-Allow-Origin"] == (
        allowed_origin
    )
    assert "Access-Control-Allow-Origin" not in blocked_response.headers
