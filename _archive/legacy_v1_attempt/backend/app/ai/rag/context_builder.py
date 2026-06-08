"""Build LLM context strings from retrieved chunks."""


def build_context(chunks: list[dict]) -> str:
    """Format search results into a single context block for the AI."""
    if not chunks:
        return ""

    parts: list[str] = []
    for index, chunk in enumerate(chunks, start=1):
        content = chunk.get("content", "").strip()
        if not content:
            continue
        title = chunk.get("title")
        if title:
            parts.append(f"[{index}] {title}\n{content}")
        else:
            parts.append(f"[{index}] {content}")

    return "\n\n".join(parts)
