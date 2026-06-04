from datetime import datetime
from uuid import uuid4

from src.domain.events import DomainEvent, UserRegistered, UserLoggedIn, UserLoggedOut


class TestDomainEvents:
    def test_domain_event_base(self):
        event = DomainEvent(event_type="test.event")
        assert event.event_type == "test.event"
        assert isinstance(event.timestamp, datetime)

    def test_user_registered_event(self):
        user_id = uuid4()
        event = UserRegistered(
            event_type="user.registered",
            user_id=user_id,
            email="test@example.com",
            username="testuser",
        )
        assert event.event_type == "user.registered"
        assert event.user_id == user_id
        assert event.email == "test@example.com"
        assert event.username == "testuser"

    def test_user_logged_in_event(self):
        user_id = uuid4()
        event = UserLoggedIn(
            event_type="user.logged_in",
            user_id=user_id,
            email="test@example.com",
        )
        assert event.event_type == "user.logged_in"
        assert event.user_id == user_id
        assert event.email == "test@example.com"

    def test_user_logged_out_event(self):
        user_id = uuid4()
        event = UserLoggedOut(
            event_type="user.logged_out",
            user_id=user_id,
        )
        assert event.event_type == "user.logged_out"
        assert event.user_id == user_id

    def test_event_inheritance(self):
        user_id = uuid4()
        event = UserRegistered(
            event_type="user.registered",
            user_id=user_id,
            email="test@example.com",
            username="testuser",
        )
        assert isinstance(event, DomainEvent)

    def test_event_default_timestamp(self):
        event = DomainEvent(event_type="test.event")
        assert isinstance(event.timestamp, datetime)
