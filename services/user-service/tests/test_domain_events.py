from datetime import datetime
from uuid import uuid4

from src.domain.events import DomainEvent, UserUpdated, RoleAssigned


class TestDomainEvents:
    def test_domain_event_base(self):
        event = DomainEvent(event_type="test.event")
        assert event.event_type == "test.event"
        assert isinstance(event.timestamp, datetime)

    def test_user_updated_event(self):
        user_id = uuid4()
        event = UserUpdated(
            event_type="user.updated",
            user_id=user_id,
            email="new@example.com",
            username="newname",
            is_active=True,
        )
        assert event.event_type == "user.updated"
        assert event.user_id == user_id
        assert event.email == "new@example.com"
        assert event.username == "newname"
        assert event.is_active is True

    def test_user_updated_event_optional_fields(self):
        user_id = uuid4()
        event = UserUpdated(
            event_type="user.updated",
            user_id=user_id,
        )
        assert event.email is None
        assert event.username is None
        assert event.is_active is None

    def test_role_assigned_event(self):
        user_id = uuid4()
        role_id = uuid4()
        assigned_by = uuid4()
        event = RoleAssigned(
            event_type="role.assigned",
            user_id=user_id,
            role_id=role_id,
            role_name="admin",
            assigned_by=assigned_by,
        )
        assert event.event_type == "role.assigned"
        assert event.user_id == user_id
        assert event.role_id == role_id
        assert event.role_name == "admin"
        assert event.assigned_by == assigned_by

    def test_role_assigned_event_without_assigner(self):
        user_id = uuid4()
        role_id = uuid4()
        event = RoleAssigned(
            event_type="role.assigned",
            user_id=user_id,
            role_id=role_id,
            role_name="viewer",
        )
        assert event.assigned_by is None

    def test_event_inheritance(self):
        event = UserUpdated(event_type="user.updated", user_id=uuid4())
        assert isinstance(event, DomainEvent)
