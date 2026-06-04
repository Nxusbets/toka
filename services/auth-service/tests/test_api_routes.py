import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime

from fastapi.testclient import TestClient
from src.api.main import app
from src.config import Settings
from src.api.dependencies import (
    get_register_use_case,
    get_login_use_case,
    get_refresh_use_case,
    get_logout_use_case,
    get_validate_use_case,
)
from src.api.middlewares import get_settings, get_current_user


pytestmark = pytest.mark.asyncio


@pytest.fixture
def test_settings():
    return Settings(
        jwt_secret_key="test-secret-key",
        jwt_algorithm="HS256",
        jwt_access_token_expire_minutes=30,
        jwt_refresh_token_expire_days=7,
        database_url="sqlite+aiosqlite://",
        redis_url="redis://localhost:6379/0",
        rabbitmq_url="amqp://localhost:5672/",
    )


@pytest.fixture
def mock_register_use_case():
    mock = AsyncMock()
    mock.execute.return_value = {
        "access_token": "access-token",
        "refresh_token": "refresh-token",
        "token_type": "bearer",
    }
    return mock


@pytest.fixture
def mock_login_use_case():
    mock = AsyncMock()
    mock.execute.return_value = {
        "access_token": "access-token",
        "refresh_token": "refresh-token",
        "token_type": "bearer",
    }
    return mock


@pytest.fixture
def mock_refresh_use_case():
    mock = AsyncMock()
    mock.execute.return_value = {
        "access_token": "new-access-token",
        "refresh_token": "new-refresh-token",
        "token_type": "bearer",
    }
    return mock


@pytest.fixture
def mock_logout_use_case():
    return AsyncMock()


@pytest.fixture
def mock_validate_use_case():
    mock = AsyncMock()
    mock.execute.return_value = {
        "user_id": str(uuid4()),
        "email": "test@example.com",
        "token_type": "access",
    }
    return mock


@pytest.fixture
def client(
    test_settings,
    mock_register_use_case,
    mock_login_use_case,
    mock_refresh_use_case,
    mock_logout_use_case,
    mock_validate_use_case,
):
    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_register_use_case] = lambda: mock_register_use_case
    app.dependency_overrides[get_login_use_case] = lambda: mock_login_use_case
    app.dependency_overrides[get_refresh_use_case] = lambda: mock_refresh_use_case
    app.dependency_overrides[get_logout_use_case] = lambda: mock_logout_use_case
    app.dependency_overrides[get_validate_use_case] = lambda: mock_validate_use_case
    app.dependency_overrides[get_current_user] = lambda: {
        "user_id": uuid4(),
        "email": "test@example.com",
    }
    return TestClient(app)


class TestAuthRoutes:
    def test_register_success(self, client, mock_register_use_case):
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "username": "testuser", "password": "password123"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["access_token"] == "access-token"
        assert data["refresh_token"] == "refresh-token"

    def test_register_validation_error(self, client):
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "invalid", "username": "ab", "password": "short"},
        )
        assert response.status_code == 422

    def test_register_missing_fields(self, client):
        response = client.post("/api/v1/auth/register", json={})
        assert response.status_code == 422

    def test_login_success(self, client, mock_login_use_case):
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "access-token"

    def test_login_validation_error(self, client):
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "invalid", "password": ""},
        )
        assert response.status_code == 422

    def test_login_missing_fields(self, client):
        response = client.post("/api/v1/auth/login", json={})
        assert response.status_code == 422

    def test_refresh_success(self, client, mock_refresh_use_case):
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "some-valid-token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "new-access-token"

    def test_refresh_missing_token(self, client):
        response = client.post("/api/v1/auth/refresh", json={})
        assert response.status_code == 422

    def test_logout_success(self, client, mock_logout_use_case):
        response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 204

    def test_logout_unauthorized(self, client):
        app.dependency_overrides[get_current_user] = lambda: (_ for _ in ()).throw(
            __import__("fastapi").HTTPException(status_code=401, detail="Missing authorization header")
        )
        response = client.post("/api/v1/auth/logout")
        assert response.status_code == 401
        app.dependency_overrides[get_current_user] = lambda: {
            "user_id": uuid4(),
            "email": "test@example.com",
        }

    def test_validate_token_success(self, client, mock_validate_use_case):
        response = client.get(
            "/api/v1/auth/validate",
            headers={"Authorization": "Bearer valid-token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True

    def test_health_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "auth-service"


class TestGetMeEndpoint:
    def test_get_me_no_auth(self, client):
        app.dependency_overrides[get_current_user] = lambda: (_ for _ in ()).throw(
            __import__("fastapi").HTTPException(status_code=401, detail="Missing authorization header")
        )
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401
