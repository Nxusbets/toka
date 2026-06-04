import pytest
from uuid import UUID
from datetime import datetime
from pydantic import ValidationError

from src.application.dto.auth_dto import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    UserResponse,
)


class TestRegisterRequest:
    def test_valid_register_request(self):
        dto = RegisterRequest(email="test@example.com", username="testuser", password="password123")
        assert dto.email == "test@example.com"
        assert dto.username == "testuser"
        assert dto.password == "password123"

    def test_invalid_email(self):
        with pytest.raises(ValidationError):
            RegisterRequest(email="not-an-email", username="testuser", password="password123")

    def test_email_too_long(self):
        with pytest.raises(ValidationError):
            RegisterRequest(
                email="a" * 256 + "@example.com",
                username="testuser",
                password="password123",
            )

    def test_username_too_short(self):
        with pytest.raises(ValidationError):
            RegisterRequest(email="test@example.com", username="ab", password="password123")

    def test_username_too_long(self):
        with pytest.raises(ValidationError):
            RegisterRequest(email="test@example.com", username="a" * 101, password="password123")

    def test_password_too_short(self):
        with pytest.raises(ValidationError):
            RegisterRequest(email="test@example.com", username="testuser", password="short")

    def test_password_too_long(self):
        with pytest.raises(ValidationError):
            RegisterRequest(email="test@example.com", username="testuser", password="a" * 129)

    def test_missing_fields(self):
        with pytest.raises(ValidationError):
            RegisterRequest()


class TestLoginRequest:
    def test_valid_login_request(self):
        dto = LoginRequest(email="test@example.com", password="password123")
        assert dto.email == "test@example.com"
        assert dto.password == "password123"

    def test_invalid_login_email(self):
        with pytest.raises(ValidationError):
            LoginRequest(email="invalid", password="password123")

    def test_missing_login_fields(self):
        with pytest.raises(ValidationError):
            LoginRequest()


class TestTokenResponse:
    def test_valid_token_response(self):
        dto = TokenResponse(access_token="abc", refresh_token="def")
        assert dto.access_token == "abc"
        assert dto.refresh_token == "def"
        assert dto.token_type == "bearer"

    def test_custom_token_type(self):
        dto = TokenResponse(access_token="abc", refresh_token="def", token_type="custom")
        assert dto.token_type == "custom"

    def test_missing_token_fields(self):
        with pytest.raises(ValidationError):
            TokenResponse()


class TestRefreshRequest:
    def test_valid_refresh_request(self):
        dto = RefreshRequest(refresh_token="some-token")
        assert dto.refresh_token == "some-token"

    def test_missing_refresh_token(self):
        with pytest.raises(ValidationError):
            RefreshRequest()


class TestUserResponse:
    def test_valid_user_response(self):
        now = datetime.utcnow()
        dto = UserResponse(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            email="test@example.com",
            username="testuser",
            is_active=True,
            is_verified=True,
            created_at=now,
            updated_at=now,
        )
        assert dto.email == "test@example.com"
        assert dto.is_active is True
        assert dto.is_verified is True

    def test_user_response_defaults(self):
        now = datetime.utcnow()
        dto = UserResponse(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            email="test@example.com",
            username="testuser",
            is_active=False,
            is_verified=False,
            created_at=now,
            updated_at=now,
        )
        assert dto.is_active is False
        assert dto.is_verified is False

    def test_missing_user_response_fields(self):
        with pytest.raises(ValidationError):
            UserResponse()
