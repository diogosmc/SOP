"""Security unit tests."""

import pytest
from jose import jwt

from app.core.config import Settings
from app.core.security import (
    TOKEN_TYPE_ACCESS,
    TOKEN_TYPE_REFRESH,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_hash_and_verify_password() -> None:
    hashed = hash_password("secret-password")
    assert hashed != "secret-password"
    assert verify_password("secret-password", hashed)
    assert not verify_password("wrong", hashed)
    assert not verify_password("secret-password", None)


def test_create_and_decode_access_token() -> None:
    settings = Settings(
        jwt_secret_key="test-secret-key-for-jwt-signing-32chars",
        jwt_access_token_expire_minutes=30,
    )
    token = create_access_token("user-123", settings)
    payload = decode_token(token, settings, expected_type=TOKEN_TYPE_ACCESS)
    assert payload is not None
    assert payload["sub"] == "user-123"
    assert payload["type"] == TOKEN_TYPE_ACCESS


def test_create_and_decode_refresh_token() -> None:
    settings = Settings(
        jwt_secret_key="test-secret-key-for-jwt-signing-32chars",
        jwt_refresh_token_expire_days=7,
    )
    token = create_refresh_token("user-456", settings)
    payload = decode_token(token, settings, expected_type=TOKEN_TYPE_REFRESH)
    assert payload is not None
    assert payload["sub"] == "user-456"


def test_decode_rejects_wrong_type() -> None:
    settings = Settings(jwt_secret_key="test-secret-key-for-jwt-signing-32chars")
    access = create_access_token("user-1", settings)
    assert decode_token(access, settings, expected_type=TOKEN_TYPE_REFRESH) is None


def test_decode_invalid_token() -> None:
    settings = Settings(jwt_secret_key="test-secret-key-for-jwt-signing-32chars")
    assert decode_token("not-a-token", settings) is None


def test_expired_token_returns_none() -> None:
    settings = Settings(jwt_secret_key="test-secret-key-for-jwt-signing-32chars")
    expired = jwt.encode(
        {"sub": "u", "type": TOKEN_TYPE_ACCESS, "exp": 1},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    assert decode_token(expired, settings, expected_type=TOKEN_TYPE_ACCESS) is None
