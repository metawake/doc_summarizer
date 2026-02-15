from pathlib import Path

import pytest


@pytest.fixture
def sample_pdf(tmp_path: Path) -> Path:
    """Will be replaced with a real test PDF fixture."""
    return tmp_path / "sample.pdf"


def test_parse_returns_text(sample_pdf: Path) -> None:
    """Parser should return non-empty markdown string from a valid PDF."""
    pytest.skip("adapter not yet implemented")


def test_parse_preserves_tables(sample_pdf: Path) -> None:
    """Parsed output should retain table structure (e.g. markdown pipe tables)."""
    pytest.skip("adapter not yet implemented")
