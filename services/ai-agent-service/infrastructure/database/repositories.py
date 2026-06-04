import statistics
from typing import Any

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance

from domain.entities.document import Document
from domain.entities.query import Query
from domain.repositories import VectorRepository, QueryLogRepository


class QdrantVectorRepository(VectorRepository):
    def __init__(self, client: AsyncQdrantClient):
        self._client = client

    async def search(self, query_vector: list[float], top_k: int = 5, score_threshold: float = 0.7) -> list[dict[str, Any]]:
        try:
            search_result = await self._client.query_points(
                collection_name="documents",
                query=query_vector,
                limit=top_k,
                score_threshold=score_threshold,
            )
            return [
                {
                    "content": hit.payload.get("content", ""),
                    "metadata": {k: v for k, v in hit.payload.items() if k != "content"},
                    "score": hit.score,
                }
                for hit in search_result.points
            ]
        except Exception:
            return []

    async def upsert(self, documents: list[Document]) -> None:
        if not documents:
            return

        collections = await self._client.get_collections()
        collection_names = [c.name for c in collections.collections]

        if "documents" not in collection_names:
            vector_size = len(documents[0].embedding) if documents[0].embedding else 1536
            await self._client.recreate_collection(
                collection_name="documents",
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )

        points = []
        for doc in documents:
            points.append(PointStruct(
                id=abs(hash(doc.content)),
                vector=doc.embedding or [],
                payload={
                    "content": doc.content,
                    **doc.metadata,
                },
            ))

        await self._client.upsert(collection_name="documents", points=points)

    async def list_collections(self) -> list[str]:
        collections = await self._client.get_collections()
        return [c.name for c in collections.collections]


class QueryLogRepositoryImpl(QueryLogRepository):
    def __init__(self):
        self._queries: list[Query] = []

    async def save(self, query: Query) -> None:
        if query.id is None:
            query.id = str(len(self._queries) + 1)
        self._queries.append(query)

    async def get_all(self) -> list[Query]:
        return list(self._queries)

    async def get_metrics(self) -> dict[str, Any]:
        if not self._queries:
            return {
                "total_queries": 0,
                "avg_latency_ms": 0.0,
                "total_tokens_used": 0,
                "total_cost": 0.0,
                "p50_latency_ms": 0.0,
                "p95_latency_ms": 0.0,
                "p99_latency_ms": 0.0,
            }

        latencies = sorted([q.latency_ms for q in self._queries])
        total_tokens = sum(q.tokens_used for q in self._queries)
        total_cost = sum(q.cost for q in self._queries)

        return {
            "total_queries": len(self._queries),
            "avg_latency_ms": statistics.mean(latencies),
            "total_tokens_used": total_tokens,
            "total_cost": total_cost,
            "p50_latency_ms": self._percentile(latencies, 50),
            "p95_latency_ms": self._percentile(latencies, 95),
            "p99_latency_ms": self._percentile(latencies, 99),
        }

    def _percentile(self, data: list[float], percentile: float) -> float:
        if not data:
            return 0.0
        k = (len(data) - 1) * percentile / 100.0
        f = int(k)
        c = f + 1
        if c >= len(data):
            return data[-1]
        return data[f] + (k - f) * (data[c] - data[f])
