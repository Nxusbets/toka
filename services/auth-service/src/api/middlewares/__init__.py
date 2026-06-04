from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from structlog import get_logger

from src.config import Settings
from src.application.use_cases.auth_use_cases import decode_token
from src.infrastructure.cache import is_token_blacklisted

logger = get_logger(__name__)

security = HTTPBearer(auto_error=False)


async def get_settings() -> Settings:
    from src.api.main import app_settings
    return app_settings


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    settings: Settings = Depends(get_settings),
) -> dict:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authorization header"
        )

    token = credentials.credentials
    payload = decode_token(token, settings)

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
        )

    jti = payload.get("jti", payload.get("sub", ""))
    if await is_token_blacklisted(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked"
        )

    logger.info("token_validated", user_id=payload["sub"])
    return {
        "user_id": UUID(payload["sub"]),
        "email": payload.get("email", ""),
    }
