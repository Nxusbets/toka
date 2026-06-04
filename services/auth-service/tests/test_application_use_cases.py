import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException

from src.config import Settings
from src.domain.entities.user import User
from src.domain.entities.refresh_token import RefreshToken
from src.application.dto.auth_dto import RegisterRequest, LoginRequest, RefreshRequest
from src.application.use_cases.auth_use_cases import (
    RegisterUserUseCase,
    LoginUseCase,
    RefreshTokenUseCase,
    LogoutUseCase,
    ValidateTokenUseCase,
    hash_password,
    verify_password,
    hash_token,
    create_access_token,
    create_refresh_token,
)


pytestmark = pytest.mark.asyncio


class TestRegisterUserUseCase:
    async def test_register_success(self, mock_user_repo, mock_refresh_token_repo, mock_event_publisher, settings, sample_user):
        mock_user_repo.get_by_email.return_value = None
        mock_user_repo.get_by_username.return_value = None
        mock_user_repo.create.return_value = sample_user
        mock_refresh_token_repo.create.return_value = RefreshToken(
            id=uuid4(), user_id=sample_user.id, token_hash="hash",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )

        use_case = RegisterUserUseCase(mock_user_repo, mock_refresh_token_repo, mock_event_publisher, settings)
        request = RegisterRequest(email="test@example.com", username="testuser", password="password123")
        result = await use_case.execute(request)

        assert result.access_token is not None
        assert result.refresh_token is not None
        assert result.token_type == "bearer"
        mock_user_repo.create.assert_called_once()
        mock_event_publisher.publish.assert_called_once()

    async def test_register_duplicate_email(self, mock_user_repo, mock_refresh_token_repo, mock_event_publisher, settings, sample_user):
        mock_user_repo.get_by_email.return_value = sample_user

        use_case = RegisterUserUseCase(mock_user_repo, mock_refresh_token_repo, mock_event_publisher, settings)
        request = RegisterRequest(email="test@example.com", username="testuser", password="password123")

        with pytest.raises(HTTPException) as exc:
            await use_case.execute(request)
        assert exc.value.status_code == 409
        assert "Email already registered" in exc.value.detail

    async def test_register_duplicate_username(self, mock_user_repo, mock_refresh_token_repo, mock_event_publisher, settings, sample_user):
        mock_user_repo.get_by_email.return_value = None
        mock_user_repo.get_by_username.return_value = sample_user

        use_case = RegisterUserUseCase(mock_user_repo, mock_refresh_token_repo, mock_event_publisher, settings)
        request = RegisterRequest(email="test@example.com", username="existinguser", password="password123")

        with pytest.raises(HTTPException) as exc:
            await use_case.execute(request)
        assert exc.value.status_code == 409
        assert "Username already taken" in exc.value.detail


class TestLoginUseCase:
    async def test_login_success(self, mock_user_repo, mock_refresh_token_repo, mock_event_publisher, settings, sample_user):
        sample_user.password_hash = hash_password("password123")
        mock_user_repo.get_by_email.return_value = sample_user
        mock_refresh_token_repo.create.return_value = RefreshToken(
            id=uuid4(), user_id=sample_user.id, token_hash="hash",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )

        use_case = LoginUseCase(mock_user_repo, mock_refresh_token_repo, mock_event_publisher, settings)
        request = LoginRequest(email="test@example.com", password="password123")
        result = await use_case.execute(request)

        assert result.access_token is not None
        assert result.refresh_token is not None

    async def test_login_invalid_credentials(self, mock_user_repo, mock_refresh_token_repo, mock_event_publisher, settings):
        mock_user_repo.get_by_email.return_value = None

        use_case = LoginUseCase(mock_user_repo, mock_refresh_token_repo, mock_event_publisher, settings)
        request = LoginRequest(email="wrong@example.com", password="wrongpass")

        with pytest.raises(HTTPException) as exc:
            await use_case.execute(request)
        assert exc.value.status_code == 401

    async def test_login_inactive_user(self, mock_user_repo, mock_refresh_token_repo, mock_event_publisher, settings):
        user = User(
            id=uuid4(), email="inactive@example.com", username="inactive",
            password_hash=hash_password("password123"), is_active=False,
        )
        mock_user_repo.get_by_email.return_value = user

        use_case = LoginUseCase(mock_user_repo, mock_refresh_token_repo, mock_event_publisher, settings)
        request = LoginRequest(email="inactive@example.com", password="password123")

        with pytest.raises(HTTPException) as exc:
            await use_case.execute(request)
        assert exc.value.status_code == 403
        assert "Account is inactive" in exc.value.detail


