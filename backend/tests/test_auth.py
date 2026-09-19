from datetime import datetime, timedelta, timezone

import jwt
from fastapi.testclient import TestClient

from core.config import get_settings
from main import app


def _client():
    return TestClient(app)


def test_register_login_me_flow(db):
    with _client() as c:
        register_resp = c.post(
            "/api/auth/register",
            json={"email": "novo@teste.com", "password": "senha1234", "name": "Novo Usuário"},
        )
        assert register_resp.status_code == 201
        body = register_resp.json()
        assert body["token_type"] == "bearer"
        assert body["user"]["email"] == "novo@teste.com"
        assert body["user"]["plan"] == "pro"

        login_resp = c.post(
            "/api/auth/login",
            json={"email": "novo@teste.com", "password": "senha1234"},
        )
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]

        me_resp = c.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me_resp.status_code == 200
        assert me_resp.json()["email"] == "novo@teste.com"


def test_login_wrong_password_401(db):
    with _client() as c:
        c.post(
            "/api/auth/register",
            json={"email": "senha-errada@teste.com", "password": "senha1234"},
        )
        resp = c.post(
            "/api/auth/login",
            json={"email": "senha-errada@teste.com", "password": "senha-incorreta"},
        )
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Email ou senha incorretos"


def test_me_with_invalid_token_401(db):
    with _client() as c:
        resp = c.get("/api/auth/me", headers={"Authorization": "Bearer token.invalido.aqui"})
        assert resp.status_code == 401


def test_me_with_expired_token_401(db):
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expired_payload = {
        "sub": "00000000-0000-0000-0000-000000000000",
        "email": "x@x.com",
        "iat": now - timedelta(days=10),
        "exp": now - timedelta(days=3),
    }
    expired_token = jwt.encode(expired_payload, settings.jwt_secret, algorithm="HS256")

    with _client() as c:
        resp = c.get("/api/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
        assert resp.status_code == 401


def test_register_duplicate_email_409(db):
    with _client() as c:
        c.post(
            "/api/auth/register",
            json={"email": "duplicado@teste.com", "password": "senha1234"},
        )
        resp = c.post(
            "/api/auth/register",
            json={"email": "duplicado@teste.com", "password": "outrasenha"},
        )
        assert resp.status_code == 409


def test_register_short_password_422(db):
    with _client() as c:
        resp = c.post(
            "/api/auth/register",
            json={"email": "curta@teste.com", "password": "1234567"},
        )
        assert resp.status_code == 422


def test_update_me_name_and_password(db):
    with _client() as c:
        register_resp = c.post(
            "/api/auth/register",
            json={"email": "editar@teste.com", "password": "senha1234"},
        )
        token = register_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        patch_resp = c.patch("/api/auth/me", json={"name": "Nome Novo"}, headers=headers)
        assert patch_resp.status_code == 200
        assert patch_resp.json()["name"] == "Nome Novo"

        patch_pw_resp = c.patch(
            "/api/auth/me",
            json={"password": "novasenha123", "current_password": "senha1234"},
            headers=headers,
        )
        assert patch_pw_resp.status_code == 200

        login_resp = c.post(
            "/api/auth/login",
            json={"email": "editar@teste.com", "password": "novasenha123"},
        )
        assert login_resp.status_code == 200


def test_update_me_password_without_current_password_422():
    from models.auth import UpdateMeRequest
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        UpdateMeRequest(password="novasenha123")


def test_demo_user_login_is_pro(db):
    settings = get_settings()
    with _client() as c:
        resp = c.post(
            "/api/auth/login",
            json={"email": settings.demo_user_email, "password": settings.demo_user_password},
        )
        assert resp.status_code == 200
        assert resp.json()["user"]["plan"] == "pro"


def test_logout_returns_204(db):
    with _client() as c:
        register_resp = c.post(
            "/api/auth/register",
            json={"email": "logout@teste.com", "password": "senha1234"},
        )
        token = register_resp.json()["access_token"]
        resp = c.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 204
