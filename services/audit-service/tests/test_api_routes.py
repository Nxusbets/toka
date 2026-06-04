import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from api.main import app
from domain.repositories import AuditLogRepository
from domain.entities.audit_log import AuditLog
from application.use_cases.audit_use_cases import LogEventUseCase


pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_repo():
    repo = MagicMock(spec=AuditLogRepository)
    repo.create = AsyncMock()
    repo.find_by_id = AsyncMock()
    repo.find_all = AsyncMock()
    repo.get_stats = AsyncMock()
    return repo


@pytest.fixture
def client(mock_repo):
    app.state.audit_repo = mock_repo
    app.state.log_event_use_case = LogEventUseCase(mock_repo)
    return TestClient(app)


class TestAuditRoutes:
    def test_list_logs_empty(self, client, mock_repo):
        mock_repo.find_all.return_value = ([], 0)

        response = client.get("/api/v1/audit/logs")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["skip"] == 0
        assert data["limit"] == 100

    def test_list_logs_with_data(self, client, mock_repo):
        now = datetime.utcnow()
        log = AuditLog(
            id="507f1f77bcf86cd799439011",
            event_type="auth.login",
            user_id="user-123",
            user_email="test@example.com",
            resource="auth",
            action="login",
            timestamp=now,
        )
        mock_repo.find_all.return_value = ([log], 1)

        response = client.get("/api/v1/audit/logs")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["total"] == 1
        assert data["items"][0]["event_type"] == "auth.login"

    def test_list_logs_with_filters(self, client, mock_repo):
        mock_repo.find_all.return_value = ([], 0)

        response = client.get(
            "/api/v1/audit/logs?skip=10&limit=50&event_type=auth.login&user_id=user-123"
        )
        assert response.status_code == 200

        mock_repo.find_all.assert_called_once_with(
            skip=10, limit=50, event_type="auth.login",
            user_id="user-123", from_date=None, to_date=None,
        )

    def test_get_log_found(self, client, mock_repo):
        now = datetime.utcnow()
        log = AuditLog(
            id="507f1f77bcf86cd799439011",
            event_type="auth.login",
            resource="auth",
            action="login",
            timestamp=now,
        )
        mock_repo.find_by_id.return_value = log

        response = client.get("/api/v1/audit/logs/507f1f77bcf86cd799439011")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "507f1f77bcf86cd799439011"
        assert data["event_type"] == "auth.login"

    def test_get_log_not_found(self, client, mock_repo):
        mock_repo.find_by_id.return_value = None

        response = client.get("/api/v1/audit/logs/nonexistent-id")
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_get_stats(self, client, mock_repo):
        mock_repo.get_stats.return_value = {
            "total": 100,
            "by_event_type": {"auth.login": 60, "user.updated": 40},
            "by_day": [{"date": "2024-01-01", "count": 10}],
        }

        response = client.get("/api/v1/audit/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 100
        assert data["by_event_type"]["auth.login"] == 60

    def test_health_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "audit-service"

    def test_list_logs_limit_invalid(self, client):
        response = client.get("/api/v1/audit/logs?limit=2000")
        assert response.status_code == 422
