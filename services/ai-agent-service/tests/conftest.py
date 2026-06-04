import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from typing import Any

from domain.entities.query import Query
from domain.entities.document import Document
from domain.repositories import VectorRepository, QueryLogRepository


@pytest.fixture
def mock_vector_repo():
    repo = MagicMock(spec=VectorRepository)
    repo.search = AsyncMock(return_value=[])
    repo.upsert = AsyncMock()
    repo.list_collections = AsyncMock(return_value=["documents"])
    return repo


@pytest.fixture
def mock_query_log_repo():
    repo = MagicMock(spec=QueryLogRepository)
    repo.save = AsyncMock()
    repo.get_all = AsyncMock(return_value=[])
    repo.get_metrics = AsyncMock(return_value={
        "total_queries": 0,
        "avg_latency_ms": 0.0,
        "total_tokens_used": 0,
        "total_cost": 0.0,
        "p50_latency_ms": 0.0,
        "p95_latency_ms": 0.0,
        "p99_latency_ms": 0.0,
    })
    return repo


@pytest.fixture
def mock_llm_client():
    client = MagicMock()
    chat_completion = MagicMock()
    chat_completion.choices = [
        MagicMock(message=MagicMock(content="This is an AI response."))
    ]
    chat_completion.usage = MagicMock(total_tokens=50)
    client.chat = MagicMock()
    client.chat.completions = MagicMock()
    client.chat.completions.create = AsyncMock(return_value=chat_completion)
    return client


@pytest.fixture
def mock_embed_client():
    client = MagicMock()
    embedding_data = MagicMock()
    embedding_data.data = [MagicMock(embedding=[0.1] * 384)]
    embedding_data2 = MagicMock()
    embedding_data2.data = [MagicMock(embedding=[0.2] * 384), MagicMock(embedding=[0.3] * 384)]
    client.embeddings = MagicMock()
    client.embeddings.create = AsyncMock(return_value=embedding_data)
    return client


@pytest.fixture
def sample_query():
    return Query(
        id="1",
        user_query="What is Toka?",
        response="Toka is a platform.",
        context_docs=[{"content": "Toka docs", "score": 0.95}],
        latency_ms=150.0,
        tokens_used=50,
        cost=0.002,
        timestamp=datetime.utcnow(),
        user_id="user-123",
    )


@pytest.fixture
def sample_document():
    return Document(
        id=None,
        content="Toka is a user management platform.",
        metadata={"source": "docs", "collection": "documents"},
        embedding=[0.1] * 384,
    )
