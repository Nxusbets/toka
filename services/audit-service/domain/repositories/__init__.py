from abc import ABC, abstractmethod
from typing import Optional

from domain.entities.audit_log import AuditLog


class AuditLogRepository(ABC):
    @abstractmethod
    async def create(self, log: AuditLog) -> AuditLog:
        ...

    @abstractmethod
    async def find_by_id(self, log_id: str) -> Optional[AuditLog]:
        ...

    @abstractmethod
    async def find_all(
        self,
        skip: int = 0,
        limit: int = 100,
        event_type: Optional[str] = None,
        user_id: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> tuple[list[AuditLog], int]:
        ...

    @abstractmethod
    async def get_stats(self) -> dict:
        ...
