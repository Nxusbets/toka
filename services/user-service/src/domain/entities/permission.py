from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class Permission:
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    resource: str = ""
    action: str = ""
    description: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
