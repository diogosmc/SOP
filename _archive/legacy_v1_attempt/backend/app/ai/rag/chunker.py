"""Text chunking for RAG indexing."""

from app.core.config import get_settings


def chunk_text(
    text: str,
    min_size: int | None = None,
    max_size: int | None = None,
    overlap: int | None = None,
) -> list[str]:
    """Split text into overlapping chunks using configured size bounds."""
    settings = get_settings()
    min_size = min_size if min_size is not None else settings.rag_chunk_min
    max_size = max_size if max_size is not None else settings.rag_chunk_max
    overlap = overlap if overlap is not None else settings.rag_chunk_overlap

    text = text.strip()
    if not text:
        return []
    if len(text) <= max_size:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + max_size, len(text))
        if end < len(text):
            break_at = text.rfind("\n", start + min_size, end)
            if break_at == -1:
                break_at = text.rfind(" ", start + min_size, end)
            if break_at > start:
                end = break_at

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)

    return chunks
