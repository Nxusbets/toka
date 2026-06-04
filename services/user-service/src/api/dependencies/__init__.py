from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings
from src.infrastructure.database import get_session
from src.infrastructure.database.repositories import (
    SQLAlchemyUserRepository,
    SQLAlchemyRoleRepository,
    SQLAlchemyPermissionRepository,
)
from src.infrastructure.message_queue import EventPublisher
from src.application.use_cases.user_use_cases import (
    CreateUserUseCase,
    GetUserUseCase,
    ListUsersUseCase,
    UpdateUserUseCase,
    DeleteUserUseCase,
    AssignRoleUseCase,
    RemoveRoleUseCase,
    CreateRoleUseCase,
    ListRolesUseCase,
    GetRoleUseCase,
    UpdateRoleUseCase,
    DeleteRoleUseCase,
    ListPermissionsUseCase,
    GetRolePermissionsUseCase,
    SyncUserUseCase,
)
from src.api.middlewares import get_settings


async def get_db() -> AsyncSession:
    async for session in get_session():
        yield session


async def get_user_repo(db: AsyncSession = Depends(get_db)):
    return SQLAlchemyUserRepository(db)


async def get_role_repo(db: AsyncSession = Depends(get_db)):
    return SQLAlchemyRoleRepository(db)


async def get_permission_repo(db: AsyncSession = Depends(get_db)):
    return SQLAlchemyPermissionRepository(db)


async def get_event_publisher(settings: Settings = Depends(get_settings)):
    from src.api.main import app_event_publisher
    return app_event_publisher


async def get_create_user_use_case(
    user_repo=Depends(get_user_repo),
    event_publisher=Depends(get_event_publisher),
) -> CreateUserUseCase:
    return CreateUserUseCase(user_repo, event_publisher)


async def get_get_user_use_case(
    user_repo=Depends(get_user_repo),
) -> GetUserUseCase:
    return GetUserUseCase(user_repo)


async def get_list_users_use_case(
    user_repo=Depends(get_user_repo),
) -> ListUsersUseCase:
    return ListUsersUseCase(user_repo)


async def get_update_user_use_case(
    user_repo=Depends(get_user_repo),
    event_publisher=Depends(get_event_publisher),
) -> UpdateUserUseCase:
    return UpdateUserUseCase(user_repo, event_publisher)


async def get_delete_user_use_case(
    user_repo=Depends(get_user_repo),
    event_publisher=Depends(get_event_publisher),
) -> DeleteUserUseCase:
    return DeleteUserUseCase(user_repo, event_publisher)


async def get_assign_role_use_case(
    user_repo=Depends(get_user_repo),
    role_repo=Depends(get_role_repo),
    event_publisher=Depends(get_event_publisher),
) -> AssignRoleUseCase:
    return AssignRoleUseCase(user_repo, role_repo, event_publisher)


async def get_remove_role_use_case(
    user_repo=Depends(get_user_repo),
) -> RemoveRoleUseCase:
    return RemoveRoleUseCase(user_repo)


async def get_create_role_use_case(
    role_repo=Depends(get_role_repo),
) -> CreateRoleUseCase:
    return CreateRoleUseCase(role_repo)


async def get_list_roles_use_case(
    role_repo=Depends(get_role_repo),
    permission_repo=Depends(get_permission_repo),
) -> ListRolesUseCase:
    return ListRolesUseCase(role_repo, permission_repo)


async def get_get_role_use_case(
    role_repo=Depends(get_role_repo),
) -> GetRoleUseCase:
    return GetRoleUseCase(role_repo)


async def get_update_role_use_case(
    role_repo=Depends(get_role_repo),
) -> UpdateRoleUseCase:
    return UpdateRoleUseCase(role_repo)


async def get_delete_role_use_case(
    role_repo=Depends(get_role_repo),
) -> DeleteRoleUseCase:
    return DeleteRoleUseCase(role_repo)


async def get_list_permissions_use_case(
    permission_repo=Depends(get_permission_repo),
) -> ListPermissionsUseCase:
    return ListPermissionsUseCase(permission_repo)


async def get_role_permissions_use_case(
    role_repo=Depends(get_role_repo),
) -> GetRolePermissionsUseCase:
    return GetRolePermissionsUseCase(role_repo)


async def get_sync_user_use_case(
    user_repo=Depends(get_user_repo),
) -> SyncUserUseCase:
    return SyncUserUseCase(user_repo)
