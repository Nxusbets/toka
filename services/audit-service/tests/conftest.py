import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from typing import Optional

from domain.entities.audit_log import AuditLog
from domain.repositories import AuditLogRepository


@pytest.fixture
def mock_audit_repo():
    repo = MagicMock(spec=AuditLogRepository)
    repo.create = AsyncMock()
    repo.find_by_id = AsyncMock()
    repo.find_all = AsyncMock(return_value=([], 0))
    repo.get_stats = AsyncMock(return_value={
        "total": 0, "by_event_type": {}, "by_day": [],
    })
    return repo


@pytest.fixture
def sample_audit_log():
    return AuditLog(
        id="507f1f77bcf86cd799439011",
        event_type="auth.login",
        user_id="user-123",
        user_email="test@example.com",
        resource="auth",
        action="login",
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0",
        metadata={"key": "value"},
        timestamp=datetime.utcnow(),
    )
