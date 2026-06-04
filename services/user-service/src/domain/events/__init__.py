from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class DomainEvent:
    event_type: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class UserUpdated(DomainEvent):
    user_id: UUID = field(default_factory=uuid4)
    email: str | None = None
    username: str | None = None
    is_active: bool | None = None


@dataclass
class RoleAssigned(DomainEvent):
    user_id: UUID = field(default_factory=uuid4)
    role_id: UUID = field(default_factory=uuid4)
    role_name: str = ""
    assigned_by: UUID | None = None
