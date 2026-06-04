import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime

from src.config import Settings
from src.domain.entities.user import User
from src.domain.entities.role import Role
from src.domain.entities.permission import Permission
from src.domain.repositories import UserRepository, RoleRepository, PermissionRepository
from src.infrastructure.message_queue import EventPublisher


@pytest.fixture
def settings():
    return Settings(
        service_name="user-service",
        database_url="sqlite+aiosqlite://",
        rabbitmq_url="amqp://localhost:5672/",
        jwt_secret_key="test-secret-key",
        jwt_algorithm="HS256",
    )


@pytest.fixture
def mock_user_repo():
    repo = MagicMock(spec=UserRepository)
    repo.create = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.get_by_email = AsyncMock()
    repo.get_by_username = AsyncMock()
    repo.list = AsyncMock(return_value=[])
    repo.count = AsyncMock(return_value=0)
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    repo.get_roles = AsyncMock(return_value=[])
    repo.assign_role = AsyncMock()
    repo.remove_role = AsyncMock()
    return repo


@pytest.fixture
def mock_role_repo():
    repo = MagicMock(spec=RoleRepository)
    repo.create = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.get_by_name = AsyncMock()
    repo.list = AsyncMock(return_value=[])
    repo.count = AsyncMock(return_value=0)
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    repo.get_permissions = AsyncMock(return_value=[])
    repo.set_permissions = AsyncMock()
    return repo


@pytest.fixture
def mock_permission_repo():
    repo = MagicMock(spec=PermissionRepository)
    repo.get_by_id = AsyncMock()
    repo.list = AsyncMock(return_value=[])
    repo.count = AsyncMock(return_value=0)
    return repo


@pytest.fixture
def mock_event_publisher():
    publisher = MagicMock(spec=EventPublisher)
    publisher.publish = AsyncMock()
    return publisher


@pytest.fixture
def sample_user():
    return User(
        id=uuid4(),
        email="test@example.com",
        username="testuser",
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_role():
    return Role(
        id=uuid4(),
        name="admin",
        description="Administrator role",
        is_system=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_permission():
    return Permission(
        id=uuid4(),
        name="user:read",
        resource="user",
        action="read",
        description="Read users",
        created_at=datetime.utcnow(),
    )
