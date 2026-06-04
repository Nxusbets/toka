import time
from typing import Any, Optional

import httpx
import structlog

from domain.entities.query import Query
from domain.entities.document import Document
from domain.repositories import VectorRepository, QueryLogRepository

logger = structlog.get_logger(__name__)

SYSTEM_PROMPT = """You are Toka AI Assistant, a specialized AI assistant for user management and analytics.
You help users understand their data, generate reports, and answer questions about user activity.

When answering questions:
1. Use the provided context (documents + live system data) to ground your answers
2. If you have live system data, use it to give accurate, specific answers
3. If neither context nor live data contains relevant information, say so
4. Be concise and accurate
5. For reports, follow chain-of-thought reasoning

Examples:
Q: How many active users do we have?
A: Based on the live system data, there are X active users out of Y total.

Q: Show me the audit logs
A: Here are the recent audit logs:
- user.registered | user@email.com | auth | ...

Q: Generate a weekly activity report for user John.
A: Let me analyze John's activity step by step.
First, I'll look at login frequency...
Then, I'll examine resource usage...
Finally, I'll summarize key metrics...
"""


class QueryUseCase:
    def __init__(self, vector_repo: VectorRepository, query_log_repo: QueryLogRepository,
                 llm_client: Any, embed_client: Any, http_client: Optional[httpx.AsyncClient] = None,
                 user_service_url: str = "", audit_service_url: str = ""):
        self._vector_repo = vector_repo
        self._query_log_repo = query_log_repo
        self._llm = llm_client
        self._embed = embed_client
        self._http = http_client
        self._user_service_url = user_service_url
        self._audit_service_url = audit_service_url

    async def _fetch_live_context(self, user_query: str) -> str:
        if not self._http:
            return ""
        query_lower = user_query.lower()
        parts: list[str] = []
        headers = {"X-Internal-Api-Key": "toka-internal-key-2024"}

        if any(w in query_lower for w in ["usuario", "user", "usuarios", "users", "cuenta", "account", "rol", "role", "permiso", "permission"]):
            try:
                resp = await self._http.get(f"{self._user_service_url}/api/v1/users?page=1&size=20", headers=headers, timeout=10.0)
                if resp.status_code == 200:
                    data = resp.json()
                    users = data if isinstance(data, list) else data.get("items", data.get("results", []))
                    if users:
                        parts.append(f"Users in the system ({len(users)} shown, {data.get('total', '?')} total):")
                        for u in users:
                            parts.append(f"  - {u.get('email', '?')} | username: {u.get('username', '?')} | active: {u.get('is_active', '?')} | created: {u.get('created_at', '?')}")
            except Exception as e:
                await logger.awarning("live_context_users_failed", error=str(e))

            try:
                resp = await self._http.get(f"{self._user_service_url}/api/v1/roles", headers=headers, timeout=10.0)
                if resp.status_code == 200:
                    data = resp.json()
                    roles = data if isinstance(data, list) else data.get("items", [])
                    if roles:
                        parts.append(f"Roles in the system ({len(roles)} total):")
                        for r in roles:
                            perms = [p.get("name", "") for p in r.get("permissions", []) if isinstance(p, dict)]
                            parts.append(f"  - {r.get('name', '?')}: {r.get('description', '')} | permissions: {', '.join(perms)}")
            except Exception as e:
                await logger.awarning("live_context_roles_failed", error=str(e))

        if any(w in query_lower for w in ["auditoría", "audit", "log", "actividad", "activity", "evento", "event"]):
            try:
                resp = await self._http.get(f"{self._audit_service_url}/api/v1/audit/logs?page=1&size=20", headers=headers, timeout=10.0)
                if resp.status_code == 200:
                    data = resp.json()
                    logs = data if isinstance(data, list) else data.get("items", data.get("results", []))
                    if logs:
                        parts.append(f"Recent audit logs ({len(logs)} shown, {data.get('total', '?')} total):")
                        for log in logs[:10]:
                            email = log.get("user_email") or log.get("email") or log.get("metadata", {}).get("user_email", "?")
                            parts.append(f"  - {log.get('event_type', '?')} | user: {email} | resource: {log.get('resource', '?')} | action: {log.get('action', '?')} | time: {log.get('timestamp', '?')}")
            except Exception as e:
                await logger.awarning("live_context_audit_failed", error=str(e))

        if any(w in query_lower for w in ["estadística", "stats", "statistics", "métrica", "metrics", "count", "total"]):
            try:
                resp = await self._http.get(f"{self._audit_service_url}/api/v1/audit/stats", headers=headers, timeout=10.0)
                if resp.status_code == 200:
                    stats = resp.json()
                    parts.append(f"System statistics: {stats}")
            except Exception as e:
                await logger.awarning("live_context_stats_failed", error=str(e))

        return "\n\n".join(parts)

    async def execute(self, user_query: str, user_id: Optional[str] = None, collection: str = "documents") -> Query:
        start_time = time.monotonic()

        embed_response = await self._embed.embeddings.create(
            input=user_query,
            model="text-embedding-3-small",
        )
        query_vector = embed_response.data[0].embedding

        context_docs = await self._vector_repo.search(query_vector, top_k=5, score_threshold=0.7)

        context_text = "\n\n".join([
            f"Document {i+1}: {doc.get('content', '')}"
            for i, doc in enumerate(context_docs)
        ])

        live_context = await self._fetch_live_context(user_query)

        full_context = context_text
        if live_context:
            full_context = full_context + "\n\n## Live System Data\n\n" + live_context if context_docs else live_context

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Relevant Context:\n{full_context}\n\nUser Query: {user_query}"},
        ]

        response = await self._llm.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.3,
            max_tokens=1024,
        )

        latency_ms = (time.monotonic() - start_time) * 1000

        query = Query(
            user_query=user_query,
            response=response.choices[0].message.content or "",
            context_docs=context_docs,
            latency_ms=latency_ms,
            tokens_used=response.usage.total_tokens if response.usage else 0,
            cost=0.0,
            user_id=user_id,
        )

        await self._query_log_repo.save(query)
        await logger.ainfo("query_completed", latency_ms=latency_ms, tokens=query.tokens_used)

        return query


