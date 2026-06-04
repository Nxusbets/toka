from abc import ABC, abstractmethod
from typing import Any, Optional

from domain.entities.query import Query
from domain.entities.document import Document


class VectorRepository(ABC):
    @abstractmethod
    async def search(self, query_vector: list[float], top_k: int = 5, score_threshold: float = 0.7) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def upsert(self, documents: list[Document]) -> None:
        ...

    @abstractmethod
    async def list_collections(self) -> list[str]:
        ...


class QueryLogRepository(ABC):
    @abstractmethod
    async def save(self, query: Query) -> None:
        ...

    @abstractmethod
    async def get_all(self) -> list[Query]:
        ...

    @abstractmethod
    async def get_metrics(self) -> dict[str, Any]:
        ...
