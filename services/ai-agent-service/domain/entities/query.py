from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Query:
    id: Optional[str] = None
    user_query: str = ""
    response: str = ""
    context_docs: list[dict] = field(default_factory=list)
    latency_ms: float = 0.0
    tokens_used: int = 0
    cost: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None
