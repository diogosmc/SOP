"""Security utilities tests."""

from app.core.security import hash_password, verify_password, create_access_token, decode_token
from app.core.config import get_settings


def test_password_hash_and_verify() -> None:
    hashed = hash_password("secret123")
    assert verify_password("secret123", hashed)
    assert not verify_password("wrong", hashed)


def test_jwt_create_and_decode() -> None:
    settings = get_settings()
    token = create_access_token("user-123", settings)
    payload = decode_token(token, settings, expected_type="access")
    assert payload is not None
    assert payload["sub"] == "user-123"
