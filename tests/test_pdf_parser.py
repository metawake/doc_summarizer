from pathlib import Path

import pymupdf
import pytest

from app.adapters.pdf_parser import PyMuPDFParser


@pytest.fixture
def parser() -> PyMuPDFParser:
    return PyMuPDFParser()


@pytest.fixture
def sample_pdf(tmp_path: Path) -> Path:
    """Create a minimal PDF with text for testing."""
    pdf_path = tmp_path / "sample.pdf"
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Hello, this is a test PDF document.")
    page.insert_text((72, 100), "It contains multiple lines of text for parsing.")
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


def test_parse_returns_text(parser: PyMuPDFParser, sample_pdf: Path) -> None:
    result = parser.parse(sample_pdf)
    assert isinstance(result, str)
    assert "test PDF document" in result


def test_parse_nonexistent_file_raises(parser: PyMuPDFParser, tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        parser.parse(tmp_path / "nope.pdf")


def test_get_page_count(parser: PyMuPDFParser, sample_pdf: Path) -> None:
    assert parser.get_page_count(sample_pdf) == 1
