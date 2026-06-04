import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

from src.config import Settings
from src.domain.entities.user import User
from src.domain.entities.refresh_token import RefreshToken
from src.domain.events import UserRegistered, UserLoggedIn, UserLoggedOut
from src.domain.repositories import UserRepository, RefreshTokenRepository
from src.infrastructure.message_queue import EventPublisher
from src.application.dto.auth_dto import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    UserResponse,
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_access_token(user_id: UUID, email: str, settings: Settings) -> str:
    expires = datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt_access_token_expire_minutes
    )
    payload = {
        "sub": str(user_id),
        "email": email,
        "type": "access",
        "exp": expires,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: UUID, settings: Settings) -> str:
    expires = datetime.now(timezone.utc) + timedelta(
        days=settings.jwt_refresh_token_expire_days
    )
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": expires,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str, settings: Settings) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def _user_to_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


class RegisterUserUseCase:
    def __init__(
        self,
        user_repo: UserRepository,
        refresh_token_repo: RefreshTokenRepository,
        event_publisher: EventPublisher,
        settings: Settings,
    ):
        self.user_repo = user_repo
        self.refresh_token_repo = refresh_token_repo
        self.event_publisher = event_publisher
        self.settings = settings

    async def execute(self, request: RegisterRequest) -> TokenResponse:
        existing = await self.user_repo.get_by_email(request.email)
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

        existing = await self.user_repo.get_by_username(request.username)
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")

        user = User(
            email=request.email,
            username=request.username,
            password_hash=hash_password(request.password),
        )
        created = await self.user_repo.create(user)

        access_token = create_access_token(created.id, created.email, self.settings)
        refresh_token_str = create_refresh_token(created.id, self.settings)
        refresh_token_hash = hash_token(refresh_token_str)

        rt = RefreshToken(
            user_id=created.id,
            token_hash=refresh_token_hash,
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=self.settings.jwt_refresh_token_expire_days),
        )
        await self.refresh_token_repo.create(rt)

        await self.event_publisher.publish(
            UserRegistered(
                event_type="user.registered",
                user_id=created.id,
                email=created.email,
                username=created.username,
            )
        )

        return TokenResponse(access_token=access_token, refresh_token=refresh_token_str)


class LoginUseCase:
    def __init__(
        self,
        user_repo: UserRepository,
        refresh_token_repo: RefreshTokenRepository,
        event_publisher: EventPublisher,
        settings: Settings,
    ):
        self.user_repo = user_repo
        self.refresh_token_repo = refresh_token_repo
        self.event_publisher = event_publisher
        self.settings = settings

    async def execute(self, request: LoginRequest) -> TokenResponse:
        user = await self.user_repo.get_by_email(request.email)
        if not user or not verify_password(request.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive"
            )

        access_token = create_access_token(user.id, user.email, self.settings)
        refresh_token_str = create_refresh_token(user.id, self.settings)
        refresh_token_hash = hash_token(refresh_token_str)

        rt = RefreshToken(
            user_id=user.id,
            token_hash=refresh_token_hash,
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=self.settings.jwt_refresh_token_expire_days),
        )
        await self.refresh_token_repo.create(rt)

        await self.event_publisher.publish(
            UserLoggedIn(
                event_type="user.logged_in",
                user_id=user.id,
                email=user.email,
            )
        )

        return TokenResponse(access_token=access_token, refresh_token=refresh_token_str)


class RefreshTokenUseCase:
    def __init__(
        self,
        refresh_token_repo: RefreshTokenRepository,
        settings: Settings,
    ):
        self.refresh_token_repo = refresh_token_repo
        self.settings = settings

    async def execute(self, request: RefreshRequest) -> TokenResponse:
        payload = decode_token(request.refresh_token, self.settings)
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
            )

        token_hash = hash_token(request.refresh_token)
        stored = await self.refresh_token_repo.get_by_token_hash(token_hash)
        if not stored or stored.revoked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked or not found"
            )

        if stored.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired"
            )

        await self.refresh_token_repo.revoke(stored.id)

        user_id = UUID(payload["sub"])
        access_token = create_access_token(user_id, payload.get("email", ""), self.settings)
        new_refresh_token_str = create_refresh_token(user_id, self.settings)
        new_token_hash = hash_token(new_refresh_token_str)

        rt = RefreshToken(
            user_id=user_id,
            token_hash=new_token_hash,
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=self.settings.jwt_refresh_token_expire_days),
        )
        await self.refresh_token_repo.create(rt)

        return TokenResponse(access_token=access_token, refresh_token=new_refresh_token_str)


class LogoutUseCase:
    def __init__(
        self,
        refresh_token_repo: RefreshTokenRepository,
        event_publisher: EventPublisher,
        settings: Settings,
    ):
        self.refresh_token_repo = refresh_token_repo
        self.event_publisher = event_publisher
        self.settings = settings

    async def execute(self, user_id: UUID, access_token: str) -> None:
        await self.refresh_token_repo.revoke_all_for_user(user_id)

        await self.event_publisher.publish(
            UserLoggedOut(event_type="user.logged_out", user_id=user_id)
        )


class ValidateTokenUseCase:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def execute(self, token: str) -> dict:
        payload = decode_token(token, self.settings)
        return {
            "user_id": payload["sub"],
            "email": payload.get("email", ""),
            "token_type": payload.get("type", "access"),
        }
