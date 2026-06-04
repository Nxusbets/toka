from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class DomainEvent:
    event_type: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class UserRegistered(DomainEvent):
    user_id: UUID = field(default_factory=uuid4)
    email: str = ""
    username: str = ""


@dataclass
class UserLoggedIn(DomainEvent):
    user_id: UUID = field(default_factory=uuid4)
    email: str = ""


@dataclass
class UserLoggedOut(DomainEvent):
    user_id: UUID = field(default_factory=uuid4)
