from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1)
    user_id: Optional[str] = None
    collection: str = "documents"


class QueryResponse(BaseModel):
    answer: str
    context_docs: list[dict[str, Any]] = []
    latency_ms: float = 0.0
    tokens_used: int = 0
    cost: float = 0.0
    model: str = ""


class IngestRequest(BaseModel):
    documents: list[dict[str, Any]]
    collection: str = "documents"


class EvaluationMetrics(BaseModel):
    total_queries: int = 0
    avg_latency_ms: float = 0.0
    total_tokens_used: int = 0
    total_cost: float = 0.0
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0


class ReportRequest(BaseModel):
    user_id: str
    period: str = "7d"
    report_type: str = "activity_summary"


class ReportResponse(BaseModel):
    report: str
    generated_at: datetime = datetime.now()
    user_id: str = ""
