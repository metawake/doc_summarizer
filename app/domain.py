from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Document:
    filename: str
    summary: str
    page_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    id: int | None = None
