from uuid import UUID
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from structlog import get_logger

from src.config import Settings
import jwt

logger = get_logger(__name__)

security = HTTPBearer(auto_error=False)


async def get_settings() -> Settings:
    from src.api.main import app_settings
    return app_settings


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    settings: Settings = Depends(get_settings),
) -> dict:
    internal_key = request.headers.get("X-Internal-Api-Key")
    if internal_key and internal_key == settings.internal_api_key:
        return {"user_id": None, "email": "internal@service", "is_internal": True}

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authorization header"
        )

    token = credentials.credentials

    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
        )

    logger.info("token_validated", user_id=payload["sub"])
    return {
        "user_id": UUID(payload["sub"]),
        "email": payload.get("email", ""),
        "is_internal": False,
    }
