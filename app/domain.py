from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class Document:
    filename: str
    summary: str
    page_count: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    id: int | None = None
