from uuid import UUID

from fastapi import APIRouter, Depends, Query, Path
from structlog import get_logger

from src.application.dto.user_dto import (
    CreateUserRequest,
    UpdateUserRequest,
    UserResponse,
    AssignRoleRequest,
    PaginatedResponse,
)
from src.application.use_cases.user_use_cases import (
    CreateUserUseCase,
    GetUserUseCase,
    ListUsersUseCase,
    UpdateUserUseCase,
    DeleteUserUseCase,
    AssignRoleUseCase,
    RemoveRoleUseCase,
)
from src.api.dependencies import (
    get_create_user_use_case,
    get_get_user_use_case,
    get_list_users_use_case,
    get_update_user_use_case,
    get_delete_user_use_case,
    get_assign_role_use_case,
    get_remove_role_use_case,
)
from src.api.middlewares import get_current_user

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("", response_model=PaginatedResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role_id: UUID | None = Query(None),
    is_active: bool | None = Query(None),
    use_case: ListUsersUseCase = Depends(get_list_users_use_case),
    _: dict = Depends(get_current_user),
):
    return await use_case.execute(page=page, page_size=page_size, role_id=role_id, is_active=is_active)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID = Path(...),
    use_case: GetUserUseCase = Depends(get_get_user_use_case),
    _: dict = Depends(get_current_user),
):
    return await use_case.execute(user_id)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    request: UpdateUserRequest,
    user_id: UUID = Path(...),
    use_case: UpdateUserUseCase = Depends(get_update_user_use_case),
    current_user: dict = Depends(get_current_user),
):
    return await use_case.execute(user_id, request)


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: UUID = Path(...),
    use_case: DeleteUserUseCase = Depends(get_delete_user_use_case),
    current_user: dict = Depends(get_current_user),
):
    await use_case.execute(user_id)
    return None


@router.post("/{user_id}/roles", response_model=UserResponse)
async def assign_role(
    request: AssignRoleRequest,
    user_id: UUID = Path(...),
    use_case: AssignRoleUseCase = Depends(get_assign_role_use_case),
    current_user: dict = Depends(get_current_user),
):
    return await use_case.execute(user_id, request, assigned_by=current_user["user_id"])


@router.delete("/{user_id}/roles/{role_id}", response_model=UserResponse)
async def remove_role(
    user_id: UUID = Path(...),
    role_id: UUID = Path(...),
    use_case: RemoveRoleUseCase = Depends(get_remove_role_use_case),
    current_user: dict = Depends(get_current_user),
):
    return await use_case.execute(user_id, role_id)
