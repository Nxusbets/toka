from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class Document:
    id: Optional[str] = None
    content: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding: Optional[list[float]] = None
