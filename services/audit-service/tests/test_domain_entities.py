from datetime import datetime

from domain.entities.audit_log import AuditLog


class TestAuditLogEntity:
    def test_audit_log_creation_with_defaults(self):
        log = AuditLog()
        assert log.id is None
        assert log.event_type == ""
        assert log.user_id is None
        assert log.user_email is None
        assert log.resource == ""
        assert log.action == ""
        assert log.ip_address is None
        assert log.user_agent is None
        assert log.metadata == {}
        assert isinstance(log.timestamp, datetime)

    def test_audit_log_creation_with_values(self):
        now = datetime.utcnow()
        log = AuditLog(
            id="507f1f77bcf86cd799439011",
            event_type="auth.login",
            user_id="user-123",
            user_email="test@example.com",
            resource="auth",
            action="login",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            metadata={"browser": "chrome"},
            timestamp=now,
        )
        assert log.id == "507f1f77bcf86cd799439011"
        assert log.event_type == "auth.login"
        assert log.user_id == "user-123"
        assert log.user_email == "test@example.com"
        assert log.resource == "auth"
        assert log.action == "login"
        assert log.ip_address == "192.168.1.1"
        assert log.user_agent == "Mozilla/5.0"
        assert log.metadata == {"browser": "chrome"}
        assert log.timestamp == now

    def test_audit_log_metadata_dict(self):
        log = AuditLog(metadata={"key": "value"})
        assert log.metadata["key"] == "value"

    def test_audit_log_no_optional_fields(self):
        log = AuditLog(event_type="test", resource="x", action="y")
        assert log.user_id is None
        assert log.user_email is None
        assert log.ip_address is None
        assert log.user_agent is None
