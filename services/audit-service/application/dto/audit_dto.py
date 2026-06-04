from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: str
    event_type: str
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    resource: str
    action: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: dict[str, Any] = {}
    timestamp: datetime


class AuditLogListResponse(BaseModel):
    items: list[AuditLogResponse]
    total: int
    skip: int
    limit: int


class AuditLogFilter(BaseModel):
    event_type: Optional[str] = None
    user_id: Optional[str] = None
    from_date: Optional[str] = None
    to_date: Optional[str] = None
    skip: int = 0
    limit: int = 100
