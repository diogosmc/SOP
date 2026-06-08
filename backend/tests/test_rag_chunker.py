"""Tests for RAG text chunker."""

from app.ai.rag.chunker import chunk_text


def test_chunk_text_short() -> None:
    text = "Nota curta sobre Python."
    chunks = chunk_text(text)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunk_text_empty() -> None:
    assert chunk_text("") == []
    assert chunk_text("   ") == []


def test_chunk_text_long() -> None:
    text = ("Parágrafo sobre loops e estruturas de controle. " * 40).strip()
    chunks = chunk_text(text)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) <= 900
        assert chunk.strip()


def test_chunk_text_preserves_overlap() -> None:
    text = "".join(f"secao{i:03d}-" + ("conteudo " * 80) + "\n" for i in range(8))
    chunks = chunk_text(text, chunk_size=700, overlap=100)
    assert len(chunks) >= 2

    for index in range(len(chunks) - 1):
        current = chunks[index]
        nxt = chunks[index + 1]
        overlap_found = any(current[-size:] in nxt for size in range(100, 20, -1))
        assert overlap_found, f"Expected overlap between chunk {index} and {index + 1}"
