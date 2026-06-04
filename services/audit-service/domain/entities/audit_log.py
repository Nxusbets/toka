from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class AuditLog:
    id: Optional[str] = None
    event_type: str = ""
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    resource: str = ""
    action: str = ""
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
