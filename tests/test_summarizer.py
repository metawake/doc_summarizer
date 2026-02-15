from unittest.mock import MagicMock, patch

from app.adapters.summarizer import OpenAISummarizer, chunk_text, count_tokens


def test_count_tokens_returns_positive_int() -> None:
    tokens = count_tokens("Hello, world!")
    assert isinstance(tokens, int)
    assert tokens > 0


def test_chunk_text_short_text_single_chunk() -> None:
    text = "Short text that fits in one chunk."
    chunks = chunk_text(text, max_tokens=1000)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunk_text_splits_on_paragraphs() -> None:
    paragraphs = ["Paragraph " + str(i) + ". " + "word " * 100 for i in range(20)]
    text = "\n\n".join(paragraphs)
    chunks = chunk_text(text, max_tokens=200)
    assert len(chunks) > 1
    # all original content should be preserved across chunks
    rejoined = "\n\n".join(chunks)
    for p in paragraphs:
        assert p in rejoined


def test_summarize_short_text_no_chunking() -> None:
    """Short text goes through single-pass summarization."""
    summarizer = OpenAISummarizer(api_key="test-key")

    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Test summary"))]

    with patch.object(summarizer.client.chat.completions, "create", return_value=mock_response):
        result = summarizer.summarize("A short document about testing.")

    assert result == "Test summary"
