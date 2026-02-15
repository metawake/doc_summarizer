from pathlib import Path
from typing import Protocol

from app.domain import Document


class PDFParser(Protocol):
    """Extracts text content from a PDF file, preserving tables and image descriptions."""

    def parse(self, file_path: Path) -> str: ...

    def get_page_count(self, file_path: Path) -> int: ...


class Summarizer(Protocol):
    """Generates a concise summary from text content."""

    def summarize(self, text: str) -> str: ...


class DocumentRepository(Protocol):
    """Persists and retrieves processed document records."""

    def save(self, document: Document) -> Document: ...

    def get_recent(self, limit: int = 5) -> list[Document]: ...
