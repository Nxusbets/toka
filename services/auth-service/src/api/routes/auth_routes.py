from fastapi import APIRouter, Depends
from structlog import get_logger

from src.application.dto.auth_dto import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    UserResponse,
)
from src.application.use_cases.auth_use_cases import (
    RegisterUserUseCase,
    LoginUseCase,
    RefreshTokenUseCase,
    LogoutUseCase,
    ValidateTokenUseCase,
    _user_to_response,
)
from src.api.dependencies import (
    get_register_use_case,
    get_login_use_case,
    get_refresh_use_case,
    get_logout_use_case,
    get_validate_use_case,
)
from src.api.middlewares import get_current_user
from src.infrastructure.database.repositories import SQLAlchemyUserRepository
from src.infrastructure.database import get_session
from src.infrastructure.cache import blacklist_token

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    request: RegisterRequest,
    use_case: RegisterUserUseCase = Depends(get_register_use_case),
):
    return await use_case.execute(request)


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    use_case: LoginUseCase = Depends(get_login_use_case),
):
    return await use_case.execute(request)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: RefreshRequest,
    use_case: RefreshTokenUseCase = Depends(get_refresh_use_case),
):
    return await use_case.execute(request)


@router.post("/logout", status_code=204)
async def logout(
    use_case: LogoutUseCase = Depends(get_logout_use_case),
    current_user: dict = Depends(get_current_user),
):
    await use_case.execute(current_user["user_id"], "")
    return None


@router.get("/validate")
async def validate_token(
    use_case: ValidateTokenUseCase = Depends(get_validate_use_case),
    current_user: dict = Depends(get_current_user),
):
    return {"valid": True, "user": current_user}


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: dict = Depends(get_current_user),
):
    async for session in get_session():
        repo = SQLAlchemyUserRepository(session)
        user = await repo.get_by_id(current_user["user_id"])
        if not user:
            from fastapi import HTTPException, status
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return _user_to_response(user)
