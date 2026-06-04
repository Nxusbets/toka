import pytest
from datetime import datetime
from pydantic import ValidationError

from application.dto.ai_dto import (
    QueryRequest,
    QueryResponse,
    IngestRequest,
    EvaluationMetrics,
    ReportRequest,
    ReportResponse,
)


class TestQueryRequest:
    def test_valid_request(self):
        dto = QueryRequest(query="What is Toka?", user_id="user-1", collection="custom")
        assert dto.query == "What is Toka?"
        assert dto.user_id == "user-1"
        assert dto.collection == "custom"

    def test_default_collection(self):
        dto = QueryRequest(query="test query")
        assert dto.collection == "documents"
        assert dto.user_id is None

    def test_missing_query(self):
        with pytest.raises(ValidationError):
            QueryRequest()

    def test_empty_query(self):
        with pytest.raises(ValidationError):
            QueryRequest(query="")


class TestQueryResponse:
    def test_valid_response(self):
        dto = QueryResponse(
            answer="Toka is a platform.",
            context_docs=[{"content": "doc", "score": 0.95}],
            latency_ms=150.0,
            tokens_used=50,
            cost=0.002,
            model="gpt-4o-mini",
        )
        assert dto.answer == "Toka is a platform."
        assert len(dto.context_docs) == 1
        assert dto.latency_ms == 150.0
        assert dto.model == "gpt-4o-mini"

    def test_default_values(self):
        dto = QueryResponse(answer="test")
        assert dto.context_docs == []
        assert dto.latency_ms == 0.0
        assert dto.tokens_used == 0
        assert dto.cost == 0.0
        assert dto.model == ""

    def test_missing_answer(self):
        with pytest.raises(ValidationError):
            QueryResponse()


class TestIngestRequest:
    def test_valid_request(self):
        dto = IngestRequest(
            documents=[{"content": "doc1", "metadata": {"source": "web"}}],
            collection="custom",
        )
        assert len(dto.documents) == 1
        assert dto.collection == "custom"

    def test_default_collection(self):
        dto = IngestRequest(documents=[{"content": "doc1"}])
        assert dto.collection == "documents"

    def test_multiple_documents(self):
        dto = IngestRequest(documents=[{"content": "a"}, {"content": "b"}])
        assert len(dto.documents) == 2

    def test_empty_documents(self):
        dto = IngestRequest(documents=[])
        assert dto.documents == []

    def test_missing_documents(self):
        with pytest.raises(ValidationError):
            IngestRequest()


class TestEvaluationMetrics:
    def test_valid_metrics(self):
        dto = EvaluationMetrics(
            total_queries=100,
            avg_latency_ms=150.5,
            total_tokens_used=5000,
            total_cost=0.05,
            p50_latency_ms=120.0,
            p95_latency_ms=300.0,
            p99_latency_ms=500.0,
        )
        assert dto.total_queries == 100
        assert dto.avg_latency_ms == 150.5
        assert dto.p50_latency_ms == 120.0

    def test_default_metrics(self):
        dto = EvaluationMetrics()
        assert dto.total_queries == 0
        assert dto.avg_latency_ms == 0.0
        assert dto.total_tokens_used == 0
        assert dto.total_cost == 0.0


class TestReportRequest:
    def test_valid_request(self):
        dto = ReportRequest(user_id="user-1", period="30d", report_type="full")
        assert dto.user_id == "user-1"
        assert dto.period == "30d"
        assert dto.report_type == "full"

    def test_default_values(self):
        dto = ReportRequest(user_id="user-1")
        assert dto.period == "7d"
        assert dto.report_type == "activity_summary"

    def test_missing_user_id(self):
        with pytest.raises(ValidationError):
            ReportRequest()


class TestReportResponse:
    def test_valid_response(self):
        dto = ReportResponse(report="This is a report.", user_id="user-1")
        assert dto.report == "This is a report."
        assert dto.user_id == "user-1"
        assert isinstance(dto.generated_at, datetime)

    def test_default_user_id(self):
        dto = ReportResponse(report="test report")
        assert dto.user_id == ""

    def test_missing_report(self):
        with pytest.raises(ValidationError):
            ReportResponse()
