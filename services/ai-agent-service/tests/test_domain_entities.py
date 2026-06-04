from datetime import datetime
from typing import Optional

from domain.entities.query import Query
from domain.entities.document import Document


class TestQueryEntity:
    def test_query_creation_with_defaults(self):
        query = Query()
        assert query.id is None
        assert query.user_query == ""
        assert query.response == ""
        assert query.context_docs == []
        assert query.latency_ms == 0.0
        assert query.tokens_used == 0
        assert query.cost == 0.0
        assert isinstance(query.timestamp, datetime)
        assert query.user_id is None

    def test_query_creation_with_values(self):
        now = datetime.utcnow()
        query = Query(
            id="q-123",
            user_query="What is Toka?",
            response="Toka is a platform.",
            context_docs=[{"content": "doc", "score": 0.95}],
            latency_ms=150.5,
            tokens_used=50,
            cost=0.002,
            timestamp=now,
            user_id="user-456",
        )
        assert query.id == "q-123"
        assert query.user_query == "What is Toka?"
        assert query.response == "Toka is a platform."
        assert len(query.context_docs) == 1
        assert query.latency_ms == 150.5
        assert query.tokens_used == 50
        assert query.cost == 0.002
        assert query.timestamp == now
        assert query.user_id == "user-456"

    def test_query_empty_context(self):
        query = Query(context_docs=[])
        assert query.context_docs == []

    def test_query_zero_metrics(self):
        query = Query(latency_ms=0.0, tokens_used=0, cost=0.0)
        assert query.latency_ms == 0.0
        assert query.tokens_used == 0
        assert query.cost == 0.0


class TestDocumentEntity:
    def test_document_creation_with_defaults(self):
        doc = Document()
        assert doc.id is None
        assert doc.content == ""
        assert doc.metadata == {}
        assert doc.embedding is None

    def test_document_creation_with_values(self):
        doc = Document(
            id="doc-123",
            content="Some document content.",
            metadata={"source": "docs"},
            embedding=[0.1, 0.2, 0.3],
        )
        assert doc.id == "doc-123"
        assert doc.content == "Some document content."
        assert doc.metadata == {"source": "docs"}
        assert doc.embedding == [0.1, 0.2, 0.3]

    def test_document_no_embedding(self):
        doc = Document(content="Text without embedding")
        assert doc.embedding is None

    def test_document_empty_metadata(self):
        doc = Document(content="test", metadata={})
        assert doc.metadata == {}
