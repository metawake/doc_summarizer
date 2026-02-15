import pytest


def test_health_endpoint() -> None:
    """Health check should return 200 with status ok."""
    pytest.skip("api tests will be wired up after adapters are implemented")


def test_upload_rejects_non_pdf() -> None:
    """Upload endpoint should reject non-PDF files with 400."""
    pytest.skip("api tests will be wired up after adapters are implemented")


def test_history_returns_recent_documents() -> None:
    """History endpoint should return last N processed documents."""
    pytest.skip("api tests will be wired up after adapters are implemented")
