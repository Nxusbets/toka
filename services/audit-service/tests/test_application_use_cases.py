import pytest
from datetime import datetime
from unittest.mock import AsyncMock

from domain.entities.audit_log import AuditLog
from application.use_cases.audit_use_cases import (
    LogEventUseCase,
    ListAuditLogsUseCase,
    GetAuditLogUseCase,
)


pytestmark = pytest.mark.asyncio


class TestLogEventUseCase:
    async def test_log_event_success(self, mock_audit_repo):
        mock_audit_repo.create.return_value = AuditLog(
            id="507f1f77bcf86cd799439011",
            event_type="auth.login",
            user_id="user-123",
            user_email="test@example.com",
            resource="auth",
            action="login",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            metadata={"key": "value"},
            timestamp=datetime.utcnow(),
        )

        use_case = LogEventUseCase(mock_audit_repo)
        event_data = {
            "event_type": "auth.login",
            "user_id": "user-123",
            "user_email": "test@example.com",
            "resource": "auth",
            "action": "login",
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0",
            "metadata": {"key": "value"},
            "timestamp": datetime.utcnow().isoformat(),
        }
        result = await use_case.execute(event_data)

        assert result.id == "507f1f77bcf86cd799439011"
        assert result.event_type == "auth.login"
        assert result.user_id == "user-123"
        mock_audit_repo.create.assert_called_once()

    async def test_log_event_minimal_data(self, mock_audit_repo):
        mock_audit_repo.create.return_value = AuditLog(
            id="abc123",
            event_type="test.event",
            resource="test",
            action="execute",
        )

        use_case = LogEventUseCase(mock_audit_repo)
        event_data = {
            "event_type": "test.event",
            "resource": "test",
            "action": "execute",
        }
        result = await use_case.execute(event_data)

        assert result.event_type == "test.event"
        assert result.resource == "test"
        assert result.action == "execute"

    async def test_log_event_unknown_type(self, mock_audit_repo):
        mock_audit_repo.create.return_value = AuditLog(
            id="abc123", event_type="unknown", resource="", action="",
        )

        use_case = LogEventUseCase(mock_audit_repo)
        result = await use_case.execute({})

        assert result.event_type == "unknown"

    async def test_log_event_with_timestamp(self, mock_audit_repo):
        now = datetime.utcnow()
        mock_audit_repo.create.return_value = AuditLog(
            id="abc123", event_type="test", resource="r", action="a", timestamp=now,
        )

        use_case = LogEventUseCase(mock_audit_repo)
        event_data = {
            "event_type": "test",
            "resource": "r",
            "action": "a",
            "timestamp": now.isoformat(),
        }
        result = await use_case.execute(event_data)

        assert result.timestamp == now


class TestListAuditLogsUseCase:
    async def test_list_empty(self, mock_audit_repo):
        mock_audit_repo.find_all.return_value = ([], 0)

        use_case = ListAuditLogsUseCase(mock_audit_repo)
        logs, total = await use_case.execute()

        assert logs == []
        assert total == 0

    async def test_list_with_results(self, mock_audit_repo, sample_audit_log):
        mock_audit_repo.find_all.return_value = ([sample_audit_log], 1)

        use_case = ListAuditLogsUseCase(mock_audit_repo)
        logs, total = await use_case.execute(skip=0, limit=10)

        assert len(logs) == 1
        assert total == 1
        assert logs[0].event_type == "auth.login"

    async def test_list_with_filters(self, mock_audit_repo):
        use_case = ListAuditLogsUseCase(mock_audit_repo)
        await use_case.execute(
            skip=10, limit=50, event_type="auth.login",
            user_id="user-123", from_date="2024-01-01", to_date="2024-12-31",
        )

        mock_audit_repo.find_all.assert_called_once_with(
            skip=10, limit=50, event_type="auth.login",
            user_id="user-123", from_date="2024-01-01", to_date="2024-12-31",
        )

    async def test_list_default_pagination(self, mock_audit_repo):
        use_case = ListAuditLogsUseCase(mock_audit_repo)
        await use_case.execute()

        mock_audit_repo.find_all.assert_called_once_with(
            skip=0, limit=100, event_type=None,
            user_id=None, from_date=None, to_date=None,
        )


class TestGetAuditLogUseCase:
    async def test_get_success(self, mock_audit_repo, sample_audit_log):
        mock_audit_repo.find_by_id.return_value = sample_audit_log

        use_case = GetAuditLogUseCase(mock_audit_repo)
        result = await use_case.execute("507f1f77bcf86cd799439011")

        assert result is not None
        assert result.id == "507f1f77bcf86cd799439011"
        assert result.event_type == "auth.login"

    async def test_get_not_found(self, mock_audit_repo):
        mock_audit_repo.find_by_id.return_value = None

        use_case = GetAuditLogUseCase(mock_audit_repo)
        result = await use_case.execute("nonexistent-id")

        assert result is None
