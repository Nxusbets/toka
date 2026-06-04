import pytest
from datetime import datetime
from pydantic import ValidationError

from application.dto.audit_dto import (
    AuditLogResponse,
    AuditLogListResponse,
    AuditLogFilter,
)


class TestAuditLogResponse:
    def test_valid_response(self):
        now = datetime.utcnow()
        dto = AuditLogResponse(
            id="507f1f77bcf86cd799439011",
            event_type="auth.login",
            user_id="user-123",
            user_email="test@example.com",
            resource="auth",
            action="login",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            metadata={"key": "value"},
            timestamp=now,
        )
        assert dto.event_type == "auth.login"
        assert dto.resource == "auth"
        assert dto.action == "login"
        assert dto.metadata == {"key": "value"}

    def test_optional_fields(self):
        now = datetime.utcnow()
        dto = AuditLogResponse(
            id="abc123",
            event_type="test",
            resource="x",
            action="y",
            timestamp=now,
        )
        assert dto.user_id is None
        assert dto.user_email is None
        assert dto.ip_address is None
        assert dto.user_agent is None
        assert dto.metadata == {}

    def test_missing_required_fields(self):
        now = datetime.utcnow()
        with pytest.raises(ValidationError):
            AuditLogResponse(
                id="abc123",
                event_type="test",
                resource="x",
                timestamp=now,
            )


class TestAuditLogListResponse:
    def test_valid_list_response(self):
        now = datetime.utcnow()
        item = AuditLogResponse(
            id="abc", event_type="test", resource="r", action="a", timestamp=now,
        )
        dto = AuditLogListResponse(items=[item], total=1, skip=0, limit=100)
        assert len(dto.items) == 1
        assert dto.total == 1
        assert dto.skip == 0
        assert dto.limit == 100

    def test_empty_list(self):
        dto = AuditLogListResponse(items=[], total=0, skip=0, limit=100)
        assert dto.items == []
        assert dto.total == 0

    def test_missing_fields(self):
        with pytest.raises(ValidationError):
            AuditLogListResponse()


class TestAuditLogFilter:
    def test_valid_filter(self):
        dto = AuditLogFilter(event_type="auth.login", user_id="user-123")
        assert dto.event_type == "auth.login"
        assert dto.user_id == "user-123"
        assert dto.from_date is None
        assert dto.to_date is None
        assert dto.skip == 0
        assert dto.limit == 100

    def test_filter_with_dates(self):
        dto = AuditLogFilter(from_date="2024-01-01", to_date="2024-12-31")
        assert dto.from_date == "2024-01-01"
        assert dto.to_date == "2024-12-31"

    def test_filter_pagination(self):
        dto = AuditLogFilter(skip=10, limit=50)
        assert dto.skip == 10
        assert dto.limit == 50

    def test_filter_all_defaults(self):
        dto = AuditLogFilter()
        assert dto.event_type is None
        assert dto.user_id is None
        assert dto.skip == 0
        assert dto.limit == 100
