def split_text(text: str, limit: int) -> list[str]:
    chunks = []
    start = 0
    end = limit

    while start < len(text):
        chunk = text[start:end]
        chunks.append(chunk)
        start = end
        end += limit

    return chunks