class TestRefreshTokenUseCase:
    async def test_refresh_success(self, mock_refresh_token_repo, settings, sample_refresh_token):
        token_str = create_refresh_token(sample_refresh_token.user_id, settings)
        token_hash = hash_token(token_str)
        sample_refresh_token.token_hash = token_hash
        sample_refresh_token.expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        mock_refresh_token_repo.get_by_token_hash.return_value = sample_refresh_token
        mock_refresh_token_repo.create.return_value = RefreshToken(
            id=uuid4(), user_id=sample_refresh_token.user_id, token_hash="newhash",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )

        use_case = RefreshTokenUseCase(mock_refresh_token_repo, settings)
        request = RefreshRequest(refresh_token=token_str)
        result = await use_case.execute(request)

        assert result.access_token is not None
        assert result.refresh_token is not None
        mock_refresh_token_repo.revoke.assert_called_once_with(sample_refresh_token.id)

    async def test_refresh_invalid_token_type(self, mock_refresh_token_repo, settings):
        access_token = create_access_token(uuid4(), "test@example.com", settings)

        use_case = RefreshTokenUseCase(mock_refresh_token_repo, settings)
        request = RefreshRequest(refresh_token=access_token)

        with pytest.raises(HTTPException) as exc:
            await use_case.execute(request)
        assert exc.value.status_code == 401
        assert "Invalid token type" in exc.value.detail

    async def test_refresh_revoked_token(self, mock_refresh_token_repo, settings, sample_refresh_token):
        token_str = create_refresh_token(sample_refresh_token.user_id, settings)
        token_hash = hash_token(token_str)
        sample_refresh_token.token_hash = token_hash
        sample_refresh_token.revoked = True
        mock_refresh_token_repo.get_by_token_hash.return_value = sample_refresh_token

        use_case = RefreshTokenUseCase(mock_refresh_token_repo, settings)
        request = RefreshRequest(refresh_token=token_str)

        with pytest.raises(HTTPException) as exc:
            await use_case.execute(request)
        assert exc.value.status_code == 401


class TestLogoutUseCase:
    async def test_logout_success(self, mock_refresh_token_repo, mock_event_publisher, settings):
        user_id = uuid4()
        use_case = LogoutUseCase(mock_refresh_token_repo, mock_event_publisher, settings)
        await use_case.execute(user_id, "access_token_string")

        mock_refresh_token_repo.revoke_all_for_user.assert_called_once_with(user_id)
        mock_event_publisher.publish.assert_called_once()


class TestValidateTokenUseCase:
    async def test_validate_valid_token(self, settings):
        user_id = uuid4()
        token = create_access_token(user_id, "test@example.com", settings)

        use_case = ValidateTokenUseCase(settings)
        result = await use_case.execute(token)

        assert result["user_id"] == str(user_id)
        assert result["email"] == "test@example.com"
        assert result["token_type"] == "access"

    async def test_validate_expired_token(self, settings):
        settings.jwt_access_token_expire_minutes = -1
        user_id = uuid4()
        token = create_access_token(user_id, "test@example.com", settings)

        use_case = ValidateTokenUseCase(settings)
        with pytest.raises(HTTPException) as exc:
            await use_case.execute(token)
        assert exc.value.status_code == 401
        assert "Token expired" in exc.value.detail


class TestHelperFunctions:
    def test_hash_password(self):
        hashed = hash_password("password123")
        assert hashed != "password123"
        assert hashed.startswith("$2b$")

    def test_verify_password(self):
        hashed = hash_password("password123")
        assert verify_password("password123", hashed) is True
        assert verify_password("wrongpass", hashed) is False

    def test_hash_token(self):
        token = "my-refresh-token-string"
        hashed = hash_token(token)
        assert hashed != token
        assert len(hashed) == 64

    def test_create_access_token(self, settings):
        user_id = uuid4()
        token = create_access_token(user_id, "test@example.com", settings)
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token(self, settings):
        user_id = uuid4()
        token = create_refresh_token(user_id, settings)
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
