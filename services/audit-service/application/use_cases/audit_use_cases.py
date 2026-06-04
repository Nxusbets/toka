from datetime import datetime
from typing import Any, Optional

import structlog

from domain.entities.audit_log import AuditLog
from domain.repositories import AuditLogRepository

logger = structlog.get_logger(__name__)


class LogEventUseCase:
    def __init__(self, repo: AuditLogRepository):
        self._repo = repo

    async def execute(self, event_data: dict[str, Any]) -> AuditLog:
        log = AuditLog(
            event_type=event_data.get("event_type", "unknown"),
            user_id=event_data.get("user_id"),
            user_email=event_data.get("user_email") or event_data.get("email"),
            resource=event_data.get("resource", ""),
            action=event_data.get("action", ""),
            ip_address=event_data.get("ip_address"),
            user_agent=event_data.get("user_agent"),
            metadata=event_data.get("metadata", {}),
            timestamp=datetime.fromisoformat(event_data["timestamp"]) if "timestamp" in event_data else datetime.utcnow(),
        )
        created = await self._repo.create(log)
        await logger.ainfo("audit_log_created", log_id=created.id, event_type=log.event_type)
        return created


class ListAuditLogsUseCase:
    def __init__(self, repo: AuditLogRepository):
        self._repo = repo

    async def execute(
        self,
        skip: int = 0,
        limit: int = 100,
        event_type: Optional[str] = None,
        user_id: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> tuple[list[AuditLog], int]:
        return await self._repo.find_all(
            skip=skip,
            limit=limit,
            event_type=event_type,
            user_id=user_id,
            from_date=from_date,
            to_date=to_date,
        )


class GetAuditLogUseCase:
    def __init__(self, repo: AuditLogRepository):
        self._repo = repo

    async def execute(self, log_id: str) -> Optional[AuditLog]:
        return await self._repo.find_by_id(log_id)
