from uuid import UUID, uuid4
from datetime import datetime

from src.domain.entities.user import User
from src.domain.entities.role import Role
from src.domain.entities.permission import Permission


class TestUserEntity:
    def test_user_creation_with_defaults(self):
        user = User()
        assert isinstance(user.id, UUID)
        assert user.email == ""
        assert user.username == ""
        assert user.is_active is True
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)

    def test_user_creation_with_values(self):
        user_id = uuid4()
        now = datetime.utcnow()
        user = User(
            id=user_id,
            email="test@example.com",
            username="testuser",
            is_active=False,
            created_at=now,
            updated_at=now,
        )
        assert user.id == user_id
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.is_active is False
        assert user.created_at == now

    def test_user_inactive(self):
        user = User(is_active=False)
        assert user.is_active is False

    def test_user_equality_by_id(self):
        user_id = uuid4()
        user1 = User(id=user_id)
        user2 = User(id=user_id)
        assert user1 == user2

    def test_user_different_ids_not_equal(self):
        assert User() != User()


class TestRoleEntity:
    def test_role_creation_with_defaults(self):
        role = Role()
        assert isinstance(role.id, UUID)
        assert role.name == ""
        assert role.description == ""
        assert role.is_system is False
        assert isinstance(role.created_at, datetime)
        assert isinstance(role.updated_at, datetime)

    def test_role_creation_with_values(self):
        role_id = uuid4()
        now = datetime.utcnow()
        role = Role(
            id=role_id,
            name="admin",
            description="Admin role",
            is_system=True,
            created_at=now,
            updated_at=now,
        )
        assert role.id == role_id
        assert role.name == "admin"
        assert role.is_system is True
        assert role.description == "Admin role"

    def test_role_system_flag(self):
        assert Role(is_system=True).is_system is True
        assert Role().is_system is False


class TestPermissionEntity:
    def test_permission_creation_with_defaults(self):
        perm = Permission()
        assert isinstance(perm.id, UUID)
        assert perm.name == ""
        assert perm.resource == ""
        assert perm.action == ""
        assert perm.description == ""
        assert isinstance(perm.created_at, datetime)

    def test_permission_creation_with_values(self):
        perm_id = uuid4()
        now = datetime.utcnow()
        perm = Permission(
            id=perm_id,
            name="user:read",
            resource="user",
            action="read",
            description="Read users",
            created_at=now,
        )
        assert perm.id == perm_id
        assert perm.name == "user:read"
        assert perm.resource == "user"
        assert perm.action == "read"
        assert perm.description == "Read users"
