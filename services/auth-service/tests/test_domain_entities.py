from uuid import UUID
from datetime import datetime

from src.domain.entities.user import User
from src.domain.entities.refresh_token import RefreshToken


class TestUserEntity:
    def test_user_creation_with_defaults(self):
        user = User()
        assert isinstance(user.id, UUID)
        assert user.email == ""
        assert user.username == ""
        assert user.password_hash == ""
        assert user.is_active is True
        assert user.is_verified is False
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)

    def test_user_creation_with_values(self):
        user_id = UUID("12345678-1234-5678-1234-567812345678")
        now = datetime.utcnow()
        user = User(
            id=user_id,
            email="test@example.com",
            username="testuser",
            password_hash="hashed_pw",
            is_active=True,
            is_verified=True,
            created_at=now,
            updated_at=now,
        )
        assert user.id == user_id
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.password_hash == "hashed_pw"
        assert user.is_active is True
        assert user.is_verified is True
        assert user.created_at == now
        assert user.updated_at == now

    def test_user_equality_by_id(self):
        user_id = uuid4()
        user1 = User(id=user_id, email="a@example.com")
        user2 = User(id=user_id, email="b@example.com")
        assert user1 == user2

    def test_user_different_ids_not_equal(self):
        user1 = User(email="a@example.com")
        user2 = User(email="b@example.com")
        assert user1 != user2


class TestRefreshTokenEntity:
    def test_refresh_token_creation_with_defaults(self):
        token = RefreshToken()
        assert isinstance(token.id, UUID)
        assert isinstance(token.user_id, UUID)
        assert token.token_hash == ""
        assert isinstance(token.expires_at, datetime)
        assert isinstance(token.created_at, datetime)
        assert token.revoked is False

    def test_refresh_token_creation_with_values(self):
        user_id = uuid4()
        now = datetime.utcnow()
        token = RefreshToken(
            user_id=user_id,
            token_hash="sha256hash",
            expires_at=now,
            created_at=now,
            revoked=False,
        )
        assert token.user_id == user_id
        assert token.token_hash == "sha256hash"
        assert token.expires_at == now
        assert token.revoked is False

    def test_refresh_token_revoked(self):
        token = RefreshToken(revoked=True)
        assert token.revoked is True


from uuid import uuid4
