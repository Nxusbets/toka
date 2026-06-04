import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from domain.entities.query import Query
from domain.entities.document import Document
from application.use_cases.ai_use_cases import (
    QueryUseCase,
    IngestDocumentUseCase,
    EvaluateUseCase,
    ReportUseCase,
)

pytestmark = pytest.mark.asyncio

class TestQueryUseCase:
    async def test_query_success(self, mock_vector_repo, mock_query_log_repo, mock_llm_client, mock_embed_client):
        mock_embed_client.embeddings.create.return_value.data[0].embedding = [0.1] * 384
        mock_vector_repo.search.return_value = [
            {"content": "Toka is a platform", "score": 0.95},
        ]

        use_case = QueryUseCase(mock_vector_repo, mock_query_log_repo, mock_llm_client, mock_embed_client)
        result = await use_case.execute(
            user_query="What is Toka?",
            user_id="user-123",
            collection="documents",
        )

        assert result.user_query == "What is Toka?"
        assert result.response == "This is an AI response."
        assert len(result.context_docs) == 1
        assert result.tokens_used == 50
        assert result.user_id == "user-123"
        mock_query_log_repo.save.assert_called_once()

    async def test_query_no_context(self, mock_vector_repo, mock_query_log_repo, mock_llm_client, mock_embed_client):
        mock_embed_client.embeddings.create.return_value.data[0].embedding = [0.1] * 384
        mock_vector_repo.search.return_value = []

        use_case = QueryUseCase(mock_vector_repo, mock_query_log_repo, mock_llm_client, mock_embed_client)
        result = await use_case.execute(user_query="Unknown topic?")

        assert len(result.context_docs) == 0
        assert result.response == "This is an AI response."

    async def test_query_no_user_id(self, mock_vector_repo, mock_query_log_repo, mock_llm_client, mock_embed_client):
        mock_embed_client.embeddings.create.return_value.data[0].embedding = [0.1] * 384
        mock_vector_repo.search.return_value = []

        use_case = QueryUseCase(mock_vector_repo, mock_query_log_repo, mock_llm_client, mock_embed_client)
        result = await use_case.execute(user_query="Hello")

        assert result.user_id is None


class TestIngestDocumentUseCase:
    async def test_ingest_single_document(self, mock_vector_repo, mock_embed_client):
        mock_embed_client.embeddings.create.return_value.data[0].embedding = [0.1] * 384

        use_case = IngestDocumentUseCase(mock_vector_repo, mock_embed_client)
        documents = [{"content": "Toka is a user management platform.", "metadata": {"source": "docs"}}]
        count = await use_case.execute(documents, collection="documents")

        assert count == 1
        mock_vector_repo.upsert.assert_called_once()

    async def test_ingest_multiple_documents(self, mock_vector_repo, mock_embed_client):
        embed_response = MagicMock()
        embed_response.data = [MagicMock(embedding=[0.1] * 384), MagicMock(embedding=[0.2] * 384)]
        mock_embed_client.embeddings.create.return_value = embed_response

        use_case = IngestDocumentUseCase(mock_vector_repo, mock_embed_client)
        documents = [
            {"content": "Document one.", "metadata": {"source": "a"}},
            {"content": "Document two.", "metadata": {"source": "b"}},
        ]
        count = await use_case.execute(documents)

        assert count == 2
        mock_vector_repo.upsert.assert_called_once()

    async def test_ingest_empty_documents(self, mock_vector_repo, mock_embed_client):
        use_case = IngestDocumentUseCase(mock_vector_repo, mock_embed_client)
        count = await use_case.execute([])

        assert count == 0
        mock_vector_repo.upsert.assert_not_called()

    async def test_ingest_long_document_chunking(self, mock_vector_repo, mock_embed_client):
        embed_response = MagicMock()
        embed_response.data = [MagicMock(embedding=[i * 0.01] * 384) for i in range(20)]
        mock_embed_client.embeddings.create.return_value = embed_response

        use_case = IngestDocumentUseCase(mock_vector_repo, mock_embed_client)
        long_content = "word " * 1000
        documents = [{"content": long_content, "metadata": {"source": "long"}}]
        count = await use_case.execute(documents)

        assert count > 1
        mock_vector_repo.upsert.assert_called_once()

    def test_chunk_text_shorter_than_chunk_size(self):
        use_case = IngestDocumentUseCase.__new__(IngestDocumentUseCase)
        text = "Short text."
        chunks = use_case._chunk_text(text, chunk_size=500, overlap=100)
        assert chunks == [text]

    def test_chunk_text_longer(self):
        use_case = IngestDocumentUseCase.__new__(IngestDocumentUseCase)
        text = "word " * 200
        chunks = use_case._chunk_text(text, chunk_size=100, overlap=20)
        assert len(chunks) > 1
        assert all(len(c) <= 100 for c in chunks)


class TestEvaluateUseCase:
    async def test_evaluate_empty(self, mock_query_log_repo):
        mock_query_log_repo.get_metrics.return_value = {
            "total_queries": 0, "avg_latency_ms": 0.0,
            "total_tokens_used": 0, "total_cost": 0.0,
            "p50_latency_ms": 0.0, "p95_latency_ms": 0.0, "p99_latency_ms": 0.0,
        }

        use_case = EvaluateUseCase(mock_query_log_repo)
        result = await use_case.execute()

        assert result["total_queries"] == 0
        mock_query_log_repo.get_metrics.assert_called_once()

    async def test_evaluate_with_data(self, mock_query_log_repo):
        mock_query_log_repo.get_metrics.return_value = {
            "total_queries": 10, "avg_latency_ms": 150.0,
            "total_tokens_used": 500, "total_cost": 0.02,
            "p50_latency_ms": 120.0, "p95_latency_ms": 300.0, "p99_latency_ms": 500.0,
        }

        use_case = EvaluateUseCase(mock_query_log_repo)
        result = await use_case.execute()

        assert result["total_queries"] == 10
        assert result["avg_latency_ms"] == 150.0


class TestIngestDocumentUseCaseChunking:
    def test_chunk_text_boundary(self):
        use_case = IngestDocumentUseCase.__new__(IngestDocumentUseCase)
        text = "A" * 600
        chunks = use_case._chunk_text(text, chunk_size=500, overlap=100)
        assert len(chunks) >= 2
        assert all(len(c) <= 500 for c in chunks)
        assert "".join(chunks).startswith(text) and text in "".join(chunks)

    def test_chunk_text_exact_size(self):
        use_case = IngestDocumentUseCase.__new__(IngestDocumentUseCase)
        text = "A" * 500
        chunks = use_case._chunk_text(text, chunk_size=500, overlap=100)
        assert chunks == [text]

    def test_chunk_text_word_boundary(self):
        use_case = IngestDocumentUseCase.__new__(IngestDocumentUseCase)
        text = "hello world " * 100
        chunks = use_case._chunk_text(text, chunk_size=50, overlap=10)
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk) <= 50
