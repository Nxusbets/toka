from __future__ import annotations
from uuid import UUID
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, update, delete, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.user import User
from src.domain.entities.role import Role
from src.domain.entities.permission import Permission
from src.domain.repositories import UserRepository, RoleRepository, PermissionRepository
from src.infrastructure.database.models import (
    UserModel,
    RoleModel,
    PermissionModel,
    UserRoleModel,
    RolePermissionModel,
)


class SQLAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user: User) -> User:
        model = UserModel(
            id=user.id,
            email=user.email,
            username=user.username,
            is_active=user.is_active,
        )
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def get_by_id(self, user_id: UUID) -> User | None:
        result = await self.session.execute(select(UserModel).where(UserModel.id == user_id))
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(UserModel).where(UserModel.email == email))
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_username(self, username: str) -> User | None:
        result = await self.session.execute(select(UserModel).where(UserModel.username == username))
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list(
        self, skip: int = 0, limit: int = 100, role_id: UUID | None = None, is_active: bool | None = None
    ) -> list[User]:
        query = select(UserModel)
        if role_id:
            query = query.join(UserRoleModel).where(UserRoleModel.role_id == role_id)
        if is_active is not None:
            query = query.where(UserModel.is_active == is_active)
        query = query.offset(skip).limit(limit).order_by(UserModel.created_at.desc())
        result = await self.session.execute(query)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def count(self, role_id: UUID | None = None, is_active: bool | None = None) -> int:
        query = select(func.count(UserModel.id))
        if role_id:
            query = query.join(UserRoleModel).where(UserRoleModel.role_id == role_id)
        if is_active is not None:
            query = query.where(UserModel.is_active == is_active)
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def update(self, user: User) -> User:
        await self.session.execute(
            update(UserModel)
            .where(UserModel.id == user.id)
            .values(
                email=user.email,
                username=user.username,
                is_active=user.is_active,
                updated_at=datetime.now(timezone.utc),
            )
        )
        await self.session.commit()
        return user

    async def delete(self, user_id: UUID) -> None:
        await self.session.execute(delete(UserModel).where(UserModel.id == user_id))
        await self.session.commit()

    async def get_roles(self, user_id: UUID) -> list[Role]:
        result = await self.session.execute(
            select(RoleModel)
            .join(UserRoleModel)
            .where(UserRoleModel.user_id == user_id)
        )
        return [self._role_to_entity(m) for m in result.scalars().all()]

    async def assign_role(self, user_id: UUID, role_id: UUID, assigned_by: UUID | None = None) -> None:
        existing = await self.session.execute(
            select(UserRoleModel).where(
                UserRoleModel.user_id == user_id, UserRoleModel.role_id == role_id
            )
        )
        if existing.scalar_one_or_none():
            return
        model = UserRoleModel(user_id=user_id, role_id=role_id, assigned_by=assigned_by)
        self.session.add(model)
        await self.session.commit()

    async def remove_role(self, user_id: UUID, role_id: UUID) -> None:
        await self.session.execute(
            delete(UserRoleModel).where(
                UserRoleModel.user_id == user_id, UserRoleModel.role_id == role_id
            )
        )
        await self.session.commit()

    @staticmethod
    def _to_entity(model: UserModel) -> User:
        return User(
            id=model.id,
            email=model.email,
            username=model.username,
            is_active=model.is_active,
            created_at=model.created_at.replace(tzinfo=None) if model.created_at else datetime.utcnow(),
            updated_at=model.updated_at.replace(tzinfo=None) if model.updated_at else datetime.utcnow(),
        )

    @staticmethod
    def _role_to_entity(model: RoleModel) -> Role:
        return Role(
            id=model.id,
            name=model.name,
            description=model.description or "",
            is_system=model.is_system,
            created_at=model.created_at.replace(tzinfo=None) if model.created_at else datetime.utcnow(),
            updated_at=model.updated_at.replace(tzinfo=None) if model.updated_at else datetime.utcnow(),
        )


class SQLAlchemyRoleRepository(RoleRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, role: Role) -> Role:
        model = RoleModel(
            id=role.id,
            name=role.name,
            description=role.description,
            is_system=role.is_system,
        )
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def get_by_id(self, role_id: UUID) -> Role | None:
        result = await self.session.execute(select(RoleModel).where(RoleModel.id == role_id))
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_name(self, name: str) -> Role | None:
        result = await self.session.execute(select(RoleModel).where(RoleModel.name == name))
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list(self, skip: int = 0, limit: int = 100) -> list[Role]:
        result = await self.session.execute(
            select(RoleModel).offset(skip).limit(limit).order_by(RoleModel.created_at.desc())
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def count(self) -> int:
        result = await self.session.execute(select(func.count(RoleModel.id)))
        return result.scalar() or 0

    async def update(self, role: Role) -> Role:
        await self.session.execute(
            update(RoleModel)
            .where(RoleModel.id == role.id)
            .values(
                name=role.name,
                description=role.description,
                updated_at=datetime.now(timezone.utc),
            )
        )
        await self.session.commit()
        return role

    async def delete(self, role_id: UUID) -> None:
        await self.session.execute(delete(RoleModel).where(RoleModel.id == role_id))
        await self.session.commit()

    async def get_permissions(self, role_id: UUID) -> list[Permission]:
        result = await self.session.execute(
            select(PermissionModel)
            .join(RolePermissionModel)
            .where(RolePermissionModel.role_id == role_id)
        )
        return [self._perm_to_entity(m) for m in result.scalars().all()]

    async def set_permissions(self, role_id: UUID, permission_ids: list[UUID]) -> None:
        await self.session.execute(
            delete(RolePermissionModel).where(RolePermissionModel.role_id == role_id)
        )
        for pid in permission_ids:
            self.session.add(RolePermissionModel(role_id=role_id, permission_id=pid))
        await self.session.commit()

    @staticmethod
    def _to_entity(model: RoleModel) -> Role:
        return Role(
            id=model.id,
            name=model.name,
            description=model.description or "",
            is_system=model.is_system,
            created_at=model.created_at.replace(tzinfo=None) if model.created_at else datetime.utcnow(),
            updated_at=model.updated_at.replace(tzinfo=None) if model.updated_at else datetime.utcnow(),
        )

    @staticmethod
    def _perm_to_entity(model: PermissionModel) -> Permission:
        return Permission(
            id=model.id,
            name=model.name,
            resource=model.resource,
            action=model.action,
            description=model.description or "",
            created_at=model.created_at.replace(tzinfo=None) if model.created_at else datetime.utcnow(),
        )


class SQLAlchemyPermissionRepository(PermissionRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, permission_id: UUID) -> Permission | None:
        result = await self.session.execute(
            select(PermissionModel).where(PermissionModel.id == permission_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list(self, skip: int = 0, limit: int = 100) -> list[Permission]:
        result = await self.session.execute(
            select(PermissionModel).offset(skip).limit(limit).order_by(PermissionModel.name)
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def count(self) -> int:
        result = await self.session.execute(select(func.count(PermissionModel.id)))
        return result.scalar() or 0

    @staticmethod
    def _to_entity(model: PermissionModel) -> Permission:
        return Permission(
            id=model.id,
            name=model.name,
            resource=model.resource,
            action=model.action,
            description=model.description or "",
            created_at=model.created_at.replace(tzinfo=None) if model.created_at else datetime.utcnow(),
        )
