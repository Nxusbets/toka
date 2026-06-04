from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass(eq=False)
class User:
    id: UUID = field(default_factory=uuid4)
    email: str = ""
    username: str = ""
    password_hash: str = ""
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, User):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
