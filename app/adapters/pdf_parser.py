import logging
from pathlib import Path

import pymupdf4llm

logger = logging.getLogger(__name__)


class PyMuPDFParser:
    """Extracts text from PDFs as LLM-friendly markdown, preserving tables and images."""

    def parse(self, file_path: Path) -> str:
        if not file_path.exists():
            raise FileNotFoundError(f"PDF not found: {file_path}")

        md_text = pymupdf4llm.to_markdown(str(file_path))

        if not md_text.strip():
            raise ValueError("PDF appears to be empty or unreadable")

        return md_text

    def get_page_count(self, file_path: Path) -> int:
        import pymupdf

        doc = pymupdf.open(str(file_path))
        count = len(doc)
        doc.close()
        return count
