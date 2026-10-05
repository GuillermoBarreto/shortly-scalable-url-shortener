"""Tests for app.core.security: token issuance, password handling, visitor hashing."""

from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.core.config import Settings
from app.core.security import (
    create_token,
    decode_token,
    hash_password,
    verify_password,
    visitor_hash,
)


@pytest.fixture()
def settings() -> Settings:
    return Settings(secret_key="test-secret-key", analytics_salt="test-salt")


def test_create_token_round_trip(settings: Settings) -> None:
    user_id = uuid4()
    token = create_token(user_id, "access", settings)
    payload = decode_token(token, "access", settings)
    assert payload["sub"] == str(user_id)
    assert payload["type"] == "access"


def test_create_token_rejects_unknown_type(settings: Settings) -> None:
    with pytest.raises(ValueError, match="Unknown token type"):
        create_token(uuid4(), "mystery", settings)


def test_decode_token_rejects_wrong_type(settings: Settings) -> None:
    token = create_token(uuid4(), "refresh", settings)
    with pytest.raises(HTTPException) as exc_info:
        decode_token(token, "access", settings)
    assert exc_info.value.status_code == 401


def test_decode_token_rejects_garbage(settings: Settings) -> None:
    with pytest.raises(HTTPException) as exc_info:
        decode_token("not-a-token", "access", settings)
    assert exc_info.value.status_code == 401


def test_password_round_trip() -> None:
    hashed = hash_password("correct horse battery staple")
    assert verify_password("correct horse battery staple", hashed) is True
    assert verify_password("wrong password", hashed) is False


def test_verify_password_fails_closed_on_garbage() -> None:
    assert verify_password("anything", "not-a-valid-hash") is False
    assert verify_password("anything", "") is False


def test_visitor_hash_is_stable_within_a_day(settings: Settings) -> None:
    assert visitor_hash("1.2.3.4", settings) == visitor_hash("1.2.3.4", settings)


def test_visitor_hash_differs_per_ip_and_salt(settings: Settings) -> None:
    other = Settings(secret_key="test-secret-key", analytics_salt="other-salt")
    assert visitor_hash("1.2.3.4", settings) != visitor_hash("5.6.7.8", settings)
    assert visitor_hash("1.2.3.4", settings) != visitor_hash("1.2.3.4", other)
