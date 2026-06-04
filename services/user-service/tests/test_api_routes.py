import pytest
from unittest.mock import AsyncMock
from uuid import uuid4, UUID
from datetime import datetime

from fastapi.testclient import TestClient
from src.api.main import app
from src.config import Settings
from src.api.dependencies import (
    get_create_user_use_case, get_get_user_use_case, get_list_users_use_case,
    get_update_user_use_case, get_delete_user_use_case, get_assign_role_use_case,
    get_remove_role_use_case, get_create_role_use_case, get_list_roles_use_case,
    get_get_role_use_case, get_update_role_use_case, get_delete_role_use_case,
    get_list_permissions_use_case, get_role_permissions_use_case,
)
from src.api.middlewares import get_settings, get_current_user


pytestmark = pytest.mark.asyncio


@pytest.fixture
def test_settings():
    return Settings(
        jwt_secret_key="test-secret-key",
        jwt_algorithm="HS256",
        database_url="sqlite+aiosqlite://",
        rabbitmq_url="amqp://localhost:5672/",
    )


@pytest.fixture
def current_user():
    return {"user_id": uuid4(), "email": "admin@example.com"}


def make_mock_use_case(return_value=None):
    mock = AsyncMock()
    mock.execute.return_value = return_value
    return mock


@pytest.fixture
def client(test_settings, current_user):
    now = datetime.utcnow()
    user_id = uuid4()
    role_id = uuid4()
    perm_id = uuid4()

    sample_user_response = {
        "id": str(user_id), "email": "test@example.com", "username": "testuser",
        "is_active": True, "created_at": now.isoformat(), "updated_at": now.isoformat(), "roles": [],
    }
    sample_role_response = {
        "id": str(role_id), "name": "admin", "description": "Admin",
        "is_system": False, "created_at": now.isoformat(), "updated_at": now.isoformat(), "permissions": [],
    }
    sample_perm_response = {
        "id": str(perm_id), "name": "user:read", "resource": "user",
        "action": "read", "description": "Read users", "created_at": now.isoformat(),
    }
    paginated_response = {
        "items": [sample_user_response], "total": 1, "page": 1, "page_size": 20, "total_pages": 1,
    }
    paginated_roles = {
        "items": [sample_role_response], "total": 1, "page": 1, "page_size": 20, "total_pages": 1,
    }
    paginated_perms = {
        "items": [sample_perm_response], "total": 1, "page": 1, "page_size": 100, "total_pages": 1,
    }

    overrides = {
        get_settings: lambda: test_settings,
        get_current_user: lambda: current_user,
        get_create_user_use_case: lambda: make_mock_use_case(sample_user_response),
        get_get_user_use_case: lambda: make_mock_use_case(sample_user_response),
        get_list_users_use_case: lambda: make_mock_use_case(paginated_response),
        get_update_user_use_case: lambda: make_mock_use_case(sample_user_response),
        get_delete_user_use_case: lambda: make_mock_use_case(None),
        get_assign_role_use_case: lambda: make_mock_use_case(sample_user_response),
        get_remove_role_use_case: lambda: make_mock_use_case(sample_user_response),
        get_create_role_use_case: lambda: make_mock_use_case(sample_role_response),
        get_list_roles_use_case: lambda: make_mock_use_case(paginated_roles),
        get_get_role_use_case: lambda: make_mock_use_case(sample_role_response),
        get_update_role_use_case: lambda: make_mock_use_case(sample_role_response),
        get_delete_role_use_case: lambda: make_mock_use_case(None),
        get_list_permissions_use_case: lambda: make_mock_use_case(paginated_perms),
        get_role_permissions_use_case: lambda: make_mock_use_case([sample_perm_response]),
    }
    for dep, mock in overrides.items():
        app.dependency_overrides[dep] = mock

    yield TestClient(app)
    app.dependency_overrides.clear()


class TestUserRoutes:
    def test_list_users(self, client):
        response = client.get("/api/v1/users", headers={"Authorization": "Bearer test-token"})
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["total"] == 1

    def test_list_users_with_filters(self, client):
        response = client.get(
            "/api/v1/users?page=1&page_size=10&is_active=true",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 200

    def test_get_user(self, client):
        response = client.get(f"/api/v1/users/{uuid4()}", headers={"Authorization": "Bearer test-token"})
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"

    def test_get_user_invalid_id(self, client):
        response = client.get("/api/v1/users/invalid", headers={"Authorization": "Bearer test-token"})
        assert response.status_code == 422

    def test_update_user(self, client):
        response = client.put(
            f"/api/v1/users/{uuid4()}",
            json={"email": "new@example.com", "username": "newname"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 200

    def test_update_user_invalid_data(self, client):
        response = client.put(
            f"/api/v1/users/{uuid4()}",
            json={"email": "invalid"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 422

    def test_delete_user(self, client):
        response = client.delete(
            f"/api/v1/users/{uuid4()}",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 204

    def test_assign_role(self, client):
        response = client.post(
            f"/api/v1/users/{uuid4()}/roles",
            json={"role_id": str(uuid4())},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 200

    def test_assign_role_invalid(self, client):
        response = client.post(
            f"/api/v1/users/{uuid4()}/roles",
            json={},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 422

    def test_remove_role(self, client):
        response = client.delete(
            f"/api/v1/users/{uuid4()}/roles/{uuid4()}",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 200

    def test_unauthorized_access(self, client):
        app.dependency_overrides[get_current_user] = lambda: (_ for _ in ()).throw(
            __import__("fastapi").HTTPException(status_code=401, detail="Missing authorization header")
        )
        response = client.get("/api/v1/users")
        assert response.status_code == 401


class TestRoleRoutes:
    def test_list_roles(self, client):
        response = client.get("/api/v1/roles", headers={"Authorization": "Bearer test-token"})
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    def test_create_role(self, client):
        response = client.post(
            "/api/v1/roles",
            json={"name": "moderator", "description": "Moderator role"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "admin"

    def test_create_role_invalid(self, client):
        response = client.post(
            "/api/v1/roles",
            json={"name": ""},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 422

    def test_get_role(self, client):
        response = client.get(f"/api/v1/roles/{uuid4()}", headers={"Authorization": "Bearer test-token"})
        assert response.status_code == 200

    def test_update_role(self, client):
        response = client.put(
            f"/api/v1/roles/{uuid4()}",
            json={"name": "updated-role"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 200

    def test_delete_role(self, client):
        response = client.delete(
            f"/api/v1/roles/{uuid4()}",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 204

    def test_list_permissions(self, client):
        response = client.get("/api/v1/permissions", headers={"Authorization": "Bearer test-token"})
        assert response.status_code == 200

    def test_get_role_permissions(self, client):
        response = client.get(
            f"/api/v1/roles/{uuid4()}/permissions",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 200

    def test_health_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "user-service"
