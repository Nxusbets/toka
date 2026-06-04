from __future__ import annotations
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Path
from structlog import get_logger

from src.application.dto.user_dto import (
    CreateRoleRequest,
    UpdateRoleRequest,
    RoleResponse,
    PermissionResponse,
    PaginatedResponse,
)
from src.application.use_cases.user_use_cases import (
    CreateRoleUseCase,
    ListRolesUseCase,
    GetRoleUseCase,
    UpdateRoleUseCase,
    DeleteRoleUseCase,
    ListPermissionsUseCase,
    GetRolePermissionsUseCase,
)
from src.api.dependencies import (
    get_create_role_use_case,
    get_list_roles_use_case,
    get_get_role_use_case,
    get_update_role_use_case,
    get_delete_role_use_case,
    get_list_permissions_use_case,
    get_role_permissions_use_case,
)
from src.api.middlewares import get_current_user

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["roles"])


@router.get("/roles", response_model=PaginatedResponse)
async def list_roles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    use_case: ListRolesUseCase = Depends(get_list_roles_use_case),
):
    return await use_case.execute(page=page, page_size=page_size)


@router.post("/roles", response_model=RoleResponse, status_code=201)
async def create_role(
    request: CreateRoleRequest,
    use_case: CreateRoleUseCase = Depends(get_create_role_use_case),
    current_user: dict = Depends(get_current_user),
):
    return await use_case.execute(request)


@router.get("/roles/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: UUID = Path(...),
    use_case: GetRoleUseCase = Depends(get_get_role_use_case),
):
    return await use_case.execute(role_id)


@router.put("/roles/{role_id}", response_model=RoleResponse)
async def update_role(
    request: UpdateRoleRequest,
    role_id: UUID = Path(...),
    use_case: UpdateRoleUseCase = Depends(get_update_role_use_case),
    current_user: dict = Depends(get_current_user),
):
    return await use_case.execute(role_id, request)


@router.delete("/roles/{role_id}", status_code=204)
async def delete_role(
    role_id: UUID = Path(...),
    use_case: DeleteRoleUseCase = Depends(get_delete_role_use_case),
    current_user: dict = Depends(get_current_user),
):
    await use_case.execute(role_id)
    return None


@router.get("/permissions", response_model=PaginatedResponse)
async def list_permissions(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=200),
    use_case: ListPermissionsUseCase = Depends(get_list_permissions_use_case),
):
    return await use_case.execute(page=page, page_size=page_size)


@router.get("/roles/{role_id}/permissions", response_model=list[PermissionResponse])
async def get_role_permissions(
    role_id: UUID = Path(...),
    use_case: GetRolePermissionsUseCase = Depends(get_role_permissions_use_case),
):
    return await use_case.execute(role_id)
