import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime, timedelta, timezone

from src.config import Settings
from src.domain.entities.user import User
from src.domain.entities.refresh_token import RefreshToken
from src.domain.repositories import UserRepository, RefreshTokenRepository
from src.infrastructure.message_queue import EventPublisher


@pytest.fixture
def settings():
    return Settings(
        service_name="auth-service",
        database_url="sqlite+aiosqlite://",
        redis_url="redis://localhost:6379/0",
        rabbitmq_url="amqp://localhost:5672/",
        jwt_secret_key="test-secret-key",
        jwt_algorithm="HS256",
        jwt_access_token_expire_minutes=30,
        jwt_refresh_token_expire_days=7,
    )


@pytest.fixture
def mock_user_repo():
    repo = MagicMock(spec=UserRepository)
    repo.create = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.get_by_email = AsyncMock()
    repo.get_by_username = AsyncMock()
    repo.update = AsyncMock()
    return repo


@pytest.fixture
def mock_refresh_token_repo():
    repo = MagicMock(spec=RefreshTokenRepository)
    repo.create = AsyncMock()
    repo.get_by_token_hash = AsyncMock()
    repo.revoke = AsyncMock()
    repo.revoke_all_for_user = AsyncMock()
    return repo


@pytest.fixture
def mock_event_publisher():
    publisher = MagicMock(spec=EventPublisher)
    publisher.publish = AsyncMock()
    publisher.connect = AsyncMock()
    publisher.close = AsyncMock()
    return publisher


@pytest.fixture
def sample_user():
    return User(
        id=uuid4(),
        email="test@example.com",
        username="testuser",
        password_hash="$2b$12$hashedpassword",
        is_active=True,
        is_verified=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_refresh_token(sample_user):
    return RefreshToken(
        id=uuid4(),
        user_id=sample_user.id,
        token_hash="abc123hash",
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        created_at=datetime.now(timezone.utc),
        revoked=False,
    )