class IngestDocumentUseCase:
    def __init__(self, vector_repo: VectorRepository, embed_client: Any):
        self._vector_repo = vector_repo
        self._embed = embed_client

    async def execute(self, documents: list[dict[str, Any]], collection: str = "documents") -> int:
        chunked_docs: list[Document] = []
        for doc in documents:
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})
            chunks = self._chunk_text(content, chunk_size=500, overlap=100)
            for i, chunk in enumerate(chunks):
                chunked_docs.append(Document(
                    content=chunk,
                    metadata={**metadata, "chunk_index": i, "collection": collection},
                ))

        for i in range(0, len(chunked_docs), 20):
            batch = chunked_docs[i:i + 20]
            texts = [d.content for d in batch]
            embed_response = await self._embed.embeddings.create(
                input=texts,
                model="text-embedding-3-small",
            )
            for j, doc in enumerate(batch):
                doc.embedding = embed_response.data[j].embedding
            await self._vector_repo.upsert(batch)

        await logger.ainfo("documents_ingested", count=len(chunked_docs), collection=collection)
        return len(chunked_docs)

    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
        if len(text) <= chunk_size:
            return [text]
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            if end < len(text):
                last_space = text.rfind(" ", start, end)
                if last_space > start:
                    end = last_space
            chunks.append(text[start:end])
            if end == len(text):
                break
            start = end - overlap
            if start < 0:
                start = 0
        return chunks


class ReportUseCase:
    def __init__(self, llm_client: Any, http_client: httpx.AsyncClient, user_service_url: str):
        self._llm = llm_client
        self._http = http_client
        self._user_service_url = user_service_url

    async def execute(self, user_id: str, period: str = "7d", report_type: str = "activity_summary") -> str:
        user_response = await self._http.get(f"{self._user_service_url}/api/v1/users/{user_id}")
        user_data = user_response.json() if user_response.status_code == 200 else {"error": "User not found"}

        prompt = f"""Generate a {report_type} report for user {user_id} over the period {period}.

Step 1: Analyze the user data
Step 2: Identify key activity patterns
Step 3: Calculate relevant metrics
Step 4: Summarize findings

User Data: {user_data}

Provide a comprehensive yet concise report."""

        response = await self._llm.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=2048,
        )

        report = response.choices[0].message.content or ""
        await logger.ainfo("report_generated", user_id=user_id, period=period)
        return report


class EvaluateUseCase:
    def __init__(self, query_log_repo: QueryLogRepository):
        self._query_log_repo = query_log_repo

    async def execute(self) -> dict[str, Any]:
        return await self._query_log_repo.get_metrics()
