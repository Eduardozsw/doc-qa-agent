from datetime import datetime, timedelta, timezone

import jwt
import pytest

from core.config import get_settings
from core.security import create_token, decode_token, hash_password, verify_password


def test_hash_password_and_verify_success():
    hashed = hash_password("minhasenha123")
    assert hashed != "minhasenha123"
    assert verify_password("minhasenha123", hashed) is True


def test_verify_password_wrong_password_fails():
    hashed = hash_password("minhasenha123")
    assert verify_password("senha-errada", hashed) is False


def test_verify_password_invalid_hash_returns_false():
    assert verify_password("qualquer", "hash-invalido-nao-bcrypt") is False


def test_create_and_decode_token_roundtrip():
    token = create_token("user-123", "user@teste.com")
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == "user-123"
    assert payload["email"] == "user@teste.com"
    assert "iat" in payload
    assert "exp" in payload


def test_decode_expired_token_returns_none():
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "user-123",
        "email": "user@teste.com",
        "iat": now - timedelta(days=10),
        "exp": now - timedelta(seconds=1),
    }
    expired_token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
    assert decode_token(expired_token) is None


def test_decode_token_wrong_signature_returns_none():
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "user-123",
        "email": "user@teste.com",
        "iat": now,
        "exp": now + timedelta(days=1),
    }
    token_wrong_secret = jwt.encode(payload, "outro-segredo-qualquer", algorithm="HS256")
    assert decode_token(token_wrong_secret) is None


def test_decode_token_garbage_returns_none():
    assert decode_token("isto-nao-e-um-jwt") is None
