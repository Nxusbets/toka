from __future__ import annotations
from uuid import UUID
from datetime import datetime, timezone

from fastapi import HTTPException, status

from src.config import Settings
from src.domain.entities.user import User
from src.domain.entities.role import Role
from src.domain.entities.permission import Permission
from src.domain.events import UserUpdated, RoleAssigned
from src.domain.repositories import UserRepository, RoleRepository, PermissionRepository
from src.infrastructure.message_queue import EventPublisher
from src.application.dto.user_dto import (
    CreateUserRequest,
    UpdateUserRequest,
    UserResponse,
    RoleResponse,
    PermissionResponse,
    AssignRoleRequest,
    CreateRoleRequest,
    UpdateRoleRequest,
    PaginatedResponse,
)


def _user_to_response(user: User, roles: list[Role] | None = None) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
        roles=[_role_to_response(r) for r in (roles or [])],
    )


def _role_to_response(role: Role, permissions: list[Permission] | None = None) -> RoleResponse:
    return RoleResponse(
        id=role.id,
        name=role.name,
        description=role.description,
        is_system=role.is_system,
        created_at=role.created_at,
        updated_at=role.updated_at,
        permissions=[_permission_to_response(p) for p in (permissions or [])],
    )


def _permission_to_response(perm: Permission) -> PermissionResponse:
    return PermissionResponse(
        id=perm.id,
        name=perm.name,
        resource=perm.resource,
        action=perm.action,
        description=perm.description,
        created_at=perm.created_at,
    )


def _paginate(items: list, total: int, page: int, page_size: int) -> PaginatedResponse:
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=max(1, (total + page_size - 1) // page_size),
    )


class CreateUserUseCase:
    def __init__(self, user_repo: UserRepository, event_publisher: EventPublisher):
        self.user_repo = user_repo
        self.event_publisher = event_publisher

    async def execute(self, request: CreateUserRequest) -> UserResponse:
        existing = await self.user_repo.get_by_email(request.email)
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")

        existing = await self.user_repo.get_by_username(request.username)
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")

        user = User(email=request.email, username=request.username)
        created = await self.user_repo.create(user)

        await self.event_publisher.publish(
            UserUpdated(
                event_type="user.updated",
                user_id=created.id,
                email=created.email,
                username=created.username,
            )
        )

        return _user_to_response(created)


class GetUserUseCase:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def execute(self, user_id: UUID) -> UserResponse:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        roles = await self.user_repo.get_roles(user_id)
        return _user_to_response(user, roles)


class ListUsersUseCase:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def execute(
        self, page: int = 1, page_size: int = 20, role_id: UUID | None = None, is_active: bool | None = None
    ) -> PaginatedResponse:
        skip = (page - 1) * page_size
        users = await self.user_repo.list(skip=skip, limit=page_size, role_id=role_id, is_active=is_active)
        total = await self.user_repo.count(role_id=role_id, is_active=is_active)
        items = []
        for u in users:
            roles = await self.user_repo.get_roles(u.id)
            items.append(_user_to_response(u, roles))
        return _paginate(items, total, page, page_size)


class UpdateUserUseCase:
    def __init__(self, user_repo: UserRepository, event_publisher: EventPublisher):
        self.user_repo = user_repo
        self.event_publisher = event_publisher

    async def execute(self, user_id: UUID, request: UpdateUserRequest) -> UserResponse:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        changed = False
        if request.email is not None and request.email != user.email:
            existing = await self.user_repo.get_by_email(request.email)
            if existing and existing.id != user_id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")
            user.email = request.email
            changed = True

        if request.username is not None and request.username != user.username:
            existing = await self.user_repo.get_by_username(request.username)
            if existing and existing.id != user_id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")
            user.username = request.username
            changed = True

        if request.is_active is not None:
            user.is_active = request.is_active
            changed = True

        if not changed:
            roles = await self.user_repo.get_roles(user_id)
            return _user_to_response(user, roles)

        user.updated_at = datetime.utcnow()
        updated = await self.user_repo.update(user)

        await self.event_publisher.publish(
            UserUpdated(
                event_type="user.updated",
                user_id=updated.id,
                email=updated.email,
                username=updated.username,
                is_active=updated.is_active,
            )
        )

        roles = await self.user_repo.get_roles(user_id)
        return _user_to_response(updated, roles)


class DeleteUserUseCase:
    def __init__(self, user_repo: UserRepository, event_publisher: EventPublisher):
        self.user_repo = user_repo
        self.event_publisher = event_publisher

    async def execute(self, user_id: UUID) -> None:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        await self.user_repo.delete(user_id)

        await self.event_publisher.publish(
            UserUpdated(
                event_type="user.updated",
                user_id=user_id,
                is_active=False,
            )
        )


