from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings
from src.infrastructure.database import get_session
from src.infrastructure.database.repositories import (
    SQLAlchemyUserRepository,
    SQLAlchemyRefreshTokenRepository,
)
from src.infrastructure.message_queue import EventPublisher
from src.application.use_cases.auth_use_cases import (
    RegisterUserUseCase,
    LoginUseCase,
    RefreshTokenUseCase,
    LogoutUseCase,
    ValidateTokenUseCase,
)
from src.api.middlewares import get_settings


async def get_db() -> AsyncSession:
    async for session in get_session():
        yield session


async def get_user_repo(db: AsyncSession = Depends(get_db)):
    return SQLAlchemyUserRepository(db)


async def get_refresh_token_repo(db: AsyncSession = Depends(get_db)):
    return SQLAlchemyRefreshTokenRepository(db)


async def get_event_publisher(settings: Settings = Depends(get_settings)):
    from src.api.main import app_event_publisher
    return app_event_publisher


async def get_register_use_case(
    user_repo=Depends(get_user_repo),
    refresh_token_repo=Depends(get_refresh_token_repo),
    event_publisher=Depends(get_event_publisher),
    settings: Settings = Depends(get_settings),
) -> RegisterUserUseCase:
    return RegisterUserUseCase(user_repo, refresh_token_repo, event_publisher, settings)


async def get_login_use_case(
    user_repo=Depends(get_user_repo),
    refresh_token_repo=Depends(get_refresh_token_repo),
    event_publisher=Depends(get_event_publisher),
    settings: Settings = Depends(get_settings),
) -> LoginUseCase:
    return LoginUseCase(user_repo, refresh_token_repo, event_publisher, settings)


async def get_refresh_use_case(
    refresh_token_repo=Depends(get_refresh_token_repo),
    settings: Settings = Depends(get_settings),
) -> RefreshTokenUseCase:
    return RefreshTokenUseCase(refresh_token_repo, settings)


async def get_logout_use_case(
    refresh_token_repo=Depends(get_refresh_token_repo),
    event_publisher=Depends(get_event_publisher),
    settings: Settings = Depends(get_settings),
) -> LogoutUseCase:
    return LogoutUseCase(refresh_token_repo, event_publisher, settings)


async def get_validate_use_case(
    settings: Settings = Depends(get_settings),
) -> ValidateTokenUseCase:
    return ValidateTokenUseCase(settings)
