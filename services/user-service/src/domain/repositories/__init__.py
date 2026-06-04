from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.user import User
from src.domain.entities.role import Role
from src.domain.entities.permission import Permission


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
    async def list(self, skip: int = 0, limit: int = 100, role_id: UUID | None = None, is_active: bool | None = None) -> list[User]:
        ...

    @abstractmethod
    async def count(self, role_id: UUID | None = None, is_active: bool | None = None) -> int:
        ...

    @abstractmethod
    async def update(self, user: User) -> User:
        ...

    @abstractmethod
    async def delete(self, user_id: UUID) -> None:
        ...

    @abstractmethod
    async def get_roles(self, user_id: UUID) -> list[Role]:
        ...

    @abstractmethod
    async def assign_role(self, user_id: UUID, role_id: UUID, assigned_by: UUID | None = None) -> None:
        ...

    @abstractmethod
    async def remove_role(self, user_id: UUID, role_id: UUID) -> None:
        ...


class RoleRepository(ABC):
    @abstractmethod
    async def create(self, role: Role) -> Role:
        ...

    @abstractmethod
    async def get_by_id(self, role_id: UUID) -> Role | None:
        ...

    @abstractmethod
    async def get_by_name(self, name: str) -> Role | None:
        ...

    @abstractmethod
    async def list(self, skip: int = 0, limit: int = 100) -> list[Role]:
        ...

    @abstractmethod
    async def count(self) -> int:
        ...

    @abstractmethod
    async def update(self, role: Role) -> Role:
        ...

    @abstractmethod
    async def delete(self, role_id: UUID) -> None:
        ...

    @abstractmethod
    async def get_permissions(self, role_id: UUID) -> list[Permission]:
        ...

    @abstractmethod
    async def set_permissions(self, role_id: UUID, permission_ids: list[UUID]) -> None:
        ...


class PermissionRepository(ABC):
    @abstractmethod
    async def get_by_id(self, permission_id: UUID) -> Permission | None:
        ...

    @abstractmethod
    async def list(self, skip: int = 0, limit: int = 100) -> list[Permission]:
        ...

    @abstractmethod
    async def count(self) -> int:
        ...