class AssignRoleUseCase:
    def __init__(self, user_repo: UserRepository, role_repo: RoleRepository, event_publisher: EventPublisher):
        self.user_repo = user_repo
        self.role_repo = role_repo
        self.event_publisher = event_publisher

    async def execute(self, user_id: UUID, request: AssignRoleRequest, assigned_by: UUID | None = None) -> UserResponse:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        role = await self.role_repo.get_by_id(request.role_id)
        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

        await self.user_repo.assign_role(user_id, request.role_id, assigned_by)

        await self.event_publisher.publish(
            RoleAssigned(
                event_type="role.assigned",
                user_id=user_id,
                role_id=request.role_id,
                role_name=role.name,
                assigned_by=assigned_by,
            )
        )

        roles = await self.user_repo.get_roles(user_id)
        return _user_to_response(user, roles)


class RemoveRoleUseCase:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def execute(self, user_id: UUID, role_id: UUID) -> UserResponse:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        await self.user_repo.remove_role(user_id, role_id)
        roles = await self.user_repo.get_roles(user_id)
        return _user_to_response(user, roles)


class CreateRoleUseCase:
    def __init__(self, role_repo: RoleRepository):
        self.role_repo = role_repo

    async def execute(self, request: CreateRoleRequest) -> RoleResponse:
        existing = await self.role_repo.get_by_name(request.name)
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Role already exists")

        role = Role(name=request.name, description=request.description)
        created = await self.role_repo.create(role)
        return _role_to_response(created)


class ListRolesUseCase:
    def __init__(self, role_repo: RoleRepository, permission_repo: PermissionRepository):
        self.role_repo = role_repo
        self.permission_repo = permission_repo

    async def execute(self, page: int = 1, page_size: int = 20) -> PaginatedResponse:
        skip = (page - 1) * page_size
        roles = await self.role_repo.list(skip=skip, limit=page_size)
        total = await self.role_repo.count()
        items = []
        for r in roles:
            perms = await self.role_repo.get_permissions(r.id)
            items.append(_role_to_response(r, perms))
        return _paginate(items, total, page, page_size)


class GetRoleUseCase:
    def __init__(self, role_repo: RoleRepository):
        self.role_repo = role_repo

    async def execute(self, role_id: UUID) -> RoleResponse:
        role = await self.role_repo.get_by_id(role_id)
        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
        permissions = await self.role_repo.get_permissions(role_id)
        return _role_to_response(role, permissions)


class UpdateRoleUseCase:
    def __init__(self, role_repo: RoleRepository):
        self.role_repo = role_repo

    async def execute(self, role_id: UUID, request: UpdateRoleRequest) -> RoleResponse:
        role = await self.role_repo.get_by_id(role_id)
        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

        if role.is_system:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot modify system roles")

        if request.name is not None:
            existing = await self.role_repo.get_by_name(request.name)
            if existing and existing.id != role_id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Role name already exists")
            role.name = request.name

        if request.description is not None:
            role.description = request.description

        role.updated_at = datetime.utcnow()
        updated = await self.role_repo.update(role)
        permissions = await self.role_repo.get_permissions(role_id)
        return _role_to_response(updated, permissions)


class DeleteRoleUseCase:
    def __init__(self, role_repo: RoleRepository):
        self.role_repo = role_repo

    async def execute(self, role_id: UUID) -> None:
        role = await self.role_repo.get_by_id(role_id)
        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
        if role.is_system:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot delete system roles")
        await self.role_repo.delete(role_id)


class ListPermissionsUseCase:
    def __init__(self, permission_repo: PermissionRepository):
        self.permission_repo = permission_repo

    async def execute(self, page: int = 1, page_size: int = 100) -> PaginatedResponse:
        skip = (page - 1) * page_size
        perms = await self.permission_repo.list(skip=skip, limit=page_size)
        total = await self.permission_repo.count()
        items = [_permission_to_response(p) for p in perms]
        return _paginate(items, total, page, page_size)


class GetRolePermissionsUseCase:
    def __init__(self, role_repo: RoleRepository):
        self.role_repo = role_repo

    async def execute(self, role_id: UUID) -> list[PermissionResponse]:
        role = await self.role_repo.get_by_id(role_id)
        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
        permissions = await self.role_repo.get_permissions(role_id)
        return [_permission_to_response(p) for p in permissions]


class SyncUserUseCase:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def execute(self, user_id: UUID, email: str, username: str) -> None:
        existing = await self.user_repo.get_by_id(user_id)
        if existing:
            existing.email = email
            existing.username = username
            existing.updated_at = datetime.utcnow()
            await self.user_repo.update(existing)
        else:
            user = User(id=user_id, email=email, username=username)
            await self.user_repo.create(user)
