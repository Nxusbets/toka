import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from api.main import app
from domain.repositories import VectorRepository, QueryLogRepository
from domain.entities.query import Query
from application.use_cases.ai_use_cases import (
    QueryUseCase, IngestDocumentUseCase, ReportUseCase, EvaluateUseCase,
)
from infrastructure.message_queue import RabbitMQPublisher


pytestmark = pytest.mark.asyncio


def make_mock_query_use_case():
    use_case = MagicMock(spec=QueryUseCase)
    use_case.execute = AsyncMock(return_value=Query(
        id="1",
        user_query="What is Toka?",
        response="Toka is a platform.",
        context_docs=[{"content": "Toka docs", "score": 0.95}],
        latency_ms=150.0,
        tokens_used=50,
        cost=0.002,
        timestamp=datetime.utcnow(),
        user_id="user-123",
    ))
    return use_case


def make_mock_ingest_use_case():
    use_case = MagicMock(spec=IngestDocumentUseCase)
    use_case.execute = AsyncMock(return_value=3)
    return use_case


def make_mock_report_use_case():
    use_case = MagicMock(spec=ReportUseCase)
    use_case.execute = AsyncMock(return_value="This is a generated report.")
    return use_case


def make_mock_evaluate_use_case():
    use_case = MagicMock(spec=EvaluateUseCase)
    use_case.execute = AsyncMock(return_value={
        "total_queries": 10,
        "avg_latency_ms": 150.0,
        "total_tokens_used": 500,
        "total_cost": 0.02,
        "p50_latency_ms": 120.0,
        "p95_latency_ms": 300.0,
        "p99_latency_ms": 500.0,
    })
    return use_case


@pytest.fixture
def client():
    mock_vector_repo = MagicMock(spec=VectorRepository)
    mock_vector_repo.list_collections = AsyncMock(return_value=["documents", "reports"])

    mock_mq = MagicMock(spec=RabbitMQPublisher)
    mock_mq.publish = AsyncMock()

    app.state.vector_repo = mock_vector_repo
    app.state.mq_publisher = mock_mq
    app.state.query_use_case = make_mock_query_use_case()
    app.state.ingest_use_case = make_mock_ingest_use_case()
    app.state.report_use_case = make_mock_report_use_case()
    app.state.evaluate_use_case = make_mock_evaluate_use_case()

    return TestClient(app)


class TestAIRoutes:
    def test_query_success(self, client):
        response = client.post(
            "/api/v1/ai/query",
            json={"query": "What is Toka?", "user_id": "user-123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == "Toka is a platform."
        assert data["model"] == "gpt-4o-mini"
        assert data["latency_ms"] == 150.0

    def test_query_missing_body(self, client):
        response = client.post("/api/v1/ai/query", json={})
        assert response.status_code == 422

    def test_query_default_collection(self, client):
        response = client.post(
            "/api/v1/ai/query",
            json={"query": "Hello"},
        )
        assert response.status_code == 200
        assert response.json()["answer"] is not None

    def test_report_success(self, client):
        response = client.post(
            "/api/v1/ai/report",
            json={"user_id": "user-123", "period": "7d", "report_type": "activity_summary"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "report" in data
        assert data["user_id"] == "user-123"

    def test_report_missing_user_id(self, client):
        response = client.post("/api/v1/ai/report", json={})
        assert response.status_code == 422

    def test_report_defaults(self, client):
        response = client.post(
            "/api/v1/ai/report",
            json={"user_id": "user-123"},
        )
        assert response.status_code == 200

    def test_ingest_success(self, client):
        response = client.post(
            "/api/v1/ai/ingest",
            json={
                "documents": [
                    {"content": "Doc 1", "metadata": {"source": "web"}},
                    {"content": "Doc 2", "metadata": {"source": "api"}},
                    {"content": "Doc 3", "metadata": {"source": "manual"}},
                ],
                "collection": "custom",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["documents_ingested"] == 3

    def test_ingest_empty_documents(self, client):
        response = client.post(
            "/api/v1/ai/ingest",
            json={"documents": []},
        )
        assert response.status_code == 200

    def test_ingest_missing_body(self, client):
        response = client.post("/api/v1/ai/ingest", json={})
        assert response.status_code == 422

    def test_evaluate_success(self, client):
        response = client.get("/api/v1/ai/evaluate")
        assert response.status_code == 200
        data = response.json()
        assert data["total_queries"] == 10
        assert data["avg_latency_ms"] == 150.0

    def test_collections(self, client):
        response = client.get("/api/v1/ai/collections")
        assert response.status_code == 200
        data = response.json()
        assert "documents" in data

    def test_health_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "ai-agent-service"

    def test_query_validation_error(self, client):
        response = client.post("/api/v1/ai/query", json={"query": ""})
        assert response.status_code == 422
