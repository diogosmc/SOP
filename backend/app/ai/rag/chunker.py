"""Text chunking for RAG indexing."""


def chunk_text(text: str, chunk_size: int = 700, overlap: int = 100) -> list[str]:
    """Split text into overlapping chunks between 500 and 900 characters when possible."""
    min_size = 500
    max_size = 900
    target_size = max(min_size, min(chunk_size, max_size))

    normalized = text.strip()
    if not normalized:
        return []
    if len(normalized) <= max_size:
        return [normalized]

    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        end = min(start + target_size, len(normalized))
        if end < len(normalized):
            break_at = normalized.rfind("\n", start + min_size, end)
            if break_at == -1:
                break_at = normalized.rfind(" ", start + min_size, end)
            if break_at > start:
                end = break_at

        chunk = normalized[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(normalized):
            break
        start = max(end - overlap, start + 1)

    return chunks
