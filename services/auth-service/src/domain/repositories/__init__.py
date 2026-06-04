from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.user import User
from src.domain.entities.refresh_token import RefreshToken


class UserRepository(ABC):
    @abstractmethod
    async def create(self, user: User) -> User:
        ...

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> User | None:
        ...

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        ...

    @abstractmethod
    async def get_by_username(self, username: str) -> User | None:
        ...

    @abstractmethod
    async def update(self, user: User) -> User:
        ...


class RefreshTokenRepository(ABC):
    @abstractmethod
    async def create(self, token: RefreshToken) -> RefreshToken:
        ...

    @abstractmethod
    async def get_by_token_hash(self, token_hash: str) -> RefreshToken | None:
        ...

    @abstractmethod
    async def revoke(self, token_id: UUID) -> None:
        ...

    @abstractmethod
    async def revoke_all_for_user(self, user_id: UUID) -> None:
        ...
