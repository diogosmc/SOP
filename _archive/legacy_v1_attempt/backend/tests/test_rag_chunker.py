"""RAG chunker tests."""

from app.ai.rag.chunker import chunk_text


def test_chunk_text_splits_long_content() -> None:
    text = "A" * 2000
    chunks = chunk_text(text, min_size=500, max_size=900, overlap=100)
    assert len(chunks) >= 2
    assert all(len(c) <= 900 for c in chunks)


def test_chunk_text_short_content() -> None:
    text = "Short note."
    chunks = chunk_text(text, min_size=500, max_size=900, overlap=100)
    assert chunks == [text]
